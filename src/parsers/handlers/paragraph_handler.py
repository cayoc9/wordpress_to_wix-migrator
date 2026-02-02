from __future__ import annotations
from typing import Any, Dict, List
from bs4.element import Tag

def handle_paragraph(element: Tag, **kwargs) -> List[Dict[str, Any]]:
    """Handles paragraph elements (p)."""
    from .utils import get_text_nodes_with_decorations, generate_ricos_id

    nodes = get_text_nodes_with_decorations(element)
    if not nodes:
        return []

    return [{
        "id": generate_ricos_id(),
        "type": "PARAGRAPH",
        "nodes": nodes,
        "paragraphData": {
            "textStyle": {"textAlignment": "AUTO"},
            "indentation": 0
        }
    }]
