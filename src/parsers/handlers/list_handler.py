from __future__ import annotations
from typing import Any, Dict, List
from bs4.element import Tag

def handle_list(element: Tag) -> Dict[str, Any]:
    """Handles list elements (ul, ol)."""
    items: List[Dict[str, Any]] = []
    for li in element.find_all("li", recursive=False):
        items.append({
            "type": "list-item",
            "nodes": [
                {
                    "type": "text",
                    "text": li.get_text(" ", strip=True),
                    "marks": [],
                }
            ],
        })
    return {
        "type": "bulleted-list" if element.name == "ul" else "numbered-list",
        "nodes": items,
    }
