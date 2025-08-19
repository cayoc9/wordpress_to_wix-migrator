from __future__ import annotations

from html import unescape
import re
import unicodedata
from typing import Dict, List


# Canonical category names and slugs provided by the user
_SLUG_TO_NAME: Dict[str, str] = {
    "dicas-hacks": "Dicas & Hacks",
    "gestao-organizacao": "Gestão & Organização",
    "inovacoes-investimentos": "Inovações & investimentos",
    "legislacao": "Legislação",
    "marketing": "Marketing",
    "nota-fiscal": "Nota Fiscal",
    "saude-financeira": "Saúde financeira",
    "tudo-para-mei": "Tudo Para MEI",
    "tutoriais": "Tutoriais",
    "uncategorized": "Uncategorized",
}


def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


def _canonical_key(text: str) -> str:
    # Unescape HTML entities, trim, collapse whitespace, lowercase, strip accents
    t = unescape(text or "").strip()
    t = re.sub(r"\s+", " ", t)
    t = t.lower()
    t = _strip_accents(t)
    # normalize variants of ampersand
    t = t.replace("&amp;", "&")
    t = t.replace(" e ", " & ")  # sometimes exported as " e "
    return t


# Build name->slug map using canonicalization
_NAME_TO_SLUG: Dict[str, str] = {}
for slug, name in _SLUG_TO_NAME.items():
    _NAME_TO_SLUG[_canonical_key(name)] = slug


def canonicalize_category(value: str) -> str:
    """
    Map a raw category value (possibly with HTML entities or case variants)
    to the canonical display name. If not recognized, returns the unescaped
    trimmed original value.
    """
    if not value:
        return ""

    raw = unescape(value).strip()
    key = _canonical_key(raw)

    # Direct slug match
    if key in _SLUG_TO_NAME:
        return _SLUG_TO_NAME[key]

    # Match by canonicalized name
    slug = _NAME_TO_SLUG.get(key)
    if slug:
        return _SLUG_TO_NAME[slug]

    # Not found, return cleaned original (entities fixed)
    return raw


def parse_categories_field(field: str) -> List[str]:
    """
    Parse and normalize a categories field from the CSV.

    - Splits primarily on '|', falling back to ',' if needed
    - Fixes HTML entities (e.g., '&amp;' -> '&')
    - Maps each category to the exact canonical name

    Returns a list of canonical category names (deduplicated, order preserved).
    """
    if not field:
        return []

    text = field.strip()
    # Prefer '|' as seen in the export; support comma as a fallback
    parts = [p.strip() for p in (text.split("|") if "|" in text else text.split(","))]
    seen = set()
    result: List[str] = []
    for p in parts:
        if not p:
            continue
        name = canonicalize_category(p)
        if name and name not in seen:
            seen.add(name)
            result.append(name)
    return result


def category_name_to_slug(name: str) -> str:
    """Convert a canonical category display name to its slug, if known."""
    key = _canonical_key(name)
    slug = _NAME_TO_SLUG.get(key)
    return slug or ""


def all_categories() -> Dict[str, str]:
    """Return a copy of the full slug->name mapping."""
    return dict(_SLUG_TO_NAME)

