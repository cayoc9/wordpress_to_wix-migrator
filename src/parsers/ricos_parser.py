"""
HTML → Ricos converter utilities
"""

import logging
import re
import uuid
from typing import Any, Callable, Dict, List, Optional

from bs4 import BeautifulSoup
from bs4.element import NavigableString

# Importando os handlers da nova arquitetura
from .handlers.blockquote_handler import handle_blockquote
from .shortcode_parser import parse_shortcodes
from .handlers.code_block_handler import handle_code_block
from .handlers.heading_handler import handle_heading
from .handlers.iframe_handler import handle_iframe
from .handlers.image_handler import handle_image
from .handlers.link_handler import handle_link
from .handlers.list_handler import handle_list
from .handlers.paragraph_handler import handle_paragraph
from .handlers.table_handler import handle_table
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
    "a": handle_link,
    "table": handle_table,
}

def generate_ricos_id() -> str:
    """Gera um ID curto para nodos Ricos."""
    return uuid.uuid4().hex[:12]

# Todas as funções auxiliares da versão antiga são mantidas, pois são necessárias para os handlers

def _convert_html_element_to_ricos_nodes(element: Any, **kwargs) -> List[Dict[str, Any]]:
    """
    Converte um elemento BeautifulSoup (nível de bloco) em uma lista de nós Ricos.
    Usa o dispatcher TAG_HANDLERS para delegar o trabalho.
    """
    ricos_nodes: List[Dict[str, Any]] = []
    tag = getattr(element, "name", None)

    if tag:
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

    # Pré-processamento de shortcodes ANTES de tudo
    html = parse_shortcodes(html)

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

    BLOCK_TAGS = {
        "p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "blockquote",
        "img", "br", "table", "div", "hr", "pre", "figure", "figcaption", "iframe"
    }
    inline_buffer = []

    def flush_inline_buffer():
        nonlocal inline_buffer
        if not inline_buffer:
            return
        
        temp_p = soup.new_tag("p")
        for item in inline_buffer:
            temp_p.append(item)
        
        ricos_output_nodes.extend(_convert_html_element_to_ricos_nodes(temp_p, **kwargs))
        inline_buffer = []

    children = list(soup.body.children) if soup.body else list(soup.children)

    for child in children:
        is_block = getattr(child, 'name', None) in BLOCK_TAGS

        if is_block:
            flush_inline_buffer()
            ricos_output_nodes.extend(_convert_html_element_to_ricos_nodes(child, **kwargs))
        else:
            inline_buffer.append(child)
    
    flush_inline_buffer()

    logger.debug("Generated Ricos nodes count: %d", len(ricos_output_nodes))
    return {"nodes": ricos_output_nodes}