from __future__ import annotations
import re
from typing import Any, Dict, Optional

YOUTUBE_PATTERNS = [
    r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([A-Za-z0-9_-]{11})",
    r"(?:https?://)?(?:www\.)?youtube\.com/embed/([A-Za-z0-9_-]{11})",
    r"(?:https?://)?youtu\.be/([A-Za-z0-9_-]{11})",
]
YOUTUBE_RX = re.compile("|".join(YOUTUBE_PATTERNS))

def extract_youtube_id(url: str) -> Optional[str]:
    """
    Attempt to extract a YouTube video ID from a given URL.

    :param url: The URL to parse.
    :return: The video ID if present, otherwise ``None``.
    """
    if not url:
        return None
    m = YOUTUBE_RX.search(url)
    if not m:
        return None
    for group in m.groups():
        if group:
            return group
    return None

def iframe_html_for_video(video_id: str) -> str:
    """
    Create an HTML iframe embed snippet for a given YouTube video ID.

    :param video_id: The 11-character YouTube video ID.
    :return: The HTML string for embedding the video.
    """
    src = f"https://www.youtube.com/embed/{video_id}"
    return (
        f'<iframe width="560" height="315" src="{src}" '
        'title="YouTube video player" frameborder="0" '
        'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" '
        'allowfullscreen></iframe>'
    )

def link_block_for_video(video_id: str) -> Dict[str, Any]:
    """
    Create a Ricos node representing a link to a YouTube video.  This is
    used as a fallback when the Wix API does not support raw HTML
    embeds.

    :param video_id: The 11-character YouTube video ID.
    :return: A dictionary representing a paragraph node with a play symbol
             and a clickable link.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    thumb = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    return {
        "type": "paragraph",
        "nodes": [
            {"type": "text", "text": "▶ ", "marks": []},
            {
                "type": "link",
                "nodes": [
                    {"type": "text", "text": "Assistir no YouTube", "marks": []}
                ],
                "data": {"url": url},
            },
        ],
        "data": {"thumbnail": thumb},
    }
