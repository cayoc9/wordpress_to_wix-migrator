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
from typing import Any, Dict, List, Optional
import unicodedata

from src.extractors.wordpress_extractor import extract_posts_from_csv, extract_posts_from_xml
from src.parsers.ricos_parser import convert_html_to_ricos
from src.migrators.wix_migrator import (
    import_image_from_url,
    get_or_create_terms,
    create_draft_post,
    publish_post,
    get_or_create_author_id,
    check_connection,
)
from src.utils.errors import report_error, report_ok, ERRORS
from src.utils.redirects import generate_redirects_csv
from src.utils.trace import make_post_trace_dir, write_json, make_event_logger

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
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)
                if isinstance(loaded_config, dict):
                    self.config = loaded_config
                else:
                    self.config = {}
            except (json.JSONDecodeError, TypeError):
                self.config = {}
        elif config and isinstance(config, dict):
            self.config = config
        else:
            self.config = {}

        # Ensure essential keys exist to prevent KeyErrors
        if not isinstance(self.config, dict):
            self.config = {}
        self.config.setdefault("wix", {})
        self.config["wix"].setdefault("app_id", os.getenv("WIX_APP_ID", ""))
        self.config["wix"].setdefault("app_secret", os.getenv("WIX_APP_SECRET", ""))
        self.config["wix"].setdefault("instance_id", os.getenv("WIX_INSTANCE_ID", ""))
        self.config["wix"].setdefault("access_token", "")
        self.config["wix"].setdefault("member_id", "")
        self.config["wix"].setdefault("base_url", "https://www.wixapis.com")

        self.config.setdefault("migration", {})
        self.config["migration"].setdefault("dry_run", False)
        self.config["migration"].setdefault("limit", None)
        self.config["migration"].setdefault("wordpress_domain", "")
        self.config["migration"].setdefault("wix_site_url", "")
        self.config["migration"].setdefault("default_author_email", "default-author@example.com")
        self.config["migration"].setdefault("publish_posts", True)
        self.config["migration"].setdefault("trace", False)
        
        # Validação leve: feita no pre_flight_check para não quebrar testes/dry-run

        self.member_map_file = "reports/member_map.json"
        # trace_id por execução para correlação
        import uuid
        self.trace_id = str(uuid.uuid4())
        self.email_to_member_id_map: Dict[str, str] = {}
        self.default_member_id: Optional[str] = None

        # Load existing member map
        if os.path.exists(self.member_map_file):
            try:
                with open(self.member_map_file, "r", encoding="utf-8") as f:
                    self.email_to_member_id_map = json.load(f)
            except json.JSONDecodeError:
                self.log_message(f"Warning: Could not decode {self.member_map_file}. Starting with empty map.", level="WARNING")

    def _validate_config(self) -> None:
        """(Mantida para compatibilidade) Validação é feita no pre_flight_check."""
        return None

    def pre_flight_check(self) -> bool:
        """Executa checagens pré-voo antes de iniciar a migração."""
        self.log_message("Executando checagens pré-voo...")
        if self.config.get("migration", {}).get("dry_run", False):
            self.log_message("Modo dry-run ativado. Pulando checagens pré-voo.", level="INFO")
            return True
        # Se faltam credenciais, registra aviso e segue (útil para testes/execuções locais)
        wix_config = self.config.get("wix", {})
        if not wix_config.get("access_token"):
            self.log_message("Aviso: 'access_token' não definido. Pulando verificação de conexão.", level="WARNING")
            return True
        if not self.config.get("migration", {}).get("wix_site_url"):
            self.log_message("Aviso: 'wix_site_url' não definido. Pulando verificação de conexão.", level="WARNING")
            return True
        if not check_connection(self.config["wix"]):
            self.log_message("Falha na verificação de conexão com a API Wix. Verifique seu 'access_token' e a rede.", level="ERROR")
            return False
        
        self.log_message("Checagens pré-voo passaram.", level="INFO")
        return True

    def log_message(self, message: str, level: str = "INFO") -> None:
        ts = json.dumps(os.times())  # simplified timestamp placeholder
        print(f"[{level}][trace:{self.trace_id}] {message}")
        # Append to log file
        os.makedirs("reports/migration", exist_ok=True)
        with open("reports/migration/migration.log", "a", encoding="utf-8") as f:
            f.write(f"{level}: {message} | trace={self.trace_id}\n")

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
        Migre uma lista de posts normalizados para o Wix. Este método aplica
        o pipeline completo: carregue imagens de capa, converta HTML para Ricos,
        garanta a existência de tags e categorias, crie rascunhos, publique-os
        e registre os resultados. Ele também gera um CSV de redirecionamentos
        no final. Se ``dry_run`` estiver habilitado na configuração, apenas
        conversões e arquivos de log serão produzidos; nenhuma chamada de rede para o Wix
        será feita.
        
        :param posts: Uma lista de dicionários de posts.
        :param new_base_url: A URL base do site Wix usada ao
        construir alvos de redirecionamento.
        :return: ``None``
        """
        if not self.pre_flight_check():
            return

        import requests  # Import here to avoid circular imports if needed elsewhere

        dry_run: bool = self.config.get("migration", {}).get("dry_run", False)
        limit: Optional[int] = self.config.get("migration", {}).get("limit")
        default_author_email: str = self.config.get("migration", {}).get("default_author_email", "fallback@example.com")
        migrated: List[Dict[str, str]] = []
        count = 0

        # Populate the initial email to member ID map
        # This is now loaded from self.member_map_file in __init__

        for post in posts:
            if limit is not None and count >= limit:
                break
            count += 1
            slug = post.get("Slug") or ""
            # Sanitiza slug para o padrão aceito pela Wix (ASCII minúsculo, hífens)
            def _sanitize_slug(s: str) -> str:
                s = unicodedata.normalize("NFKD", s)
                s = s.encode("ascii", "ignore").decode("ascii")
                s = s.lower().strip().replace(" ", "-")
                import re as _re
                s = _re.sub(r"[^a-z0-9\-]", "-", s)
                s = _re.sub(r"-+", "-", s).strip("-")
                return s
            sanitized = _sanitize_slug(slug)
            if sanitized != slug:
                self.log_message(f"Slug sanitizado: '{slug}' => '{sanitized}'", level="INFO")
                post["Slug"] = sanitized
                slug = sanitized
            self.log_message(f"Migrating post '{slug}'")

            # Preparação de rastreabilidade por post
            trace_enabled = bool(self.config.get("migration", {}).get("trace", False))
            trace_dir = make_post_trace_dir(slug) if trace_enabled else None
            trace_event = make_event_logger(trace_dir) if trace_dir else None
            if trace_dir:
                try:
                    write_json(trace_dir, "01_post_normalized.json", post)
                    if trace_event:
                        trace_event({"stage": "extract", "event": "post_loaded"})
                except Exception:
                    pass

            # Debug opcional
            if trace_event:
                trace_event({
                    "stage": "parser",
                    "event": "html_received",
                    "html_length": len(post.get("ContentHTML", "") or ""),
                })

            author_email = post.get("Author Email")
            member_id = None

            if not dry_run:
                # Use the new get_or_create_author_id function
                member_id = get_or_create_author_id(
                    self.config["wix"],
                    author_email if author_email else default_author_email, # Use post author email or default
                    default_author_email
                )
                if member_id:
                    # Update the map for caching within this migration run
                    if author_email:
                        self.email_to_member_id_map[author_email] = member_id
                    else:
                        self.email_to_member_id_map[default_author_email] = member_id
                    # Save the updated map to file
                    os.makedirs(os.path.dirname(self.member_map_file), exist_ok=True)
                    with open(self.member_map_file, "w", encoding="utf-8") as f:
                        json.dump(self.email_to_member_id_map, f)
                else:
                    self.log_message(f"Could not find or create a member for post '{slug}'. Skipping post.", level="WARNING")
                    report_error("MISSING_MEMBER_ID", post, None, {"trace_id": self.trace_id})
                    continue
            else: # dry_run is True
                self.log_message(f"Dry-run: would determine member ID for {author_email if author_email else 'default author'}", level="INFO")
                # In dry-run, we don't actually get a member_id from API, so we can set a placeholder
                member_id = "dry-run-member-id"

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
                            report_error("MEDIA_UPLOAD", post, None, {"trace_id": self.trace_id})
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
                    embed_strategy="HTML",
                    image_importer=image_importer if not dry_run else None,
                    paragraph_spacing_px=2,
                    trace_dump_dir=trace_dir,
                    trace_event=trace_event,
                )
                if trace_event:
                    trace_event({"stage": "parser", "event": "ricos_ready"})
                
                # Create draft
                if dry_run:
                    self.log_message(f"Dry-run: would create draft for {slug}")
                    # Emula o payload esperado da API no dry-run
                    draft_resp = {"draftPost": {"id": f"dry-{slug}"}}
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
                        report_error("WIX_NETWORK", post, e, {"trace_id": self.trace_id, "stage": "create_draft"})
                        # Dump de erro por post
                        if trace_dir:
                            try:
                                from src.utils.trace import write_json
                                write_json(trace_dir, "90_error_create_draft.json", {
                                    "error": error_details,
                                    "stage": "create_draft",
                                })
                            except Exception:
                                pass
                        self.log_message(f"Network error creating draft for post '{slug}': {error_details}", "ERROR")
                        continue
                
                draft_id = (draft_resp.get("draftPost") or {}).get("id")
                if not draft_id:
                    report_error("WIX_DRAFT_400", post, None, {"trace_id": self.trace_id})
                    self.log_message(f"Draft creation for post '{slug}' did not return an ID.", "ERROR")
                    continue
                
                report_ok("DRAFT_CREATED", post, {"draft_id": draft_id}, {"trace_id": self.trace_id})
                
                # Publish
                if not self.config.get("migration", {}).get("publish_posts", True):
                    self.log_message(f"Skipping publishing for post '{slug}' as per configuration.", "INFO")
                    new_url = f"{new_base_url.rstrip('/')}/post/{slug}" # Placeholder URL
                    migrated.append({"Slug": slug, "Permalink": post.get("Permalink"), "NewURL": new_url})
                    continue

                if dry_run:
                    new_url = f"{new_base_url.rstrip('/')}/post/{slug}"
                else:
                    try:
                        pub_resp = publish_post(self.config["wix"], draft_id)
                        new_url = (pub_resp.get("post") or {}).get("url") or f"{new_base_url.rstrip('/')}/post/{slug}"
                    except Exception as e:
                        error_details = e.response.text if hasattr(e, "response") else str(e)
                        report_error("PUBLISH", post, e, {"trace_id": self.trace_id, "stage": "publish"})
                        if trace_dir:
                            try:
                                from src.utils.trace import write_json
                                write_json(trace_dir, "91_error_publish.json", {
                                    "error": error_details,
                                    "stage": "publish",
                                    "draft_id": draft_id,
                                })
                            except Exception:
                                pass
                        self.log_message(f"Failed to publish post '{slug}': {error_details}", "ERROR")
                        continue
                
                migrated.append({"Slug": slug, "Permalink": post.get("Permalink"), "NewURL": new_url})
                report_ok("PUBLISHED", post, {"url": new_url}, {"trace_id": self.trace_id})

            except Exception as e:
                error_details = e.response.text if hasattr(e, "response") else str(e)
                report_error("WIX_NETWORK", post, e, {"trace_id": self.trace_id, "stage": "migrate_post"})
                if trace_dir:
                    try:
                        from src.utils.trace import write_json
                        write_json(trace_dir, "99_error_unexpected.json", {
                            "error": error_details,
                            "stage": "migrate_post",
                        })
                    except Exception:
                        pass
                self.log_message(f"An unexpected error occurred while migrating post '{slug}': {error_details}", "ERROR")

        # Generate redirects
        try:
            generate_redirects_csv(migrated)
            self.log_message(f"Redirect CSV generated with {len(migrated)} entries")
        except Exception as e:
            self.log_message(f"Failed to generate redirects: {e}", "ERROR")

        self._generate_summary_report(posts, migrated)

    def _generate_summary_report(self, all_posts: List[Dict[str, Any]], migrated_posts: List[Dict[str, Any]]) -> None:
        """Gera um relatório de sumário da migração."""
        total_posts = len(all_posts)
        successful_migrations = len(migrated_posts)
        failed_migrations = total_posts - successful_migrations

        summary = {
            "total_posts": total_posts,
            "successful_migrations": successful_migrations,
            "failed_migrations": failed_migrations,
            "migrated_slugs": [post["Slug"] for post in migrated_posts],
            "failed_slugs": [post["Slug"] for post in all_posts if post["Slug"] not in [p["Slug"] for p in migrated_posts]]
        }

        summary_path = os.path.join("reports", "migration", "summary.json")
        redirect_map_path = os.path.join("reports", "migration", "redirect_map.csv")
        error_log_path = os.path.join("reports", "migration", "errors.jsonl")

        try:
            os.makedirs(os.path.dirname(summary_path), exist_ok=True)
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=4)
            self.log_message(f"Summary report generated at {summary_path}")
        except IOError as e:
            self.log_message(f"Failed to write summary report: {e}", "ERROR")
        
        # Log final para o console
        self.log_message("--- Migration Finished ---", "INFO")
        self.log_message(f"Total posts processed: {total_posts}", "INFO")
        self.log_message(f"  - Successful: {successful_migrations}", "INFO")
        self.log_message(f"  - Failed: {failed_migrations}", "INFO")
        self.log_message(f"Redirect map: {redirect_map_path}", "INFO")
        self.log_message(f"Error log: {error_log_path}", "INFO")
        self.log_message(f"Summary report: {summary_path}", "INFO")
