from __future__ import annotations
from typing import Any, Dict
from bs4.element import Tag

def handle_code_block(element: Tag) -> Dict[str, Any]:
    """Converte <pre> em nó Ricos CODE_BLOCK com TEXT interno."""
    code = element.get_text("\n", strip=False)
    return {
        "type": "CODE_BLOCK",
        "nodes": [{"type": "TEXT", "textData": {"text": code, "decorations": []}}],
        "codeBlockData": {"textStyle": {"textAlignment": "AUTO"}}
    }
