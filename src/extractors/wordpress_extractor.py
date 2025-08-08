"""
WordPress export extractors.

This module defines functions to read posts from CSV or XML export
files produced by WordPress and normalize them into a consistent
structure suitable for the Wix migration pipeline.  Normalization
includes deriving the slug from the permalink, splitting categories
and tags, and capturing common SEO metadata if present in the export.
"""

from __future__ import annotations

import csv
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from urllib.parse import urlparse

__all__ = [
    "extract_posts_from_csv",
    "extract_posts_from_xml",
]

def _clean_list(value: Optional[str]) -> List[str]:
    """
    Split a pipe-separated string into a list of trimmed strings.  If
    ``value`` is ``None`` or empty, returns an empty list.

    :param value: The raw string from the CSV export.
    :return: A list of individual terms.
    """
    if not value:
        return []
    return [v.strip() for v in value.split("|") if v.strip()]

def _derive_slug(permalink: str) -> str:
    """
    Extract the slug from a WordPress permalink.  The slug is the last
    non-empty path segment.

    :param permalink: The full URL to the post.
    :return: The slug (without leading/trailing slashes) or an empty string.
    """
    if not permalink:
        return ""
    path = urlparse(permalink).path
    if not path:
        return ""
    segments = [segment for segment in path.split("/") if segment]
    return segments[-1] if segments else ""

def extract_posts_from_csv(file_path: str) -> List[Dict[str, str]]:
    """
    Read a CSV export from WordPress and return a list of normalized posts.

    The CSV columns expected include ``Title``, ``Slug``, ``Content``,
    ``Excerpt``, ``FeaturedImage``, ``Categorias``, ``Tags``, ``Permalink``,
    ``SEO_Title``, ``SEO_Description``.  Keys are treated in a case-
    insensitive manner and missing fields default to the empty string.

    :param file_path: Path to the CSV file.
    :return: A list of dictionaries describing each post.
    """
    posts: List[Dict[str, str]] = []
    # Increase the CSV field size limit to accommodate large HTML fields
    try:
        import csv as _csv_mod
        _csv_mod.field_size_limit(10 * 1024 * 1024)  # 10 MB
    except Exception:
        pass
    try:
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Normalize keys to lower-case for easier lookup
                lower_row = {k.lower(): (v or "").strip() for k, v in row.items()}
                title = lower_row.get("title") or lower_row.get("post_title") or ""
                permalink = lower_row.get("permalink") or lower_row.get("link") or ""
                slug = lower_row.get("slug") or _derive_slug(permalink)
                post = {
                    "Title": title,
                    "Slug": slug,
                    "ContentHTML": lower_row.get("content") or lower_row.get("content_html") or "",
                    "Excerpt": lower_row.get("excerpt") or lower_row.get("post_excerpt") or "",
                    "FeaturedImageUrl": lower_row.get("featuredimage") or lower_row.get("featured_image") or "",
                    "Categories": _clean_list(lower_row.get("categorias") or lower_row.get("categories")),
                    "Tags": _clean_list(lower_row.get("tags") or lower_row.get("post_tag")),
                    "Permalink": permalink,
                    "MetaTitle": lower_row.get("seo_title") or lower_row.get("meta_title") or "",
                    "MetaDescription": lower_row.get("seo_description") or lower_row.get("meta_description") or "",
                }
                posts.append(post)
    except FileNotFoundError:
        print(f"CSV file not found: {file_path}")
    except Exception as e:
        print(f"Error parsing CSV {file_path}: {e}")
    return posts

def extract_posts_from_xml(file_path: str) -> List[Dict[str, str]]:
    """
    Parse a WordPress XML (WXR) export file into normalized post
    dictionaries.  Handles both standard WXR files and simplified XML
    structures with ``<post>`` elements.

    :param file_path: Path to the XML file.
    :return: A list of normalized posts.
    """
    posts: List[Dict[str, str]] = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Determine whether this is a custom simplified format (with <post> nodes)
        simplified_posts = root.findall(".//post")
        if simplified_posts:
            for post_el in simplified_posts:
                title = post_el.findtext("title", default="")
                permalink = post_el.findtext("Permalink", default="")
                slug = post_el.findtext("Slug") or _derive_slug(permalink)
                post = {
                    "Title": title,
                    "Slug": slug,
                    "ContentHTML": post_el.findtext("Content", default=""),
                    "Excerpt": post_el.findtext("Excerpt", default=""),
                    "FeaturedImageUrl": post_el.findtext("FeaturedImage", default=""),
                    "Categories": _clean_list(post_el.findtext("Categorias") or post_el.findtext("Categories")),
                    "Tags": _clean_list(post_el.findtext("Tags")),
                    "Permalink": permalink,
                    "MetaTitle": post_el.findtext("SEO_Title", default=""),
                    "MetaDescription": post_el.findtext("SEO_Description", default=""),
                }
                posts.append(post)
        else:
            # Assume standard WXR with <item> elements
            ns = {
                "wp": "http://wordpress.org/export/1.2/",
                "content": "http://purl.org/rss/1.0/modules/content/",
            }
            for item in root.findall(".//item"):
                title = item.findtext("title", default="")
                permalink = item.findtext("link", default="")
                slug = _derive_slug(permalink)
                content = item.findtext("content:encoded", namespaces=ns) or ""
                excerpt = item.findtext("excerpt:encoded", namespaces=ns) or ""
                categories = [c.text for c in item.findall("category[@domain='category']")]
                tags = [t.text for t in item.findall("category[@domain='post_tag']")]
                status = item.findtext("wp:status", default="", namespaces=ns)
                if status and status.lower() != "publish":
                    # Skip unpublished posts
                    continue
                post = {
                    "Title": title,
                    "Slug": slug,
                    "ContentHTML": content,
                    "Excerpt": excerpt,
                    "FeaturedImageUrl": "",  # WXR does not include the featured image URL directly
                    "Categories": categories,
                    "Tags": tags,
                    "Permalink": permalink,
                    "MetaTitle": "",
                    "MetaDescription": "",
                }
                posts.append(post)
    except FileNotFoundError:
        print(f"XML file not found: {file_path}")
    except Exception as e:
        print(f"Error parsing XML {file_path}: {e}")
    return posts
