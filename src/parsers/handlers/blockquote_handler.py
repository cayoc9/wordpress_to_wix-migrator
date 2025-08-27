from __future__ import annotations
from typing import Any, Dict
from bs4.element import Tag

def handle_blockquote(element: Tag) -> Dict[str, Any]:
    """Converte BLOCKQUOTE em nó Ricos BLOCKQUOTE contendo PARAGRAPH/ TEXT."""
    text = element.get_text(" ", strip=True)
    if not text:
        return None
    return {
        "type": "BLOCKQUOTE",
        "nodes": [{
            "type": "PARAGRAPH",
            "nodes": [{"type": "TEXT", "textData": {"text": text, "decorations": []}}],
            "paragraphData": {}
        }],
        "blockquoteData": {"indentation": 1}
    }
