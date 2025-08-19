from __future__ import annotations

from typing import Any, Dict, List, Optional


# --- Builders for common Ricos nodes ---

def doc(nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"nodes": nodes or []}


def paragraph(text_nodes: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    return {"type": "PARAGRAPH", "nodes": text_nodes or []}


def heading(level: int, text_nodes: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    lvl = max(1, min(6, int(level or 1)))
    return {"type": "HEADING", "level": lvl, "nodes": text_nodes or []}


def blockquote(nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"type": "BLOCKQUOTE", "nodes": nodes}


def divider() -> Dict[str, Any]:
    return {"type": "DIVIDER"}


def code_block(text: str) -> Dict[str, Any]:
    return {"type": "CODE_BLOCK", "nodes": [text_node(text)]}


def list_container(ordered: bool, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "type": "ORDERED_LIST" if ordered else "BULLETED_LIST",
        "nodes": items,
    }


def list_item(nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"type": "LIST_ITEM", "nodes": nodes}


def text_node(text: str, decorations: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    node: Dict[str, Any] = {"type": "TEXT", "text": text or ""}
    if decorations:
        node["decorations"] = decorations
    return node


def deco(deco_type: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    d: Dict[str, Any] = {"type": deco_type}
    if data:
        d["data"] = data
    return d


# --- Minimal validator/normalizer ---

def validate_ricos(document: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure the document follows basic Ricos expectations.
    - Root has 'nodes' list.
    - TEXT is wrapped inside allowed block nodes by construction, but we keep
      a defensive pass for stray TEXT nodes.
    - HEADING has valid 'level'.
    """
    nodes = document.get("nodes")
    if not isinstance(nodes, list):
        return doc([])

    fixed: List[Dict[str, Any]] = []
    for n in nodes:
        if not isinstance(n, dict):
            continue
        t = n.get("type")
        if t == "HEADING":
            lvl = n.get("level")
            if not isinstance(lvl, int) or lvl < 1 or lvl > 6:
                n["level"] = 1
        if t == "TEXT":
            # Wrap stray TEXT in a paragraph
            fixed.append(paragraph([n]))
        else:
            fixed.append(n)
    return doc(fixed)

