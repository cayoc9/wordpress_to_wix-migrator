"""
High-level orchestration of the WordPress → Wix migration.

This module defines a :class:`WordPressMigrationTool` class that ties
together the extractors, parsers, migrators and utilities into a
complete pipeline.  It supports migrating posts from CSV or XML export
files, uploading media, converting HTML to Ricos, creating draft posts,
publishing them, writing log files and generating a redirect CSV.

Configuration is supplied via a JSON file path or directly as a
dictionary.  The ``wix`` section must include ``site_id``, ``api_key``
and ``base_url``.  Optional migration settings (e.g., dry-run) can be
provided under the ``migration`` key.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from src.extractors.wordpress_extractor import extract_posts_from_csv, extract_posts_from_xml
from src.parsers.ricos_parser import convert_html_to_ricos, strip_html_nodes
from src.migrators.wix_migrator import (
    upload_image_from_url,
    get_or_create_terms,
    create_draft_post,
    publish_post,
)
from src.utils.errors import report_error, report_ok, ERRORS
from src.utils.redirects import generate_redirects_csv

import json

class WordPressMigrationTool:
    """
    Encapsulates all state and behavior required to migrate a set of
    WordPress posts to Wix.  This class is responsible for reading
    configuration, extracting posts, performing transformations and
    migrating them.  Detailed success and failure information is
    recorded using the :mod:`src.utils.errors` module.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, *, config_file: Optional[str] = None) -> None:
        if config_file:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
        if config is None:
            # Default configuration from environment variables
            config = {
                "wix": {
                    "site_id": os.getenv("WIX_SITE_ID", ""),
                    "api_key": os.getenv("WIX_API_KEY", ""),
                    "base_url": "https://www.wixapis.com",
                },
                "migration": {
                    "dry_run": False,
                    "limit": None,
                },
            }
        self.config = config

    def log_message(self, message: str, level: str = "INFO") -> None:
        ts = json.dumps(os.times())  # simplified timestamp placeholder
        print(f"[{level}] {message}")
        # Append to log file
        os.makedirs("reports/migration", exist_ok=True)
        with open("reports/migration/migration.log", "a", encoding="utf-8") as f:
            f.write(f"{level}: {message}\n")

    def extract_posts(self, csv_path: Optional[str] = None, xml_path: Optional[str] = None) -> List[Dict[str, Any]]:
        posts: List[Dict[str, Any]] = []
        if csv_path and os.path.exists(csv_path):
            self.log_message(f"Extracting posts from CSV {csv_path}")
            try:
                posts.extend(extract_posts_from_csv(csv_path))
            except Exception as e:
                self.log_message(f"Error extracting CSV: {e}", "ERROR")
        if xml_path and os.path.exists(xml_path):
            self.log_message(f"Extracting posts from XML {xml_path}")
            try:
                posts.extend(extract_posts_from_xml(xml_path))
            except Exception as e:
                self.log_message(f"Error extracting XML: {e}", "ERROR")
        return posts

    def migrate_posts(self, posts: List[Dict[str, Any]], *, new_base_url: str) -> None:
        """
        Migrate a list of normalized posts to Wix.  This method applies
        the full pipeline: upload cover images, convert HTML to Ricos,
        ensure tags and categories exist, create drafts, publish them
        and log results.  It also generates a CSV of redirects at the
        end.  If ``dry_run`` is enabled in the configuration, only
        conversions and log files are produced; no network calls to Wix
        are made.

        :param posts: A list of post dictionaries.
        :param new_base_url: The base URL of the Wix site used when
            constructing redirect targets.
        :return: ``None``
        """
        dry_run: bool = self.config.get("migration", {}).get("dry_run", False)
        limit: Optional[int] = self.config.get("migration", {}).get("limit")
        migrated: List[Dict[str, str]] = []
        count = 0
        for post in posts:
            if limit is not None and count >= limit:
                break
            count += 1
            slug = post.get("Slug") or ""
            self.log_message(f"Migrating post '{slug}'")
            try:
                # Upload cover image
                if post.get("FeaturedImageUrl"):
                    if dry_run:
                        self.log_message(f"Dry-run: would upload cover {post['FeaturedImageUrl']}")
                    else:
                        new_url = upload_image_from_url(self.config["wix"], post["FeaturedImageUrl"])
                        if new_url:
                            post["FeaturedImageUrl"] = new_url
                        else:
                            report_error("MEDIA_UPLOAD", post)
                # Taxonomies
                post["CategoryIds"] = []
                post["TagIds"] = []
                if post.get("Categories"):
                    if dry_run:
                        self.log_message(f"Dry-run: would ensure categories {post['Categories']}")
                    else:
                        post["CategoryIds"] = get_or_create_terms(self.config["wix"], "categories", post["Categories"])
                if post.get("Tags"):
                    if dry_run:
                        self.log_message(f"Dry-run: would ensure tags {post['Tags']}")
                    else:
                        post["TagIds"] = get_or_create_terms(self.config["wix"], "tags", post["Tags"])
                # HTML conversion
                ricos = convert_html_to_ricos(post.get("ContentHTML", ""), embed_strategy="html_iframe")
                # Create draft
                if dry_run:
                    self.log_message(f"Dry-run: would create draft for {slug}")
                    draft_resp = {"post": {"id": f"dry-{slug}"}}
                else:
                    try:
                        draft_resp = create_draft_post(self.config["wix"], post, ricos)
                    except Exception as e:
                        # If the draft fails due to HTML embeds, strip and retry once
                        if hasattr(e, "response") and e.response.status_code == 400:
                            ricos_no_html = strip_html_nodes(json.loads(json.dumps(ricos)))
                            try:
                                draft_resp = create_draft_post(self.config["wix"], post, ricos_no_html, allow_html_iframe=False)
                            except Exception as e2:
                                report_error("WIX_DRAFT_400", post, e2)
                                continue
                        else:
                            report_error("WIX_NETWORK", post, e)
                            continue
                draft_id = (draft_resp.get("post") or {}).get("id")
                if not draft_id:
                    report_error("WIX_DRAFT_400", post)
                    continue
                report_ok("DRAFT_CREATED", post, {"draft_id": draft_id})
                # Publish
                if dry_run:
                    new_url = f"{new_base_url.rstrip('/')}/post/{slug}"
                else:
                    try:
                        pub_resp = publish_post(self.config["wix"], draft_id)
                        new_url = (pub_resp.get("post") or {}).get("url") or f"{new_base_url.rstrip('/')}/post/{slug}"
                    except Exception as e:
                        report_error("PUBLISH", post, e)
                        continue
                migrated.append({"Slug": slug, "Permalink": post.get("Permalink"), "NewURL": new_url})
                report_ok("PUBLISHED", post, {"url": new_url})
            except Exception as e:
                report_error("WIX_NETWORK", post, e)
        # Generate redirects
        try:
            generate_redirects_csv(migrated, old_domain=self.config.get("old_domain", ""), new_base=new_base_url)
            self.log_message(f"Redirect CSV generated with {len(migrated)} entries")
        except Exception as e:
            self.log_message(f"Failed to generate redirects: {e}", "ERROR")
