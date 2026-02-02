from __future__ import annotations
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, parse_qs

from bs4 import BeautifulSoup
from bs4.element import NavigableString

def generate_ricos_id() -> str:
    """Gera um ID curto para nodos Ricos."""
    import uuid
    return uuid.uuid4().hex[:6]

def _get_inline_styles(element: Any) -> Dict[str, str]:
    style_attr = element.get("style")
    styles: Dict[str, str] = {}
    if style_attr:
        for style_pair in style_attr.split(";"):
            if ":" in style_pair:
                prop, value = style_pair.split(":", 1)
                prop = prop.strip().lower()
                value = value.strip()
                if prop:
                    styles[prop] = value
    return styles

def get_text_nodes_with_decorations(element: Any) -> List[Dict[str, Any]]:
    """
    Recursivamente extrai nós de texto de um elemento BeautifulSoup e suas decorações.
    """
    text_nodes: List[Dict[str, Any]] = []
    inline_styles = _get_inline_styles(element)

    for child in element.contents:
        if isinstance(child, NavigableString):
            raw = str(child)
            if raw.strip():
                node = {"type": "TEXT", "textData": {"text": raw, "decorations": []}}
                if "text-decoration" in inline_styles and "underline" in inline_styles["text-decoration"]:
                    node["textData"]["decorations"].append({"type": "UNDERLINE"})
                if "color" in inline_styles:
                    node["textData"]["decorations"].append({"type": "COLOR", "colorData": {"foreground": inline_styles["color"]}})
                if "background-color" in inline_styles:
                    node["textData"]["decorations"].append({"type": "COLOR", "colorData": {"background": inline_styles["background-color"]}})
                if "font-size" in inline_styles:
                    fs = inline_styles["font-size"]
                    px_match = re.match(r"([\d.]+)px$", fs)
                    if px_match:
                        try:
                            node["textData"]["decorations"].append({"type": "FONT_SIZE", "fontSizeData": {"value": float(px_match.group(1)), "unit": "PX"}})
                        except ValueError:
                            pass
                text_nodes.append(node)
        elif child.name in ["strong", "b"]:
            for tn in get_text_nodes_with_decorations(child):
                tn.get("textData", {}).setdefault("decorations", []).append({"type": "BOLD"})
                text_nodes.append(tn)
        elif child.name in ["em", "i"]:
            for tn in get_text_nodes_with_decorations(child):
                tn.get("textData", {}).setdefault("decorations", []).append({"type": "ITALIC"})
                text_nodes.append(tn)
        elif child.name == "u":
            for tn in get_text_nodes_with_decorations(child):
                tn.get("textData", {}).setdefault("decorations", []).append({"type": "UNDERLINE"})
                text_nodes.append(tn)
        elif child.name == "a":
            href = child.get("href")
            if href:
                for tn in get_text_nodes_with_decorations(child):
                    tn.get("textData", {}).setdefault("decorations", []).append({"type": "LINK", "linkData": {"url": href}})
                    text_nodes.append(tn)
            else:
                text_nodes.extend(get_text_nodes_with_decorations(child))
        elif child.name == "span":
            text_nodes.extend(get_text_nodes_with_decorations(child))
        elif child.name == "br":
            pass
        else:
            txt = child.get_text(strip=True) if hasattr(child, "get_text") else ""
            if txt:
                text_nodes.append({"type": "TEXT", "textData": {"text": txt, "decorations": []}})
    return text_nodes

def extract_video_info(url: str) -> Optional[Dict[str, str]]:
    if not url:
        return None
    
    
    # Tenta extrair o ID do vídeo de várias URLs do YouTube
    youtube_patterns = [
        r"(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]+)",
        r"(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]+)",
        r"(?:https?:\/\/)?youtu\.be\/([a-zA-Z0-9_-]+)"
    ]
    for pattern in youtube_patterns:
        match = re.search(pattern, url)
        if match:
            return {"platform": "youtube", "id": match.group(1)}
            
    # Tenta extrair o ID do vídeo de várias URLs do Vimeo
    vimeo_patterns = [
        r"(?:https?:\/\/)?(?:www\.)?vimeo\.com\/(\d+)",
        r"(?:https?:\/\/)?vimeo\.com\/embed\/(\d+)"
    ]
    for pattern in vimeo_patterns:
        match = re.search(pattern, url)
        if match:
            return {"platform": "vimeo", "id": match.group(1)}
            
    return None


def iframe_html_for_video(video_id: str, platform: str) -> str:
    """Gera o HTML do iframe para um vídeo."""
    if platform == "youtube":
        return f'<iframe src="https://www.youtube.com/embed/{video_id}" allowfullscreen></iframe>'
    elif platform == "vimeo":
        return f'<iframe src="https://player.vimeo.com/video/{video_id}" allowfullscreen></iframe>'
    return ""


def link_block_for_video(video_id: str, platform: str) -> Dict[str, Any]:
    """Gera um bloco de link para um vídeo."""
    if platform == "youtube":
        url = f"https://www.youtube.com/watch?v={video_id}"
        text = "Assistir no YouTube"
    elif platform == "vimeo":
        url = f"https://vimeo.com/{video_id}"
        text = "Assistir no Vimeo"
    else:
        return {}

    return {
        "type": "paragraph",
        "nodes": [
            {"type": "text", "text": "▶ ", "marks": []},
            {
                "type": "link",
                "data": {"url": url},
                "nodes": [{"type": "text", "text": text, "marks": []}],
            },
        ],
    }
