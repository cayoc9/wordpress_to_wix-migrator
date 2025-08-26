from __future__ import annotations
from typing import Any, Dict
from bs4.element import Tag
from .utils import extract_youtube_id, iframe_html_for_video, link_block_for_video

def handle_iframe(element: Tag, embed_strategy: str) -> Dict[str, Any]:
    """Handles iframe elements."""
    src = element.get("src")
    vid = extract_youtube_id(src or "")
    if vid and embed_strategy == "html_iframe":
        return {"type": "html", "data": {"html": iframe_html_for_video(vid)}}
    elif vid:
        return link_block_for_video(vid)
    else:
        if src:
            return {
                "type": "paragraph",
                "nodes": [
                    {
                        "type": "link",
                        "data": {"url": src},
                        "nodes": [
                            {"type": "text", "text": src, "marks": []}
                        ],
                    }
                ],
            }
    return None
