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
    r"\\[([a-zA-Z0-9_-]+)"  # 1: tag
    r"((?:\\s+[a-zA-Z_]+=\"[^\"]*\")*)"  # 2: attrs
    r"\\s*]"
    r"(?:([^\\[]*)\\[/\1\\])?"  # 3: content (opcional)
    r"|\\s*\\[([a-zA-Z0-9_-]+)"  # 4: self-closing tag
    r"((?:\\s+[a-zA-Z_]+=\"[^\"]*\")*)"  # 5: self-closing attrs
    r"\\s*[/]"
)
# ATTR_REGEX = re.compile(r'\s*([a-zA-Z_]+)=\