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
from src.parsers.ricos_parser import convert_html_to_ricos
from src.migrators.wix_migrator import (
    import_image_from_url,
    get_or_create_terms,
    create_draft_post,
    publish_post,
    list_members,
    create_member,
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
        if config_file and os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
        elif config is None:
            # Default configuration
            config = {}

        # Ensure essential keys exist to prevent KeyErrors
        config.setdefault("wix", {})
        config["wix"].setdefault("app_id", os.getenv("WIX_APP_ID", ""))
        config["wix"].setdefault("app_secret", os.getenv("WIX_APP_SECRET", ""))
        config["wix"].setdefault("instance_id", os.getenv("WIX_INSTANCE_ID", ""))
        config["wix"].setdefault("access_token", "")
        config["wix"].setdefault("member_id", "")
        config["wix"].setdefault("base_url", "https://www.wixapis.com")

        config.setdefault("migration", {})
        config["migration"].setdefault("dry_run", False)
        config["migration"].setdefault("limit", None)
        config["migration"].setdefault("wordpress_domain", "")
        config["migration"].setdefault("wix_site_url", "")
        
        self.config = config
        self.member_map_file = "reports/member_map.json"
        self.email_to_member_id_map: Dict[str, str] = {}
        self.default_member_id: Optional[str] = None

        # Load existing member map
        if os.path.exists(self.member_map_file):
            try:
                with open(self.member_map_file, "r", encoding="utf-8") as f:
                    self.email_to_member_id_map = json.load(f)
            except json.JSONDecodeError:
                self.log_message(f"Warning: Could not decode {self.member_map_file}. Starting with empty map.", level="WARNING")

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
        import requests  # Import here to avoid circular imports if needed elsewhere

        dry_run: bool = self.config.get("migration", {}).get("dry_run", False)
        limit: Optional[int] = self.config.get("migration", {}).get("limit")
        migrated: List[Dict[str, str]] = []
        count = 0

        # Populate the initial email to member ID map
        # This is now loaded from self.member_map_file in __init__

        for post in posts:
            if limit is not None and count >= limit:
                break
            count += 1
            slug = post.get("Slug") or ""
            self.log_message(f"Migrating post '{slug}'")

            # Print HTML content for debugging
            print(f"DEBUG: Post '{slug}' HTML content:")
            print(post.get("ContentHTML", ""))
            print("---")

            author_email = post.get("Author Email")
            member_id = None

            if author_email:
                if author_email in self.email_to_member_id_map:
                    member_id = self.email_to_member_id_map[author_email]
                elif not dry_run:
                    self.log_message(f"Creating new member for email: {author_email}", level="INFO")
                    try:
                        new_member = create_member(self.config["wix"], author_email)
                        if new_member:
                            member_id = new_member["id"]
                            self.email_to_member_id_map[author_email] = member_id
                            # Save the updated map
                            os.makedirs(os.path.dirname(self.member_map_file), exist_ok=True)
                            with open(self.member_map_file, "w", encoding="utf-8") as f:
                                json.dump(self.email_to_member_id_map, f)
                            self.log_message(f"Successfully created member {new_member.get('profile', {}).get('nickname', author_email)} for email: {author_email}", level="INFO")
                        else:
                            # This path is for other potential issues with create_member that don't raise HTTPError
                            # If ALREADY_EXISTS is handled by create_member returning None, we should log it.
                            # However, based on the error message, it seems to raise an exception.
                            # Let's keep this for robustness.
                            self.log_message(f"Failed to create member for email: {author_email} (create_member returned None). This should not happen with the new error handling. Skipping post.", level="ERROR")
                            report_error("MEMBER_CREATION_FAILED", post)
                            continue
                    except requests.exceptions.HTTPError as e:
                         if e.response is not None and e.response.status_code == 409:
                            # Handle 409 Conflict (e.g., member already exists)
                            self.log_message(f"Member with email {author_email} already exists (409).", level="INFO")
                            # Check if the member ID is already in the map
                            if author_email in self.email_to_member_id_map:
                                member_id = self.email_to_member_id_map[author_email]
                                self.log_message(f"Using existing member ID for {author_email} from map.", level="INFO")
                            else:
                                self.log_message(f"Member ID for {author_email} not found in map. Skipping post.", level="WARNING")
                                report_error("MEMBER_ALREADY_EXISTS_BUT_NOT_IN_MAP", post)
                                continue
                         else:
                            # Re-raise other HTTP errors
                            self.log_message(f"Failed to create member for email: {author_email}. Error: {e}. Skipping post.", level="ERROR")
                            report_error("MEMBER_CREATION_FAILED", post)
                            continue
                    except Exception as e: # Catch other potential errors from create_member
                         self.log_message(f"Unexpected error creating member for email: {author_email}. Error: {e}. Skipping post.", level="ERROR")
                         report_error("MEMBER_CREATION_FAILED", post)
                         continue
            else: # No author email in post
                if self.default_member_id:
                    member_id = self.default_member_id
                elif not dry_run:
                    self.log_message("No author email for post. Creating a default author.", level="INFO")
                    default_email = "default-author@example.com"
                    try:
                        new_member = create_member(self.config["wix"], default_email)
                        if new_member:
                            self.default_member_id = new_member["id"]
                            member_id = self.default_member_id
                            self.email_to_member_id_map[default_email] = member_id
                            # Save the updated map
                            os.makedirs(os.path.dirname(self.member_map_file), exist_ok=True)
                            with open(self.member_map_file, "w", encoding="utf-8") as f:
                                json.dump(self.email_to_member_id_map, f)
                            self.log_message(f"Successfully created default member {new_member.get('profile', {}).get('nickname', default_email)}", level="INFO")
                        else:
                            self.log_message("Failed to create default member. Skipping post.", level="ERROR")
                            report_error("MEMBER_CREATION_FAILED", post)
                            continue
                    except requests.HTTPError as e:
                        if e.response.status_code == 409: # ALREADY_EXISTS
                            self.log_message(f"Default member with email {default_email} already exists. Cannot retrieve ID. Skipping post.", level="WARNING")
                            report_error("MEMBER_ALREADY_EXISTS", post)
                            continue
                        else:
                            self.log_message(f"Failed to create default member. Error: {e}. Skipping post.", level="ERROR")
                            report_error("MEMBER_CREATION_FAILED", post)
                            continue

            if not member_id and not dry_run:
                self.log_message(f"Could not find or create a member for post '{slug}'. Skipping post.", level="WARNING")
                report_error("MISSING_MEMBER_ID", post)
                continue

            try:
                # Upload cover image
                if post.get("FeaturedImageUrl"):
                    if dry_run:
                        self.log_message(f"Dry-run: would upload cover {post['FeaturedImageUrl']}")
                    else:
                        media_id = import_image_from_url(self.config["wix"], post["FeaturedImageUrl"])
                        if media_id:
                            post["FeaturedImageId"] = media_id
                        else:
                            report_error("MEDIA_UPLOAD", post)
                            self.log_message(f"Failed to upload media for post '{slug}'", "ERROR")

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
                        # Limit tags to 30 as per Wix API validation
                        post["TagIds"] = get_or_create_terms(self.config["wix"], "tags", post["Tags"][:30])
                
                # HTML conversion
                print(f"DEBUG: Converting HTML to Ricos for post '{slug}'")
                image_importer = lambda url: import_image_from_url(self.config["wix"], url)
                ricos = convert_html_to_ricos(
                    post.get("ContentHTML", ""), 
                    embed_strategy="html_iframe",
                    image_importer=image_importer if not dry_run else None,
                    paragraph_spacing_px=2
                )
                print(f"DEBUG: Ricos content for post '{slug}':")
                print(ricos)
                print("---")
                
                # Create draft
                if dry_run:
                    self.log_message(f"Dry-run: would create draft for {slug}")
                    draft_resp = {"post": {"id": f"dry-{slug}"}}
                else:
                    try:
                        draft_resp = create_draft_post(
                            self.config["wix"], 
                            post, 
                            ricos,
                            member_id=member_id
                        )
                    except Exception as e:
                        error_details = e.response.text if hasattr(e, "response") else str(e)
                        report_error("WIX_NETWORK", post, e)
                        self.log_message(f"Network error creating draft for post '{slug}': {error_details}", "ERROR")
                        continue
                
                draft_id = (draft_resp.get("draftPost") or {}).get("id")
                if not draft_id:
                    report_error("WIX_DRAFT_400", post)
                    self.log_message(f"Draft creation for post '{slug}' did not return an ID.", "ERROR")
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
                        error_details = e.response.text if hasattr(e, "response") else str(e)
                        report_error("PUBLISH", post, e)
                        self.log_message(f"Failed to publish post '{slug}': {error_details}", "ERROR")
                        continue
                
                migrated.append({"Slug": slug, "Permalink": post.get("Permalink"), "NewURL": new_url})
                report_ok("PUBLISHED", post, {"url": new_url})

            except Exception as e:
                error_details = e.response.text if hasattr(e, "response") else str(e)
                report_error("WIX_NETWORK", post, e)
                self.log_message(f"An unexpected error occurred while migrating post '{slug}': {error_details}", "ERROR")

        # Generate redirects
        try:
            generate_redirects_csv(migrated, old_domain=self.config.get("migration", {}).get("wordpress_domain", ""), new_base=new_base_url)
            self.log_message(f"Redirect CSV generated with {len(migrated)} entries")
        except Exception as e:
            self.log_message(f"Failed to generate redirects: {e}", "ERROR")
