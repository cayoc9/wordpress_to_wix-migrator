from __future__ import annotations

from html import unescape
import re
from typing import List


def _normalize_label(value: str) -> str:
    """Unescape HTML entities and collapse inner whitespace.

    Preserves original casing but trims leading/trailing spaces
    and converts sequences of whitespace to a single space.
    """
    if not value:
        return ""
    text = unescape(value).strip()
    # Collapse multiple whitespace to single space
    text = re.sub(r"\s+", " ", text)
    return text


def parse_tags_field(field: str) -> List[str]:
    """
    Parse and normalize a tags field from the CSV export.

    - Splits primarily on '|', with ',' as a fallback
    - Unescapes HTML entities (e.g., '&amp;' -> '&')
    - Trims spaces, collapses inner whitespace
    - Deduplicates case-insensitively while preserving first-seen casing

    Returns a list of cleaned tag labels suitable for Wix Blog Tags API.
    """
    if not field:
        return []

    text = field.strip()
    parts = [p.strip() for p in (text.split("|") if "|" in text else text.split(","))]
    seen_lower = set()
    result: List[str] = []
    for p in parts:
        if not p:
            continue
        label = _normalize_label(p)
        key = label.lower()
        if label and key not in seen_lower:
            seen_lower.add(key)
            result.append(label)
    return result


def to_wix_terms_payload(categories: List[str], tags: List[str]) -> dict:
    """
    Build a simple Wix-compatible payload structure representing categories and tags
    that can be iterated to create terms using the Blog REST APIs.

    Note: Actual API calls are done elsewhere. This helper simply organizes
    labels in the shape expected by the `create` endpoints.
    """
    return {
        "categories": [{"category": {"label": _normalize_label(c)}} for c in categories if c],
        "tags": [{"label": _normalize_label(t)} for t in tags if t],
    }

