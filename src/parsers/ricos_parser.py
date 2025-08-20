"""
Ricos converter orchestration.

By default, uses a local HTML→Ricos converter that maps common HTML
elements to the Wix Ricos Document format without calling Wix APIs.
Optionally, when explicitly enabled in configuration, attempts the
Wix REST API "convert-to-ricos" endpoint.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, Callable

import requests

# Import utilities from the wix_migrator to ensure consistent patterns
from src.migrators.wix_migrator import RateLimiter, wix_headers, with_retries, import_image_from_url
from .ricos_local import convert_html_to_ricos_local

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
    Converts an HTML string to the Wix Ricos format.

    Default behavior: local conversion (no network).
    If cfg["enable_remote_convert"] is True, tries the Wix REST API first
    and falls back to local conversion on error or invalid output.

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

    # Should we try the remote Wix converter first?
    try_remote: bool = bool(cfg.get("enable_remote_convert"))
    if not try_remote:
        # Provide image importer using Wix Media import endpoint when cfg is provided
        def _img_importer(url: str) -> Optional[str]:
            return import_image_from_url(cfg, url)
        table_mode = str(cfg.get("table_mode", "html"))  # html|plugin|paragraphs
        return convert_html_to_ricos_local(html, image_importer=_img_importer, table_mode=table_mode)

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
        def _img_importer(url: str) -> Optional[str]:
            return import_image_from_url(cfg, url)
        table_mode = str(cfg.get("table_mode", "html"))
        return convert_html_to_ricos_local(html, image_importer=_img_importer, table_mode=table_mode)

    except requests.exceptions.HTTPError as e:
        print(f"Failed to convert HTML via Wix API after multiple retries. Error: {e}")
        if e.response:
            print(f"Response body: {e.response.text}")
        # Fallback: best-effort local conversion to avoid raw-HTML text-only content
        def _img_importer(url: str) -> Optional[str]:
            return import_image_from_url(cfg, url)
        table_mode = str(cfg.get("table_mode", "html"))
        return convert_html_to_ricos_local(html, image_importer=_img_importer, table_mode=table_mode)
