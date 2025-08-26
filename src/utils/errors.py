"""
Structured logging helpers for migration errors and successes.

The :mod:`src.utils.errors` module centralizes the writing of log entries for
both failed and successful operations during the migration. Each entry is
appended to a JSON Lines file under ``reports/migration`` so that the
information can be reviewed or parsed after a run.
"""

from __future__ import annotations

import json
import os
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Mapping of event codes used throughout the migration to descriptive messages.
ERRORS: Dict[str, str] = {
    "MEDIA_UPLOAD_FAILED": "Failed to upload media to Wix",
    "WIX_DRAFT_400": "Wix API returned 400 when creating draft",
    "WIX_NETWORK_ERROR": "Network error communicating with Wix",
    "POST_PUBLISH_FAILED": "Failed to publish post",
    "DRAFT_CREATED": "Draft created successfully",
    "POST_PUBLISHED": "Post published successfully",
    "IMAGE_IMPORTED": "Image imported and uploaded successfully",
}

_REPORT_DIR = os.path.join("reports", "migration")
_ERROR_LOG = os.path.join(_REPORT_DIR, "errors.jsonl")
_OK_LOG = os.path.join(_REPORT_DIR, "success.jsonl")


def _write_jsonl(path: str, data: Dict[str, Any]) -> None:
    """Append ``data`` as a JSON object followed by a newline to ``path``."""
    try:
        os.makedirs(_REPORT_DIR, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
            f.write("\n")
    except IOError as e:
        logger.error("Failed to write to log file %s: %s", path, e)


def report_error(code: str, post: Dict[str, Any], exc: Optional[Exception] = None) -> None:
    """
    Log an error event for ``post``.
    """
    message = ERRORS.get(code, code)
    entry: Dict[str, Any] = {
        "code": code,
        "message": message,
        "slug": post.get("slug"),
        "title": post.get("title"),
    }
    if exc is not None:
        entry["error_details"] = str(exc)
    logger.error("[FAIL] %s - Slug: %s", message, post.get('slug', 'N/A'))
    _write_jsonl(_ERROR_LOG, entry)


def report_ok(code: str, post: Dict[str, Any], extra: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a successful event for ``post``.
    """
    message = ERRORS.get(code, code)
    entry: Dict[str, Any] = {
        "code": code,
        "message": message,
        "slug": post.get("slug"),
        "title": post.get("title"),
    }
    if extra:
        entry.update(extra)
    logger.info("[OK] %s - Slug: %s", message, post.get('slug', 'N/A'))
    _write_jsonl(_OK_LOG, entry)