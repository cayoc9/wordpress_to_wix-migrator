from __future__ import annotations
from typing import Any, Dict
from bs4.element import Tag

def handle_code_block(element: Tag) -> Dict[str, Any]:
    """Handles preformatted text elements (pre)."""
    code = element.get_text("\n", strip=False)
    return {
        "type": "code-block",
        "nodes": [{"type": "text", "text": code, "marks": []}],
    }
