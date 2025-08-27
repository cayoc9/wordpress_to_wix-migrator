#!/usr/bin/env python3
"""
Atualiza um draft post do Wix Blog (v3) lendo:
- Token de autorização em config/migration_config.json (wix.access_token)
- Conteúdo do post a partir de um arquivo JSON salvo em data/posts/<post_id>.json

Também permite sobrepor campos via argumentos (title, excerpt, texto simples, richcontent-file),
agendar publicação ou publicar imediatamente.
"""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, Optional

import requests

BASE_DRAFT_URL = "https://www.wixapis.com/blog/v3/draft-posts"
MAX_RETRIES = 5
RETRY_BASE_DELAY = 1.5  # segundos


def load_config() -> Dict[str, Any]:
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "config", "migration_config.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)


def backoff_sleep(attempt: int) -> None:
    delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
    time.sleep(delay)


def do_request(method: str, url: str, token: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": token,
    }
    attempt = 0
    while True:
        attempt += 1
        resp = requests.request(method, url, headers=headers, json=payload, timeout=30)
        if resp.status_code in (200, 201, 202, 204):
            if resp.text:
                try:
                    return resp.json()
                except json.JSONDecodeError:
                    return {}
            return {}
        if resp.status_code in (429, 500, 502, 503, 504) and attempt < MAX_RETRIES:
            backoff_sleep(attempt)
            continue

        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise RuntimeError(f"Erro {resp.status_code} em {method} {url}: {detail}")


def make_simple_rich_content(paragraph_text: str) -> Dict[str, Any]:
    return {
        "nodes": [
            {
                "type": "PARAGRAPH",
                "nodes": [
                    {
                        "type": "TEXT",
                        "textData": {"text": paragraph_text},
                    }
                ],
            }
        ]
    }


def update_draft_post(
    token: str,
    draft_id: str,
    draft_fields: Dict[str, Any],
    action: str = "UPDATE",
    scheduled_publish_date: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    url = f"{BASE_DRAFT_URL}/{draft_id}"
    body: Dict[str, Any] = {"action": action}

    if action == "UPDATE":
        body["draftPost"] = draft_fields
    elif action == "UPDATE_SCHEDULE":
        body["draftPost"] = {"scheduledPublishDate": scheduled_publish_date}
    else:
        raise ValueError("action deve ser 'UPDATE' ou 'UPDATE_SCHEDULE'")

    if dry_run:
        print("---- DRY RUN: Payload UPDATE ----")
        print(json.dumps(body, ensure_ascii=False, indent=2))
        return {}

    return do_request("PATCH", url, token, body)


def publish_draft_post(token: str, draft_id: str, dry_run: bool = False) -> Dict[str, Any]:
    url = f"{BASE_DRAFT_URL}/{draft_id}/publish"
    if dry_run:
        print("---- DRY RUN: Publish would be called ----")
        print(f"POST {url}")
        return {}
    return do_request("POST", url, token, None)


def load_post_fields_from_file(post_file: str) -> Dict[str, Any]:
    """Extrai campos relevantes (title, excerpt, richContent) do JSON salvo em data/posts/<id>.json.

    O arquivo salvo por scripts/get_wix_post.py contém o objeto "post" já "flattened". Este loader
    tenta ler chaves comuns e ignora as ausentes.
    """
    with open(post_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Se por algum motivo vier envolto em {"post": {...}}, desembrulha
    if isinstance(data, dict) and "post" in data and isinstance(data["post"], dict):
        data = data["post"]

    def sanitize_node_types(node: Dict[str, Any]):
        t = node.get("type")
        # Corrige tipos de lista para os esperados pela API (Ricos)
        if t == "NUMBERED_LIST":
            node["type"] = "ORDERED_LIST"
        elif t == "BULLETED_LIST":
            node["type"] = "UNORDERED_LIST"
        # Recurse em nodes filhos
        for child_key in ("nodes",):
            if isinstance(node.get(child_key), list):
                for child in node[child_key]:
                    if isinstance(child, dict):
                        sanitize_node_types(child)

    fields: Dict[str, Any] = {}
    if isinstance(data, dict):
        if data.get("title"):
            fields["title"] = data["title"]
        if data.get("excerpt"):
            fields["excerpt"] = data["excerpt"]
        if data.get("richContent"):
            rc = data["richContent"]
            # Sanitiza árvore de conteúdo para compatibilidade
            if isinstance(rc, dict) and isinstance(rc.get("nodes"), list):
                for n in rc["nodes"]:
                    if isinstance(n, dict):
                        sanitize_node_types(n)
            fields["richContent"] = rc
    return fields


def resolve_post_file(args_post_file: Optional[str], post_id: Optional[str]) -> Optional[str]:
    if args_post_file:
        return args_post_file
    if post_id:
        return os.path.join("data", "posts", f"{post_id}.json")
    return None


def main():
    parser = argparse.ArgumentParser(description="Atualiza e publica/agenda um draftPost usando dados de data/posts/<id>.json e config.")
    parser.add_argument("--draft-id", required=True, help="ID do draft post (obrigatório).")
    parser.add_argument("--post-id", help="ID do post para localizar data/posts/<post-id>.json.")
    parser.add_argument("--post-file", help="Caminho direto do arquivo do post (ex.: data/posts/<id>.json).")

    parser.add_argument("--title", help="Sobrescrever título.")
    parser.add_argument("--excerpt", help="Sobrescrever excerpt.")
    parser.add_argument("--text", help="Conteúdo simples em um parágrafo (gera richContent básico).")
    parser.add_argument("--richcontent-file", help="Caminho para arquivo JSON contendo 'richContent'.")

    parser.add_argument("--no-publish", action="store_true", help="Somente atualizar rascunho; não publicar.")
    parser.add_argument("--schedule", help="Agendar publicação (ISO 8601, ex.: 2025-08-30T14:00:00Z).")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar payloads sem fazer chamadas.")

    args = parser.parse_args()

    # Carrega token do config (preferencial). Mantemos compatibilidade com env se desejar no futuro.
    try:
        cfg = load_config()
    except Exception as e:
        print(f"Erro ao carregar config/migration_config.json: {e}", file=sys.stderr)
        sys.exit(1)

    token = (cfg.get("wix") or {}).get("access_token")
    if not token:
        print("Token não encontrado em wix.access_token no config/migration_config.json", file=sys.stderr)
        sys.exit(1)

    # Monta os campos do draft a partir do arquivo do post, depois aplica sobrescrições via args
    post_file = resolve_post_file(args.post_file, args.post_id)
    draft_fields: Dict[str, Any] = {}
    if post_file and os.path.exists(post_file):
        loaded_fields = load_post_fields_from_file(post_file)
        draft_fields.update(loaded_fields)
    elif post_file:
        print(f"Aviso: arquivo de post não encontrado: {post_file}. Seguindo apenas com sobrescrições de argumentos.")

    # Sobrescrições via argumentos
    if args.title:
        draft_fields["title"] = args.title
    if args.excerpt:
        draft_fields["excerpt"] = args.excerpt
    if args.richcontent_file:
        try:
            with open(args.richcontent_file, "r", encoding="utf-8") as f:
                draft_fields["richContent"] = json.load(f)
        except Exception as e:
            print(f"Erro ao ler richContent de {args.richcontent_file}: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.text:
        draft_fields["richContent"] = make_simple_rich_content(args.text)

    if not draft_fields and not args.schedule:
        print("Nada para atualizar: informe post-file/post-id ou --title/--excerpt/--text/--richcontent-file ou --schedule.", file=sys.stderr)
        sys.exit(1)

    # 1) UPDATE
    if draft_fields:
        print("Atualizando rascunho (UPDATE)...")
        update_draft_post(
            token=token,
            draft_id=args.draft_id,
            draft_fields=draft_fields,
            action="UPDATE",
            dry_run=args.dry_run,
        )
        if not args.dry_run:
            print("Rascunho atualizado.")

    # 2) Agendar, se solicitado
    if args.schedule:
        print(f"Agendando publicação para: {args.schedule}")
        update_draft_post(
            token=token,
            draft_id=args.draft_id,
            draft_fields={},
            action="UPDATE_SCHEDULE",
            scheduled_publish_date=args.schedule,
            dry_run=args.dry_run,
        )
        if not args.dry_run:
            print("Publicação agendada.")
        return

    # 3) Publicar, se não desabilitado
    if not args.no_publish:
        print("Publicando rascunho...")
        publish_draft_post(token=token, draft_id=args.draft_id, dry_run=args.dry_run)
        if not args.dry_run:
            print("Post publicado.")
    else:
        print("--no-publish definido: apenas atualização de rascunho realizada.")


if __name__ == "__main__":
    main()
