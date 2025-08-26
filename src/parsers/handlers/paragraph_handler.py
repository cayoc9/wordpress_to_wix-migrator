from __future__ import annotations
from typing import Any, Dict, List
from bs4.element import Tag

def handle_paragraph(element: Tag) -> Dict[str, Any]:
    """Handles paragraph elements (p)."""
    text = element.get_text(" ", strip=True)
    if text:
        return {
            "type": "paragraph",
            "nodes": [{"type": "text", "text": text, "marks": []}],
        }
    return None
