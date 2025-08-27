"""
HTML → Ricos converter utilities
"""

import logging
import inspect
import re
import uuid
from typing import Any, Callable, Dict, List, Optional

from bs4 import BeautifulSoup
from bs4.element import NavigableString

# Importando os handlers da nova arquitetura
from .handlers.blockquote_handler import handle_blockquote
#from .shortcode_parser import parse_shortcodes
from .handlers.code_block_handler import handle_code_block
from .handlers.heading_handler import handle_heading
from .handlers.iframe_handler import handle_iframe
from .handlers.image_handler import handle_image
from .handlers.link_handler import handle_link
from .handlers.list_handler import handle_list
from .handlers.paragraph_handler import handle_paragraph
from .handlers.misc_handlers import handle_line_break, handle_figure # Supondo um handler para <br> e <figure>
from .handlers.script_handler import handle_script
from .utils import generate_ricos_id

__all__ = [
    "convert_html_to_ricos",
    "generate_ricos_id",
]

logger = logging.getLogger(__name__)

def _fname(name: str, trace_prefix: Optional[str] = None) -> str:
    return f"{trace_prefix + '_' if trace_prefix else ''}{name}"

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
    "script": handle_script,
    # "table": handle_table,  # Vamos importar dinamicamente para evitar circular import
}

# Importação dinâmica do handle_table para evitar circular import
def get_table_handler():
    from .handlers.table_handler import handle_table
    return handle_table

# Todas as funções auxiliares da versão antiga são mantidas, pois são necessárias para os handlers

def _convert_html_element_to_ricos_nodes(element: Any, **kwargs) -> List[Dict[str, Any]]:
    """
    Converte um elemento BeautifulSoup (nível de bloco) em uma lista de nós Ricos.
    Usa o dispatcher TAG_HANDLERS para delegar o trabalho.
    """
    ricos_nodes: List[Dict[str, Any]] = []
    tag = getattr(element, "name", None)
    trace_event: Optional[Callable[[Dict[str, Any]], None]] = kwargs.get("trace_event")
    trace_prefix: Optional[str] = kwargs.get("trace_prefix")

    
    logger.debug(f"_convert_html_element_to_ricos_nodes called with tag: {tag}")
    
    if tag:
        handler = TAG_HANDLERS.get(tag)
        logger.debug(f"Handler for tag {tag}: {handler}")
        # Tratamento especial para tabelas para evitar circular import
        if tag == "table":
            handler = get_table_handler()
        
        if handler:
            if trace_event:
                trace_event({
                    "stage": "parser",
                    "event": "handle_tag_start",
                    "tag": tag,
                    "handler": getattr(handler, "__name__", str(handler)),
                })
            # Decide dinamicamente quais kwargs repassar conforme a assinatura do handler
            sig = inspect.signature(handler)
            params = sig.parameters
            supports_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
            handler_kwargs: Dict[str, Any] = {}
            if "image_importer" in params and "image_importer" in kwargs:
                handler_kwargs["image_importer"] = kwargs["image_importer"]
            # Alguns handlers (ex.: iframe) aceitam "embed_strategy" explicitamente
            if "embed_strategy" in params and "embed_strategy" in kwargs:
                handler_kwargs["embed_strategy"] = kwargs["embed_strategy"]
            if supports_kwargs:
                for k in ("trace_dump_dir", "trace_event", "trace_prefix"):
                    if k in kwargs:
                        handler_kwargs[k] = kwargs[k]
            produced = handler(element, **handler_kwargs)
            # Normaliza retorno dos handlers: aceita lista de nós, nó único (dict) ou None
            if produced is None:
                pass
            elif isinstance(produced, list):
                ricos_nodes.extend(produced)
            elif isinstance(produced, dict):
                ricos_nodes.append(produced)
            else:
                logger.debug("Handler %s returned unsupported type: %s", handler, type(produced))
            if trace_event:
                trace_event({
                    "stage": "parser",
                    "event": "handle_tag_end",
                    "tag": tag,
                    "produced_nodes": len(produced),
                })
        else:
            logger.info("No handler found for HTML tag '%s' — converting to HTML node.", tag)
            ricos_nodes.append({
                "type": "HTML",
                "id": generate_ricos_id(),
                "htmlData": {
                    "html": str(element),
                    "source": "HTML",
                    "containerData": {"width": {"custom": "940px"}}
                }
            })
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
    # Rastreabilidade opcional
    trace_dump_dir: Optional[str] = kwargs.get("trace_dump_dir")
    trace_event: Optional[Callable[[Dict[str, Any]], None]] = kwargs.get("trace_event")

    if not html or not html.strip():
        logger.debug("Empty HTML input — returning empty nodes")
        if trace_dump_dir:
            # Dump do HTML vazio para manter consistência do pipeline
            try:
                from src.utils.trace import write_text, write_json  # import tardio para evitar ciclos
                write_text(trace_dump_dir, _fname("02_content_original.html", kwargs.get("trace_prefix")), html or "")
                write_json(trace_dump_dir, _fname("05_ricos.json", kwargs.get("trace_prefix")), {"nodes": []})
            except Exception:
                pass
        return {"nodes": []}

    # Pré-processamento de shortcodes ANTES de tudo
    # html = parse_shortcodes(html)

    # Pré-processamento de shortcodes (lógica mantida da versão antiga)
    def caption_shortcode_to_figure(match):
        img_tag = match.group(2)
        caption_text = match.group(3).strip()
        if caption_text:
            return f'<figure class="wp-caption">{img_tag}<figcaption class="wp-caption-text">{caption_text}</figcaption></figure>'
        else:
            return img_tag

    caption_pattern = re.compile(r'\[caption(.*?)\]\s*(<img .*?>)\s*(.*?)\s*\[/caption\]', re.DOTALL)
    if trace_dump_dir:
        try:
            from src.utils.trace import write_text  # import tardio
            write_text(trace_dump_dir, _fname("02_content_original.html", kwargs.get("trace_prefix")), html)
        except Exception:
            pass
    html = caption_pattern.sub(caption_shortcode_to_figure, html)
    if trace_dump_dir:
        try:
            from src.utils.trace import write_text  # import tardio
            write_text(trace_dump_dir, _fname("03_content_preprocessed.html", kwargs.get("trace_prefix")), html)
        except Exception:
            pass

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
    result = {"nodes": ricos_output_nodes}
    if trace_dump_dir:
        try:
            from src.utils.trace import write_json  # import tardio
            write_json(trace_dump_dir, _fname("05_ricos.json", kwargs.get("trace_prefix")), result)
        except Exception:
            pass
    if trace_event:
        trace_event({
            "stage": "parser",
            "event": "conversion_done",
            "nodes_count": len(ricos_output_nodes),
        })
    return result
