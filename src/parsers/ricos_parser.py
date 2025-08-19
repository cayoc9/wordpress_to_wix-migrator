"""
Ricos parser for converting HTML into the Wix Rich Content format.

This module is a copy of the standalone ``ricos_parser.py`` at the
repository root.  It is provided here to satisfy the import path
``src.parsers.ricos_parser``.  See the root-level module for detailed
documentation.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Callable
from bs4 import BeautifulSoup, NavigableString
import uuid

__all__ = [
    "convert_html_to_ricos",
]

def convert_html_to_ricos(html: str, *, embed_strategy: str = "html_iframe", image_importer: Optional[Callable[[str], Optional[str]]] = None) -> Dict[str, Any]:
    """
    Converte HTML para o formato Ricos do Wix usando HtmlNode para HTML bruto.
    
    Esta versão envia o HTML bruto como um bloco HTML embutido,
    o que é suportado pela API do Wix Blog através do HtmlNode.
    """
    print(f"DEBUG: convert_html_to_ricos called with HTML (length {len(html) if html else 0}): {html[:200] if html else ''}...")
    
    if not html or not html.strip():
        print("DEBUG: HTML is empty, returning empty nodes")
        return {"nodes": []}
    
    # Criar um HtmlNode que contém o HTML bruto
    # Isso é suportado pela API do Wix Blog
    html_node = {
        "type": "HTML",
        "htmlData": {
            "html": html,
            "source": "HTML"
        },
        "id": str(uuid.uuid4())  # ID único para o node
    }
    
    print(f"DEBUG: Created HTML node with raw HTML content")
    return {"nodes": [html_node]}