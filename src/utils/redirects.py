"""
Generation of redirect mapping CSV files compatible with Wix 301 redirect importer.
"""

from __future__ import annotations

import csv
import os
import logging
from typing import Dict, Iterable
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def generate_redirects_csv(
    posts: Iterable[Dict[str, str]],
    out_path: str = "reports/redirect_map.csv"
) -> str:
    """
    Generate a CSV mapping old WordPress URLs to new Wix URLs.

    The output format is a two-column CSV with headers "Source Path" and
    "Target Path", suitable for Wix's 301 redirect importer.

    Parameters
    ----------
    posts:
        Iterable of dictionaries, where each must contain keys `Permalink`
        (the old URL) and `NewURL` (the new Wix URL).
    out_path:
        Location of the CSV file to be written. The parent directory is
        created automatically.

    Returns
    -------
    str
        The path of the generated CSV file.
    """
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    try:
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Source Path", "Target Path"])
            count = 0
            for post in posts:
                old_url = post.get("Permalink")
                new_url = post.get("NewURL")

                if not old_url or not new_url:
                    logger.warning("Skipping redirect for post with missing URL. Slug: %s", post.get("slug"))
                    continue

                # Wix requires relative paths for redirects
                old_path = urlparse(old_url).path
                new_path = urlparse(new_url).path

                if old_path and new_path:
                    writer.writerow([old_path, new_path])
                    count += 1

        logger.info("%d redirects successfully written to %s", count, out_path)
        return out_path
    except IOError as e:
        logger.error("Failed to write redirects CSV to %s: %s", out_path, e)
        return ""