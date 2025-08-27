import logging
import re
from typing import Dict, Callable, Optional

from .shortcode_handlers.button_handler import handle_button
from .shortcode_handlers.embed_handler import handle_embed
from .shortcode_handlers.gallery_handler import handle_gallery

logger = logging.getLogger(__name__)

SHORTCODE_HANDLERS: Dict[str, Callable] = {
    "button": handle_button,
    "embed": handle_embed,
    "gallery": handle_gallery,
}

# Regex para capturar: [tag attr="val"]content[/tag] ou [tag attr="val" /]
SHORTCODE_REGEX = re.compile(
    r"\[([a-zA-Z0-9_-]+)"  # 1: tag
    r"((?:\s+[a-zA-Z_]+=\"[^\"]*\")*)"  # 2: attrs
    r"\s*\]"
    r"(?:([^[]*)\[/\1\])?"  # 3: content (opcional)
    r"|\s*\[([a-zA-Z0-9_-]+)"  # 4: self-closing tag
    r"((?:\s+[a-zA-Z_]+=\"[^\"]*\")*)"  # 5: self-closing attrs
    r"\s*/\]"
)

def parse_shortcodes(html: str) -> str:
    """
    Parse shortcodes in HTML and replace them with appropriate HTML elements.
    """
    def replace_shortcode(match):
        # Extrair grupos do match
        tag = match.group(1) or match.group(4)
        attrs_str = match.group(2) or match.group(5)
        content = match.group(3)
        
        # Parse attributes
        attrs = {}
        if attrs_str:
            attr_regex = re.compile(r'\s*([a-zA-Z_]+)="([^"]*)"')
            for attr_match in attr_regex.finditer(attrs_str):
                attr_name, attr_value = attr_match.groups()
                attrs[attr_name] = attr_value
        
        # Chamar o handler apropriado
        handler = SHORTCODE_HANDLERS.get(tag)
        if handler:
            return handler(attrs, content)
        
        # Se não houver handler, retornar o shortcode original
        return match.group(0)
    
    return SHORTCODE_REGEX.sub(replace_shortcode, html)