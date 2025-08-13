"""
Redirect generation utilities for the WordPress → Wix migration.

This module provides a helper function, :func:`generate_redirects_csv`,
to create a CSV file mapping old WordPress post URLs to their new
locations on the Wix site.  The resulting CSV is suitable for use with
Wix's bulk redirect import tool.

The function handles both full URLs (if an ``old_domain`` is provided)
and relative paths.  It correctly constructs the source and target paths
for the redirect map.

Usage example::

    from src.utils.redirects import generate_redirects_csv

    migrated_posts = [
        {"Slug": "post-one", "Permalink": "http://old.com/2023/01/post-one/", "NewURL": "https://new.wix.com/post/post-one"},
        {"Slug": "post-two", "Permalink": "http://old.com/2023/02/post-two/", "NewURL": "https://new.wix.com/post/post-two"},
    ]

    generate_redirects_csv(migrated_posts, old_domain="old.com", new_base="https://new.wix.com")

This will produce a file named ``redirects.csv`` with the following
content::

    Source Path,Target Path
    /2023/01/post-one/,/post/post-one
    /2023/02/post-two/,/post/post-two

"""

from __future__ import annotations

import csv
from typing import Dict, List
from urllib.parse import urlparse

def generate_redirects_csv(migrated: List[Dict[str, str]], *, old_domain: str = "", new_base: str = "") -> None:
    """
    Generate a CSV file mapping old WordPress URLs to new Wix URLs.

    The output format is a two-column CSV with headers "Source Path" and
    "Target Path", suitable for Wix's 301 redirect importer.

    :param migrated: A list of dictionaries, where each dictionary
                     represents a successfully migrated post and must
                     contain keys ``Permalink`` (the old URL) and
                     ``NewURL`` (the new Wix URL).
    :param old_domain: The domain of the old WordPress site. If provided,
                       it will be stripped from the permalinks to create
                       relative source paths.
    :param new_base: The base URL of the new Wix site. If provided, it
                     will be stripped from the new URLs to create
                     relative target paths.
    """
    with open("reports/redirect_map.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Source Path", "Target Path"])
        for item in migrated:
            old_url = item.get("Permalink", "")
            new_url = item.get("NewURL", "")
            if not old_url or not new_url:
                continue
            # Create relative paths
            old_path = urlparse(old_url).path
            new_path = urlparse(new_url).path
            writer.writerow([old_path, new_path])
