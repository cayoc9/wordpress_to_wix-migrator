"""
HTML → Ricos converter utilities
"""

import logging
import re
import uuid
from typing import Any, Callable, Dict, List, Optional

from bs4 import BeautifulSoup, NavigableString

# Importando os handlers da nova arquitetura
from .handlers.blockquote_handler import handle_blockquote
from .handlers.code_block_handler import handle_code_block
from .handlers.heading_handler import handle_heading
from .handlers.iframe_handler import handle_iframe
from .handlers.image_handler import handle_image
from .handlers.list_handler import handle_list
from .handlers.paragraph_handler import handle_paragraph
from .handlers.misc_handlers import handle_line_break, handle_figure # Supondo um handler para <br> e <figure>

__all__ = [
    "convert_html_to_ricos",
    "generate_ricos_id",
]

logger = logging.getLogger(__name__)

# O Dispatcher da nova arquitetura
TAG_HANDLERS = {
    "h1": handle_heading,
    "h2": handle_heading,
    "h3": handle_heading,
    "h4": handle_heading,
    "h5": handle_heading,
    "h6": handle_heading,
    "p": handle_paragraph,
    "ul": handle_list,
    "ol": handle_list,
    "li": handle_list, # LI é tratado dentro do handle_list
    "blockquote": handle_blockquote,
    "pre": handle_code_block,
    "img": handle_image,
    "iframe": handle_iframe,
    "figure": handle_figure,
    "figcaption": handle_figure, # Figcaption é melhor tratado dentro do handle_figure
    "br": handle_line_break,
}

def generate_ricos_id() -> str:
    """Gera um ID curto para nodos Ricos."""
    return uuid.uuid4().hex[:12]

# Todas as funções auxiliares da versão antiga são mantidas, pois são necessárias para os handlers
def _get_text_alignment(element: Any) -> Optional[str]:
    # ... (código da função _get_text_alignment da versão antiga)
    style = element.get("style")
    if style:
        match = re.search(r"text-align:\s*(center|justify|left|right)\b;?", style, flags=re.IGNORECASE)
        if match:
            align = match.group(1).upper()
            if align in ["CENTER", "JUSTIFY", "LEFT", "RIGHT"]:
                return align
    align_attr = element.get("align")
    if align_attr:
        align_attr = align_attr.strip().upper()
        if align_attr in ["CENTER", "JUSTIFY", "LEFT", "RIGHT"]:
            return align_attr
    return None


def _get_inline_styles(element: Any) -> Dict[str, str]:
    # ... (código da função _get_inline_styles da versão antiga)
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


def _get_text_nodes_with_decorations(element: Any) -> List[Dict[str, Any]]:
    # ... (código completo da função _get_text_nodes_with_decorations da versão antiga)
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
            for tn in _get_text_nodes_with_decorations(child):
                tn.get("textData", {}).setdefault("decorations", []).append({"type": "BOLD"})
                text_nodes.append(tn)
        elif child.name in ["em", "i"]:
            for tn in _get_text_nodes_with_decorations(child):
                tn.get("textData", {}).setdefault("decorations", []).append({"type": "ITALIC"})
                text_nodes.append(tn)
        elif child.name == "u":
            for tn in _get_text_nodes_with_decorations(child):
                tn.get("textData", {}).setdefault("decorations", []).append({"type": "UNDERLINE"})
                text_nodes.append(tn)
        elif child.name == "a":
            href = child.get("href")
            if href:
                for tn in _get_text_nodes_with_decorations(child):
                    tn.get("textData", {}).setdefault("decorations", []).append({"type": "LINK", "linkData": {"url": href}})
                    text_nodes.append(tn)
            else:
                text_nodes.extend(_get_text_nodes_with_decorations(child))
        elif child.name == "span":
            text_nodes.extend(_get_text_nodes_with_decorations(child))
        elif child.name == "br":
            pass
        else:
            txt = child.get_text(strip=True) if hasattr(child, "get_text") else ""
            if txt:
                text_nodes.append({"type": "TEXT", "textData": {"text": txt, "decorations": []}})
    return text_nodes

def _convert_html_element_to_ricos_nodes(element: Any, **kwargs) -> List[Dict[str, Any]]:
    """
    Converte um elemento BeautifulSoup (nível de bloco) em uma lista de nós Ricos.
    Usa o dispatcher TAG_HANDLERS para delegar o trabalho.
    """
    ricos_nodes: List[Dict[str, Any]] = []
    tag = getattr(element, "name", None)

    handler = TAG_HANDLERS.get(tag)

    if handler:
        # Passa as kwargs (image_importer, etc.) para o handler apropriado
        ricos_nodes.extend(handler(element, **kwargs))
    # Fallback para tags não mapeadas (ex: tabelas)
    elif tag:
        logger.info("Unhandled HTML tag '%s' — converting to HTML node.", tag)
        ricos_nodes.append({
            "type": "HTML",
            "id": generate_ricos_id(),
            "htmlData": {
                "html": str(element),
                "source": "HTML",
                "containerData": {"width": {"custom": "940px"}}
            }
        })
    return ricos_nodes


def convert_html_to_ricos(html: str, **kwargs) -> Dict[str, Any]:
    """
    Converte uma string HTML em uma estrutura de nós Ricos.
    Esta é a função principal que orquestra a conversão.
    """
    logger.debug("convert_html_to_ricos called: html length=%s", len(html) if html else 0)

    if not html or not html.strip():
        logger.debug("Empty HTML input — returning empty nodes")
        return {"nodes": []}

    # Pré-processamento de shortcodes (lógica mantida da versão antiga)
    def caption_shortcode_to_figure(match):
        img_tag = match.group(2)
        caption_text = match.group(3).strip()
        if caption_text:
            return f'<figure class="wp-caption">{img_tag}<figcaption class="wp-caption-text">{caption_text}</figcaption></figure>'
        else:
            return img_tag

    caption_pattern = re.compile(r'\[caption(.*?)\]\s*(<img .*?>)\s*(.*?)\s*\[/caption\]', re.DOTALL)
    html = caption_pattern.sub(caption_shortcode_to_figure, html)

    soup = BeautifulSoup(html, "html.parser")
    ricos_output_nodes: List[Dict[str, Any]] = []

    # Lógica de buffer para agrupar texto e tags inline (mantida da versão antiga)
    BLOCK_TAGS = {
        "p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "blockquote",
        "img", "br", "table", "div", "hr", "pre", "figure", "figcaption", "iframe"
    }

    inline_buffer: List[Any] = []

    def flush_inline_buffer():
        nonlocal inline_buffer
        if not inline_buffer:
            return

        temp_p = soup.new_tag("p")
        for item in inline_buffer:
            try:
                temp_p.append(item.extract())
            except Exception:
                temp_p.append(item)
        
        # O buffer inline é sempre tratado como um parágrafo
        ricos_output_nodes.extend(handle_paragraph(temp_p, **kwargs))
        inline_buffer = []

    children = list(soup.body.children) if soup.body else list(soup.children)

    for child in children:
        is_inline = isinstance(child, NavigableString) or (getattr(child, "name", None) not in BLOCK_TAGS)

        if is_inline:
            inline_buffer.append(child)
        else:
            flush_inline_buffer()
            if getattr(child, "name", None):
                # Chamada centralizada que usa o dispatcher
                ricos_output_nodes.extend(_convert_html_element_to_ricos_nodes(child, **kwargs))
            elif isinstance(child, NavigableString) and child.strip():
                tmp = soup.new_tag("p")
                tmp.append(child.extract())
                ricos_output_nodes.extend(handle_paragraph(tmp, **kwargs))

    flush_inline_buffer()

    logger.debug("Generated Ricos nodes count: %d", len(ricos_output_nodes))
    return {"nodes": ricos_output_nodes}