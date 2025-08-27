from __future__ import annotations
from typing import Any, Dict, List
from bs4.element import Tag

def handle_list(element: Tag) -> Dict[str, Any]:
    """Converte UL/OL para Ricos BULLETED_LIST/ORDERED_LIST com LIST_ITEMs."""
    list_type = "BULLETED_LIST" if element.name == "ul" else "ORDERED_LIST"
    items: List[Dict[str, Any]] = []
    for li in element.find_all("li", recursive=False):
        text = li.get_text(" ", strip=True)
        if not text:
            continue
        items.append({
            "type": "LIST_ITEM",
            "nodes": [{
                "type": "PARAGRAPH",
                "nodes": [{"type": "TEXT", "textData": {"text": text, "decorations": []}}],
                "paragraphData": {}
            }]
        })
    return {
        "type": list_type,
        "nodes": items,
        f"{list_type.lower()}Data": {"indentation": 0}
    }
