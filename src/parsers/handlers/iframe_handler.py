from __future__ import annotations
from typing import Any, Dict, List, Optional
from bs4.element import Tag
from .utils import extract_video_info, iframe_html_for_video, link_block_for_video

def handle_iframe(element: Tag, embed_strategy: str = "HTML") -> List[Dict[str, Any]]:
    """Converte <iframe> em nó HTML ou em parágrafo com link.

    - Para YouTube/Vimeo: por padrão gera HTML (iframe); como fallback, gera LINK.
    - Para outros iframes: gera um parágrafo com link para a URL.
    """
    nodes: List[Dict[str, Any]] = []
    src = element.get("src")
    if isinstance(src, list):
        src = src[0] if src else ""
    video_info = extract_video_info(src or "")

    if video_info:
        platform = video_info["platform"]
        video_id = video_info["id"]
        if embed_strategy == "HTML":
            nodes.append({
                "type": "HTML",
                "htmlData": {"html": iframe_html_for_video(video_id, platform), "source": "HTML",
                              "containerData": {"width": {"size": "CONTENT"}}}
            })
        else:  # LINK (fallback)
            nodes.append(link_block_for_video(video_id, platform))
    else:
        if src:
            nodes.append({
                "type": "PARAGRAPH",
                "nodes": [
                    {"type": "TEXT", "textData": {"text": src, "decorations": [
                        {"type": "LINK", "linkData": {"url": src}}
                    ]}}
                ],
                "paragraphData": {}
            })
    return nodes
