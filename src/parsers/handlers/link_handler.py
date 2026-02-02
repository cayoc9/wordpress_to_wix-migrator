from __future__ import annotations
from typing import Any, Dict, List
from bs4.element import Tag
from .utils import get_text_nodes_with_decorations, generate_ricos_id

def handle_link(element: Tag, **kwargs) -> List[Dict[str, Any]]:
    """Handles link elements (a)."""
    
    nodes = get_text_nodes_with_decorations(element)
    if not nodes:
        return []

    # Envolve o link em um nó de parágrafo para manter a estrutura de bloco
    return [{
        "id": generate_ricos_id(),
        "type": "PARAGRAPH",
        "nodes": nodes,
        "paragraphData": {
            "textStyle": {"textAlignment": "AUTO"},
            "indentation": 0
        }
    }]