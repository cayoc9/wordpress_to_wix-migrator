"""
Error reporting utilities for the WordPress → Wix migration.

This module provides a simple mechanism for recording structured errors
during the migration process.  Each error is associated with a unique
code (e.g., ``MEDIA_UPLOAD``, ``WIX_DRAFT_400``) and includes the
original post data that caused the failure, along with any relevant
exception information.  Successful operations can also be logged using
:func:`report_ok`.

All errors and successes are stored in the global ``ERRORS`` dictionary,
keyed by post slug.  This allows for easy generation of a summary report
at the end of the migration, detailing which posts succeeded, which
failed, and why.

Usage example::

    from src.utils.errors import report_error, report_ok, ERRORS

    post = {"Slug": "my-first-post", ...}
    try:
        # ... perform some operation ...
        report_ok("DRAFT_CREATED", post, {"draft_id": "123"})
    except Exception as e:
        report_error("WIX_NETWORK", post, e)

    # Later, to generate a report:
    for slug, entries in ERRORS.items():
        print(f"Post: {slug}")
        for entry in entries:
            print(f"  - {entry['status']}: {entry['code']}")
            if entry.get('error'):
                print(f"    {entry['error']}")

"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# Global dictionary to store errors and successes, keyed by post slug.
# Each value is a list of dictionaries, allowing multiple events per post.
ERRORS: Dict[str, List[Dict[str, Any]]] = {}

def report_error(code: str, post: Dict[str, Any], error: Optional[Exception] = None) -> None:
    """
    Record a failed migration step for a specific post.

    :param code: A unique, uppercase string identifying the error type.
    :param post: The normalized post dictionary that was being processed.
    :param error: The exception that was raised, if any.
    """
    slug = post.get("Slug") or post.get("ID") or "unknown-post"
    if slug not in ERRORS:
        ERRORS[slug] = []
    err_obj = {
        "status": "error",
        "code": code,
        "post": post,
    }
    if error:
        err_obj["error"] = str(error)
    ERRORS[slug].append(err_obj)

def report_ok(code: str, post: Dict[str, Any], data: Optional[Dict[str, Any]] = None) -> None:
    """
    Record a successful migration step for a specific post.

    :param code: A unique, uppercase string identifying the success type.
    :param post: The normalized post dictionary that was being processed.
    :param data: Optional dictionary of supplemental data (e.g., new URL).
    """
    slug = post.get("Slug") or post.get("ID") or "unknown-post"
    if slug not in ERRORS:
        ERRORS[slug] = []
    ok_obj = {
        "status": "ok",
        "code": code,
        "post": post,
    }
    if data:
        ok_obj.update(data)
    ERRORS[slug].append(ok_obj)
