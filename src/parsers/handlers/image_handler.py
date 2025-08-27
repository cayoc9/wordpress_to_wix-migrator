from __future__ import annotations
from typing import Any, Dict, Optional
from bs4.element import Tag

def handle_image(element: Tag, image_importer: Optional[callable] = None, **kwargs) -> Dict[str, Any]:
    """Converte <img> em nó Ricos IMAGE com Wix Media ID quando possível.

    - Se `image_importer` for fornecido, importa a imagem e usa o ID retornado.
    - Caso contrário, retorna um nó IMAGE com `image.src.url` (fallback).
    """
    src = element.get("src")
    alt = (element.get("alt") or "").strip()
    if not src:
        return None

    media: Dict[str, Any] = {}
    if callable(image_importer):
        media_id = image_importer(src)
        if media_id:
            media = {"src": {"id": media_id}}
        else:
            media = {"src": {"url": src}}
    else:
        media = {"src": {"url": src}}

    node: Dict[str, Any] = {
        "type": "IMAGE",
        "nodes": [],
        "imageData": {
            "containerData": {"width": {"size": "CONTENT"}, "alignment": "CENTER"},
            "image": media,
            "altText": alt,
        },
    }
    return node
