"""
Generation of redirect mapping CSV files.

The :func:`generate_redirects_csv` helper writes a CSV file containing the
mapping of WordPress URLs to their new Wix counterparts.  The resulting file is
used to configure 301 redirects so that existing links continue to work after
migration.
"""

from __future__ import annotations

import csv
import os
from typing import Dict, Iterable


def generate_redirects_csv(
    posts: Iterable[Dict[str, str]], *, old_domain: str, new_base: str, out_path: str = "reports/redirect_map.csv"
) -> str:
    """Generate a CSV mapping old WordPress URLs to new Wix URLs.

    Parameters
    ----------
    posts:
        Iterable of dictionaries with at least ``Slug`` and ``NewURL`` keys.
        ``Permalink`` is used if available to determine the original URL.
    old_domain:
        The base domain of the legacy WordPress site.  If a post does not
        include a ``Permalink`` this domain is combined with the ``Slug`` to
        construct the old URL.
    new_base:
        Base URL for the Wix site.  Used as a fallback when ``NewURL`` is not
        provided.
    out_path:
        Location of the CSV file to be written.  The parent directory is
        created automatically.

    Returns
    -------
    str
        The path of the generated CSV file.
    """
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["OldURL", "NewURL"])
        for post in posts:
            slug = post.get("Slug", "")
            old_url = post.get("Permalink")
            if not old_url and old_domain:
                old_url = f"{old_domain.rstrip('/')}/{slug}" if slug else old_domain.rstrip('/')
            new_url = post.get("NewURL") or f"{new_base.rstrip('/')}/{slug}"
            writer.writerow([old_url, new_url])
    return out_path
