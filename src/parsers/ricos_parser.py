"""
Ricos parser for converting HTML into the Wix Rich Content format using the
official Wix REST API.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, Callable

import requests

# Import utilities from the wix_migrator to ensure consistent patterns
from src.migrators.wix_migrator import RateLimiter, wix_headers, with_retries

__all__ = [
    "convert_html_to_ricos",
]

# Use a single rate limiter instance, consistent with wix_migrator.py
_limiter = RateLimiter(180)


def convert_html_to_ricos(
    cfg: Dict[str, Any],
    html: str,
    *,
    embed_strategy: str = "api",
    image_importer: Optional[Callable[[str], Optional[str]]] = None,
) -> Dict[str, Any]:
    """
    Converts an HTML string to the Wix Ricos format using the Wix REST API.

    This function adheres to the project's standards for API calls, including
    rate limiting, retry logic, and configuration handling as defined in
    `wix_migrator.py`.

    Args:
        cfg: The application configuration dictionary, containing `base_url`
             and `access_token`.
        html: The raw HTML string to be converted.
        embed_strategy: (Ignored) Kept for compatibility.
        image_importer: (Ignored) Kept for compatibility.

    Returns:
        A dictionary representing the Ricos document structure.

    Raises:
        requests.exceptions.RequestException: For API or network-related errors
                                            after all retries have failed.
    """
    if not html or not html.strip():
        return {"nodes": []}

    # Prefer not to truncate here. We'll attempt API conversion first; if it fails,
    # we fall back to a local HTML→Ricos converter without hard cuts.

    api_url = f"{cfg['base_url']}/ricos/v1/ricos-document/convert/to-ricos"
    
    # Use the documented payload shape for this endpoint: { html, options: { plugins } }
    # Keep a broad plugin set that covers common content types.
    enabled_plugins = [
        "TABLE", "HEADING", "IMAGE", "LINK", "VIDEO", "HTML", "TEXT_COLOR",
        "TEXT_HIGHLIGHT", "LINE_SPACING", "SPOILER", "POLL", "MENTIONS",
        "LINK_PREVIEW", "LINK_BUTTON", "INDENT", "GIPHY", "GALLERY", "FILE",
        "EMOJI", "DIVIDER", "COLLAPSIBLE_LIST", "CODE_BLOCK", "AUDIO", "ACTION_BUTTON"
    ]

    payload = {"html": html, "options": {"plugins": enabled_plugins}}

    # This inner function is the unit of work for the retry wrapper.
    def do_request() -> requests.Response:
        # Wait before the request to respect rate limits.
        _limiter.wait()
        return requests.post(
            api_url,
            headers={**wix_headers(cfg), "Content-Type": "application/json"},
            data=json.dumps(payload),
        )

    try:
        # Execute the request with the project's standard retry logic.
        response = with_retries(do_request)
        ricos_response = response.json()
        # The Ricos document may be under 'document' or directly returned
        doc = ricos_response.get("document") if isinstance(ricos_response, dict) else None
        if isinstance(doc, dict) and "nodes" in doc:
            return doc
        if isinstance(ricos_response, dict) and "nodes" in ricos_response:
            return ricos_response
        # Fallback to local conversion if shape is unexpected
        return _local_html_to_ricos(html)

    except requests.exceptions.HTTPError as e:
        print(f"Failed to convert HTML via Wix API after multiple retries. Error: {e}")
        if e.response:
            print(f"Response body: {e.response.text}")
        # Fallback: best-effort local conversion to avoid raw-HTML text-only content
        return _local_html_to_ricos(html)


def _local_html_to_ricos(html: str) -> Dict[str, Any]:
    """Very simple HTML→Ricos converter using BeautifulSoup.

    Maps common tags to PARAGRAPH/TEXT and HEADING nodes, and converts links
    to inline text with the URL. Images are represented as text placeholders
    to avoid invalid schema when no media ID is available.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html or "", "html.parser")
    nodes: list[dict] = []

    def add_paragraph(text: str) -> None:
        text = (text or "").strip()
        if not text:
            return
        # Split on newlines to avoid giant text nodes
        for piece in [p for p in text.splitlines() if p.strip()]:
            nodes.append({
                "type": "PARAGRAPH",
                "nodes": [{"type": "TEXT", "text": piece}]
            })

    # Walk only top-level block elements; fallback to full text if none
    block_tags = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote"}
    found_any = False
    for el in soup.body.children if soup.body else soup.children:
        if getattr(el, "name", None) in block_tags:
            found_any = True
            name = el.name.lower()
            if name.startswith("h") and len(name) == 2 and name[1].isdigit():
                lvl = int(name[1])
                text = el.get_text(" ", strip=True)
                nodes.append({
                    "type": "HEADING",
                    "level": max(1, min(6, lvl)),
                    "nodes": [{"type": "TEXT", "text": text}],
                })
            elif name == "blockquote":
                text = el.get_text(" ", strip=True)
                nodes.append({
                    "type": "BLOCKQUOTE",
                    "nodes": [{"type": "PARAGRAPH", "nodes": [{"type": "TEXT", "text": text}]}]
                })
            elif name == "li":
                add_paragraph(el.get_text(" ", strip=True))
            else:
                # p and everything else here
                # Inline anchors: append " (url)" after text to preserve information
                for a in el.find_all("a"):
                    href = a.get("href")
                    if href:
                        a.string = (a.get_text(strip=True) or href) + f" ({href})"
                # Images become placeholders
                for img in el.find_all("img"):
                    alt = img.get("alt") or "imagem"
                    src = img.get("src") or ""
                    img.replace_with(soup.new_string(f"[Imagem: {alt}] {src}".strip()))
                add_paragraph(el.get_text(" ", strip=True))

    if not found_any:
        # Fallback to whole-document text if no block elements detected
        text = soup.get_text(" ", strip=True)
        add_paragraph(text)

    return {"nodes": nodes or [{"type": "PARAGRAPH", "nodes": [{"type": "TEXT", "text": ""}]}]}
