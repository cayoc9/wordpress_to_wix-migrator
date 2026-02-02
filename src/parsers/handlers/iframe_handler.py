from __future__ import annotations
from typing import Any, Dict, List, Optional
from bs4.element import Tag
from .utils import extract_video_info, iframe_html_for_video, link_block_for_video

def handle_iframe(element: Tag, embed_strategy: str = "NATIVE") -> List[Dict[str, Any]]:
    """Handles iframe elements."""
    nodes: List[Dict[str, Any]] = []
    src = element.get("src")
    if isinstance(src, list):
        src = src[0] if src else ""
    video_info = extract_video_info(src or "")
    
    if video_info:
        platform = video_info["platform"]
        video_id = video_info["id"]
        
        if embed_strategy == "NATIVE":
            # Return Wix native video component
            provider = "YOUTUBE" if platform == "youtube" else "VIMEO" if platform == "vimeo" else platform.upper()
            nodes.append({
                "type": "video",
                "data": {
                    "videoId": video_id,
                    "provider": provider
                }
            })
        elif embed_strategy == "HTML":
            # Return HTML iframe
            nodes.append({"type": "html", "data": {"html": iframe_html_for_video(video_id, platform)}})
        elif embed_strategy == "LINK":
            # Return link block
            nodes.append(link_block_for_video(video_id, platform))
        else:
            # Default fallback to link block if strategy is not recognized
            nodes.append(link_block_for_video(video_id, platform))
    else:
        # Fallback for unrecognized iframes
        if src:
            if isinstance(src, list):
                src = src[0] if src else ""
            nodes.append({
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
            })
    return nodes
