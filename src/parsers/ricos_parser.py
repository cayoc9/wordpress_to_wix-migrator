"""
Ricos parser for converting HTML into the Wix Rich Content format.

This module is a copy of the standalone ``ricos_parser.py`` at the
repository root.  It is provided here to satisfy the import path
``src.parsers.ricos_parser``.  See the root-level module for detailed
documentation.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional

from bs4 import BeautifulSoup, Tag

from .handlers.blockquote_handler import handle_blockquote
from .handlers.code_block_handler import handle_code_block
from .handlers.heading_handler import handle_heading
from .handlers.iframe_handler import handle_iframe
from .handlers.image_handler import handle_image
from .handlers.list_handler import handle_list
from .handlers.paragraph_handler import handle_paragraph
from .handlers.utils import extract_youtube_id, iframe_html_for_video, link_block_for_video

__all__ = [
    "convert_html_to_ricos",
    "strip_html_nodes",
]

TAG_HANDLERS: Dict[str, Callable[..., Optional[Dict[str, Any]]]] = {
    "h1": handle_heading,
    "h2": handle_heading,
    "h3": handle_heading,
    "h4": handle_heading,
    "h5": handle_heading,
    "h6": handle_heading,
    "p": handle_paragraph,
    "ul": handle_list,
    "ol": handle_list,
    "blockquote": handle_blockquote,
    "pre": handle_code_block,
    "img": handle_image,
    "iframe": handle_iframe,
}


def _convert_html_element_to_ricos_nodes(
    element: Tag, embed_strategy: str
) -> List[Dict[str, Any]]:
    """Converts a single HTML element to a list of Ricos nodes."""
    name = element.name.lower()
    handler = TAG_HANDLERS.get(name)
    if not handler:
        return []

    if name == "iframe":
        node = handler(element, embed_strategy=embed_strategy)
    else:
        node = handler(element)

    return [node] if node else []


def convert_html_to_ricos(
    html: str, *, embed_strategy: str = "html_iframe"
) -> Dict[str, Any]:
    """
    Convert raw HTML into a Ricos (Wix Rich Content) structure.
    """
    if not html:
        return {"nodes": []}

    soup = BeautifulSoup(html or "", "html.parser")
    nodes: List[Dict[str, Any]] = []

    for el in soup.recursiveChildGenerator():
        if not isinstance(el, Tag):
            continue
        nodes.extend(_convert_html_element_to_ricos_nodes(el, embed_strategy))

    if not nodes:
        text = (soup.get_text(" ", strip=True) or "").strip()
        if text:
            nodes.append(
                {
                    "type": "paragraph",
                    "nodes": [{"type": "text", "text": text, "marks": []}],
                }
            )

    return {"nodes": nodes}


def strip_html_nodes(ricos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove HTML embed nodes from a Ricos structure.
    """
    new_nodes: List[Dict[str, Any]] = []
    for node in ricos.get("nodes", []):
        if node.get("type") == "html":
            html = (node.get("data") or {}).get("html", "")
            m = re.search(r'src="([^\\"]+)"', html)
            url = m.group(1) if m else None
            if url:
                new_nodes.append(
                    {
                        "type": "paragraph",
                        "nodes": [
                            {
                                "type": "link",
                                "data": {"url": url},
                                "nodes": [
                                    {"type": "text", "text": url, "marks": []}
                                ],
                            }
                        ],
                    }
                )
        else:
            new_nodes.append(node)
    ricos["nodes"] = new_nodes
    return ricos
