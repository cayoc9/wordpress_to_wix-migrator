import re
from typing import Dict, Callable, Optional

from .shortcode_handlers.button_handler import handle_button
from .shortcode_handlers.embed_handler import handle_embed

SHORTCODE_HANDLERS: Dict[str, Callable] = {
    "button": handle_button,
    "embed": handle_embed,
}

# Regex para capturar: [tag attr="val"]content[/tag] ou [tag attr="val" /]
SHORTCODE_REGEX = re.compile(
    r"\[([a-zA-Z0-9_-]+)"  # 1: tag
    r"((?:\s+[a-zA-Z_]+=\"[^\"]*\")*)"  # 2: attrs
    r"\s*\]"
    r"(?:([^\[]*)\[\/\1\])?"  # 3: content (opcional)
    r"|\[([a-zA-Z0-9_-]+)"  # 4: self-closing tag
    r"((?:\s+[a-zA-Z_]+=\"[^\"]*\")*)"  # 5: self-closing attrs
    r"\s*\/\]"
)
ATTR_REGEX = re.compile(r'\s*([a-zA-Z_]+)=\"([^\"]*)\"')

def _parse_attrs(attr_str: str) -> Dict[str, str]:
    return dict(ATTR_REGEX.findall(attr_str))

def _replace_shortcode(match: re.Match) -> str:
    if match.group(1):  # Shortcode com conteúdo
        tag = match.group(1).lower()
        attrs = _parse_attrs(match.group(2))
        content = match.group(3)
    else:  # Shortcode auto-fechado
        tag = match.group(4).lower()
        attrs = _parse_attrs(match.group(5))
        content = None

    handler = SHORTCODE_HANDLERS.get(tag)
    if handler:
        return handler(attrs=attrs, content=content)
    return match.group(0) # Retorna o shortcode original se não houver handler

def parse_shortcodes(html: str) -> str:
    """Converte shortcodes do WordPress em HTML padrão."""
    if not html:
        return ""
    return SHORTCODE_REGEX.sub(_replace_shortcode, html)