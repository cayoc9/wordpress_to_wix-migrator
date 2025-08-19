"""
Ricos parser for converting HTML into the Wix Rich Content format using the
official Wix REST API.
"""

from __future__ import annotations

import json
from typing import Any, Dict

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

    # Truncate HTML if it exceeds Wix's limit of 10000 characters
    if len(html) > 10000:
        print(f"WARNING: HTML content is {len(html)} characters, truncating to 10000 characters")
        html = html[:10000]

    api_url = f"{cfg['base_url']}/ricos/v1/ricos-document/convert/to-ricos"
    
    # A comprehensive list of plugins based on API schema to support most content
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
        # The actual Ricos document is nested under the 'document' key
        return ricos_response.get("document", {"nodes": []})

    except requests.exceptions.HTTPError as e:
        print(f"Failed to convert HTML via Wix API after multiple retries. Error: {e}")
        if e.response:
            print(f"Response body: {e.response.text}")
        # Fallback: return a simple Ricos document with the HTML as a single text node
        # This ensures the migration can continue even if the API fails
        return {
            "nodes": [
                {
                    "type": "PARAGRAPH",
                    "nodes": [
                        {
                            "type": "TEXT",
                            "text": "Content could not be converted to Ricos format. Displaying raw HTML:",
                            "bold": True
                        }
                    ]
                },
                {
                    "type": "PARAGRAPH",
                    "nodes": [
                        {
                            "type": "TEXT",
                            "text": html[:5000] + ("..." if len(html) > 5000 else "")  # Limit size
                        }
                    ]
                }
            ]
        }
