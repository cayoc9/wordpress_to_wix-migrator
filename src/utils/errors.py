"""
Structured logging helpers for migration errors and successes.

The :mod:`src.utils.errors` module centralizes the writing of log entries for
both failed and successful operations during the migration.  Each entry is
appended to a JSON Lines file under ``reports/migration`` so that the
information can be reviewed or parsed after a run.

Two public functions are provided:

``report_error``
    Record an error that occurred for a post.  An optional exception can be
    supplied and will be serialized to the log.

``report_ok``
    Record a successful step for a post.  Additional key/value information can
    be attached to the entry via the ``extra`` parameter.

The ``ERRORS`` dictionary maps error or event codes to human readable
messages.  Codes not present in the dictionary fall back to the code itself.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

# Mapping of event codes used throughout the migration to descriptive messages.
# The keys include both error and success codes as the same lookup is used by
# :func:`report_error` and :func:`report_ok`.
ERRORS: Dict[str, str] = {
    "MEDIA_UPLOAD": "Failed to upload media to Wix",
    "WIX_DRAFT_400": "Wix API returned 400 when creating draft",
    "WIX_NETWORK": "Network error communicating with Wix",
    "PUBLISH": "Failed to publish post",
    "DRAFT_CREATED": "Draft created successfully",
    "PUBLISHED": "Post published successfully",
}

_REPORT_DIR = os.path.join("reports", "migration")
_ERROR_LOG = os.path.join(_REPORT_DIR, "errors.jsonl")
_OK_LOG = os.path.join(_REPORT_DIR, "success.jsonl")


def _write_jsonl(path: str, data: Dict[str, Any]) -> None:
    """Append ``data`` as a JSON object followed by a newline to ``path``."""
    os.makedirs(_REPORT_DIR, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
        f.write("\n")


def report_error(code: str, post: Dict[str, Any], exc: Optional[Exception] = None) -> None:
    """Log an error event for ``post``.

    Parameters
    ----------
    code:
        A key identifying the type of error.  If ``code`` is present in
        :data:`ERRORS` its value will be used as the message.
    post:
        The post dictionary associated with the error.  Only the ``Slug`` and
        ``Title`` keys are referenced if present.
    exc:
        Optional exception instance that triggered the error.  The string
        representation of the exception will be included in the log entry.
    """
    message = ERRORS.get(code, code)
    entry: Dict[str, Any] = {
        "code": code,
        "message": message,
        "slug": post.get("Slug"),
        "title": post.get("Title"),
    }
    if exc is not None:
        entry["error"] = str(exc)
    print(f"[ERROR] {message} - {post.get('Slug', '')}")
    _write_jsonl(_ERROR_LOG, entry)


def report_ok(code: str, post: Dict[str, Any], extra: Optional[Dict[str, Any]] = None) -> None:
    """Log a successful event for ``post``.

    Parameters
    ----------
    code:
        A key identifying the type of event.
    post:
        The post dictionary associated with the event.
    extra:
        Optional dictionary of additional fields to merge into the log entry.
    """
    message = ERRORS.get(code, code)
    entry: Dict[str, Any] = {
        "code": code,
        "message": message,
        "slug": post.get("Slug"),
        "title": post.get("Title"),
    }
    if extra:
        entry.update(extra)
    print(f"[OK] {message} - {post.get('Slug', '')}")
    _write_jsonl(_OK_LOG, entry)
