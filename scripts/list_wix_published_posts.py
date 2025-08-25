#!/usr/bin/env python3

import os
import json
import time
import argparse
import sys
from typing import List, Dict, Any

import requests


BASE_URL = "https://www.wixapis.com/blog/v3/posts"
PAGE_SIZE = 100
MAX_RETRIES = 5
RETRY_BASE_DELAY = 1.5  # segundos (exponencial)


def load_config() -> Dict[str, Any]:
    """Carrega o config/migration_config.json."""
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "config", "migration_config.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)


def backoff_sleep(attempt: int) -> None:

    delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
    time.sleep(delay)


def fetch_page(token: str, offset: int) -> Dict[str, Any]:
    """Busca uma página de posts com limite 100 e offset informado, com retry simples em 429/5xx."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": token,  # Ex.: "Bearer <token>" ou token direto, conforme config
    }
    params = {
        "paging.limit": PAGE_SIZE,
        "paging.offset": offset,
    }

    attempt = 0
    while True:
        attempt += 1
        resp = requests.get(BASE_URL, headers=headers, params=params, timeout=30)
        if resp.status_code == 200:
            try:
                return resp.json()
            except json.JSONDecodeError:
                raise RuntimeError("A resposta da API não é um JSON válido.")
        elif resp.status_code in (429, 500, 502, 503, 504) and attempt < MAX_RETRIES:
            backoff_sleep(attempt)
            continue
        else:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise RuntimeError(
                f"Falha ao buscar posts (status {resp.status_code}). Detalhes: {detail}"
            )


def fetch_all_posts(token: str, max_pages: int | None = None) -> List[Dict[str, Any]]:
    """Pagina até o fim (ou até max_pages) e retorna a lista completa de objetos 'post'."""
    all_posts: List[Dict[str, Any]] = []
    offset = 0
    page_count = 0

    while True:
        page_count += 1
        result = fetch_page(token, offset)

        posts = result.get("posts", [])
        all_posts.extend(posts)

        if len(posts) < PAGE_SIZE:
            break


        offset += PAGE_SIZE

        if max_pages and page_count >= max_pages:

            break

    return all_posts


def ensure_dir(path: str) -> None:

    os.makedirs(os.path.dirname(path), exist_ok=True)


def main():

    parser = argparse.ArgumentParser(description="Listar posts publicados do Wix usando config/migration_config.json.")
    parser.add_argument("--out-ids", default="data/wix_post_ids.json", help="Arquivo de saída com apenas IDs.")
    parser.add_argument("--out-posts", default="data/wix_posts_full.json", help="Arquivo de saída com posts completos.")
    parser.add_argument("--no-full", action="store_true", help="Não salvar o arquivo com posts completos.")
    parser.add_argument("--max-pages", type=int, default=None, help="(Opcional) Limite de páginas para debug.")
    args = parser.parse_args()

    try:
        config = load_config()
    except Exception as e:
        print(f"Erro ao carregar config/migration_config.json: {e}", file=sys.stderr)
        sys.exit(1)

    token = (config.get("wix") or {}).get("access_token")
    if not token:
        print("Token não encontrado em wix.access_token no config/migration_config.json", file=sys.stderr)
        sys.exit(1)

    print("Buscando posts...")
    posts = fetch_all_posts(token=token, max_pages=args.max_pages)

    if not posts:
        print("Nenhum post retornado pela API. Verifique permissões/escopos e se há posts publicados.")
        sys.exit(0)

    # Mantém apenas publicados quando possível

    published = [p for p in posts if p.get("status") == "PUBLISHED" or p.get("published") is True] or posts

    post_ids = [p.get("id") for p in published if p.get("id")]

    ensure_dir(args.out_ids)
    with open(args.out_ids, "w", encoding="utf-8") as f:
        json.dump(post_ids, f, ensure_ascii=False, indent=2)
    print(f"IDs salvos em: {args.out_ids} (total: {len(post_ids)})")

    if not args.no_full:
        ensure_dir(args.out_posts)
        with open(args.out_posts, "w", encoding="utf-8") as f:
            json.dump(published, f, ensure_ascii=False, indent=2)
        print(f"Posts completos salvos em: {args.out_posts}")

    print("Concluído.")


if __name__ == "__main__":
    main()
