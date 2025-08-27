from __future__ import annotations
from typing import Any, Dict, List
from bs4.element import Tag

def handle_heading(element: Tag) -> Dict[str, Any]:
    """Handles heading elements (h1-h6)."""
    level = int(element.name[-1])
    text = element.get_text(strip=True)
    if text:
        return {
            "type": "HEADING",
            "headingData": {"level": level},
            "nodes": [{"type": "TEXT", "textData": {"text": text, "decorations": []}}],
        }
    return None
