from __future__ import annotations
from typing import Any, Dict
from bs4.element import Tag

def handle_blockquote(element: Tag) -> Dict[str, Any]:
    """Handles blockquote elements."""
    text = element.get_text(" ", strip=True)
    if text:
        return {
            "type": "blockquote",
            "nodes": [{"type": "text", "text": text, "marks": []}],
        }
    return None
