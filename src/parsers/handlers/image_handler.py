from __future__ import annotations
from typing import Any, Dict
from bs4.element import Tag

def handle_image(element: Tag) -> Dict[str, Any]:
    """Handles image elements (img)."""
    src = element.get("src")
    alt = element.get("alt") or ""
    if src:
        return {
            "type": "image",
            "data": {"src": src, "alt": alt},
            "nodes": [],
        }
    return None
