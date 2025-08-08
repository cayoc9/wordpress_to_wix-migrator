"""
Ricos parser for converting HTML into the Wix Rich Content format.

This module is a copy of the standalone ``ricos_parser.py`` at the
repository root.  It is provided here to satisfy the import path
``src.parsers.ricos_parser``.  See the root-level module for detailed
documentation.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup

__all__ = [
    "convert_html_to_ricos",
    "strip_html_nodes",
]

# Patterns used to extract YouTube video identifiers.  This list covers the
# typical URL formats encountered in WordPress exports: watch URLs,
# embed URLs and short youtu.be links.
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

def convert_html_to_ricos(html: str, *, embed_strategy: str = "html_iframe") -> Dict[str, Any]:
    """
    Convert raw HTML into a Ricos (Wix Rich Content) structure.

    Supported HTML elements include headings (h1–h6), paragraphs, lists,
    blockquotes, code blocks, images and YouTube iframes.  Images are
    represented with their original ``src`` and ``alt`` attributes – it is
    the responsibility of the caller to replace those URLs once they
    have been uploaded to Wix.

    The ``embed_strategy`` parameter dictates how YouTube iframes are
    handled:

    * ``"html_iframe"`` (default): produce a node of type ``html`` containing
      the raw iframe markup.  If the Wix API rejects the request (HTTP
      400), callers should catch the exception, remove HTML nodes using
      :func:`strip_html_nodes`, and retry with a fallback strategy.
    * Any other value: represent the video as a simple link with a
      play indicator; this requires no special support on the Wix side.

    :param html: The input HTML string.
    :param embed_strategy: Strategy for handling video embeds.
    :return: A dictionary with a single key ``nodes`` holding a list of
             Ricos nodes.
    """
    if not html:
        return {"nodes": []}

    soup = BeautifulSoup(html or "", "html.parser")
    nodes: List[Dict[str, Any]] = []

    def add_text_para(text: str) -> None:
        text = (text or "").strip()
        if text:
            nodes.append({
                "type": "paragraph",
                "nodes": [{"type": "text", "text": text, "marks": []}],
            })

    for el in soup.recursiveChildGenerator():
        if not getattr(el, "name", None):
            continue
        name = el.name.lower()

        if name in [f"h{i}" for i in range(1, 7)]:
            level = int(name[-1])
            text = el.get_text(strip=True)
            if text:
                nodes.append({
                    "type": "heading",
                    "data": {"level": level},
                    "nodes": [{"type": "text", "text": text, "marks": []}],
                })
        elif name == "p":
            txt = el.get_text(" ", strip=True)
            if txt:
                add_text_para(txt)
        elif name in ("ul", "ol"):
            items: List[Dict[str, Any]] = []
            for li in el.find_all("li", recursive=False):
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
            nodes.append({
                "type": "bulleted-list" if name == "ul" else "numbered-list",
                "nodes": items,
            })
        elif name == "blockquote":
            txt = el.get_text(" ", strip=True)
            if txt:
                nodes.append({
                    "type": "blockquote",
                    "nodes": [{"type": "text", "text": txt, "marks": []}],
                })
        elif name == "pre":
            code = el.get_text("\n", strip=False)
            nodes.append({
                "type": "code-block",
                "nodes": [{"type": "text", "text": code, "marks": []}],
            })
        elif name == "img":
            src = el.get("src")
            alt = el.get("alt") or ""
            if src:
                nodes.append({
                    "type": "image",
                    "data": {"src": src, "alt": alt},
                    "nodes": [],
                })
        elif name == "iframe":
            src = el.get("src")
            vid = extract_youtube_id(src or "")
            if vid and embed_strategy == "html_iframe":
                nodes.append({"type": "html", "data": {"html": iframe_html_for_video(vid)}})
            elif vid:
                nodes.append(link_block_for_video(vid))
            else:
                if src:
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

    if not nodes:
        add_text_para(soup.get_text(" ", strip=True))
    return {"nodes": nodes}

def strip_html_nodes(ricos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove HTML embed nodes from a Ricos structure.  Each HTML node is
    replaced by a paragraph containing a link to the original embedded
    resource.  Any node without a ``data.html`` attribute is dropped.

    :param ricos: The rich content structure returned by
                  :func:`convert_html_to_ricos`.
    :return: A modified rich content structure with HTML nodes removed.
    """
    new_nodes: List[Dict[str, Any]] = []
    for node in ricos.get("nodes", []):
        if node.get("type") == "html":
            html = (node.get("data") or {}).get("html", "")
            m = re.search(r'src="([^\\"]+)"', html)
            url = m.group(1) if m else None
            if url:
                new_nodes.append({
                    "type": "paragraph",
                    "nodes": [
                        {
                            "type": "link",
                            "data": {"url": url},
                            "nodes": [
                                {"type": "text", "text": url, "marks": []}
                            ],
                        }
                    ],
                })
        else:
            new_nodes.append(node)
    ricos["nodes"] = new_nodes
    return ricos
