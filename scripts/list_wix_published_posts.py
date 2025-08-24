#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Lista todos os posts PUBLICADOS do Wix Blog e salva metadados em JSON.

Uso:
  python scripts/list_wix_published_posts.py \
    [--out data/published_posts.json] \
    [--limit 10000] \
    [--all] \
    [--details]

Autenticação:
  - Lê primeiro de variáveis de ambiente: WIX_API_KEY (ou WIX_ACCESS_TOKEN), WIX_SITE_ID
  - Fallback para config/migration_config.json em: wix.api_key, wix.access_token, wix.site_id

Notas:
  - Com --details, enriquece cada item com GET /blog/v3/posts/{id}?fieldsets=URL,SEO (e mantém demais campos).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


import requests

BASE_URL = "https://www.wixapis.com/blog/v3"


def die(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    sys.exit(code)

def load_wix_config() -> Dict[str, Any]:
    cfg_path = Path(__file__).parent.parent / "config" / "migration_config.json"
    if cfg_path.exists():
        try:
            return json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def resolve_auth() -> tuple[Optional[str], Optional[str]]:
    # Tenta carregar o token do wix_token.json primeiro
    token_path = Path(__file__).parent.parent / "wix_token.json"
    access_token = None
    if token_path.exists():
        try:
            token_data = json.loads(token_path.read_text(encoding="utf-8"))
            access_token = token_data.get("access_token")
        except Exception:
            pass

    cfg = load_wix_config()
    wix_cfg = cfg.get("wix", {}) if isinstance(cfg, dict) else {}

    # Prioridade: Token do wix_token.json > WIX_API_KEY > wix.api_key > WIX_ACCESS_TOKEN > wix.access_token
    authorization = (
        access_token
        or os.getenv("WIX_API_KEY")
        or wix_cfg.get("api_key")
        or os.getenv("WIX_ACCESS_TOKEN")
        or wix_cfg.get("access_token")
    )
    site_id = os.getenv("WIX_SITE_ID") or wix_cfg.get("site_id")

    if not authorization:
        die(
            "Token/API Key não encontrado. Gere um token com 'generate_wix_token.py' ou configure WIX_API_KEY/WIX_ACCESS_TOKEN."
        )
    return authorization, site_id

def wix_request(method: str, path: str, *, json_body: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
    authorization, site_id = resolve_auth()
    url = f"{BASE_URL}{path}"
    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json",
    }
    if site_id:
        headers["wix-site-id"] = site_id
    resp = requests.request(method, url, headers=headers, json=json_body, timeout=30)
    if not resp.ok:
        content_type = resp.headers.get("Content-Type", "")
        if "application/json" in content_type:
            try:
                data = resp.json()
            except Exception:
                data = None
            msg = data.get("message") if isinstance(data, dict) else resp.text
            details = data.get("details") if isinstance(data, dict) else None
            err = f"Falha {resp.status_code} em {method} {path}: {msg}"
            if details:
                err += f"\nDetalhes: {json.dumps(details, ensure_ascii=False)}"
            die(err)
        else:
            die(f"Falha {resp.status_code} em {method} {path}:\n{resp.text}")
    try:
        return resp.json()
    except Exception:
        return None

def query_published_posts(limit_total: int = 10000, fetch_all: bool = False, *, only_ids: bool = False) -> List[Dict[str, Any]]:

    posts: List[Dict[str, Any]] = []
    fetched = 0
    page_size = 50
    offset = 0

    while True:
        body = {
            "query": {
                "filter": {"status": "PUBLISHED"},
                "sort": [{"fieldName": "lastPublishedDate", "order": "DESC"}],
                "paging": {"limit": page_size, "offset": offset},
            }
        }
        # Se estiver buscando apenas IDs, usar fieldsets mínimos para otimização
        if only_ids:
            body["query"]["fieldsets"] = ["ID"]
        data = wix_request("POST", "/posts/query", json_body=body)
        if data is None:
            break

        page_posts = data.get("posts") or []
        posts.extend(page_posts)
        fetched += len(page_posts)

        if not page_posts:
            break

        offset += page_size

        if (not fetch_all) and fetched >= limit_total:
            break

    return posts

def pick_metadata(p: Dict[str, Any]) -> Dict[str, Any]:
    keys = [
        "id",
        "title",
        "slug",
        "status",
        "firstPublishedDate",
        "lastPublishedDate",
        "contentId",
        "minutesToRead",
        "categoryIds",
        "tagIds",
        "language",
        "coverMedia",
    ]
    out = {k: p.get(k) for k in keys}
    return out

def enrich_with_details(posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    enriched: List[Dict[str, Any]] = []
    for p in posts:
        pid = p.get("id")
        if not pid:
            enriched.append(p)
            continue
        # Trazer URL e SEO completos do item
        details = wix_request("GET", f"/posts/{pid}?fieldsets=URL,SEO")
        detail_post = details.get("post") if isinstance(details, dict) else None
        if isinstance(detail_post, dict):
            merged = dict(p)
            # Mesclar sem perder campos existentes
            for k, v in detail_post.items():
                if k not in merged or merged[k] in (None, []) or (isinstance(merged[k], dict) and not merged[k]):

                    merged[k] = v
            enriched.append(merged)
        else:
            enriched.append(p)
    return enriched

def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Lista posts publicados do Wix Blog e salva em JSON")
    ap.add_argument("--out", default="data/published_posts.json", help="Arquivo de saída JSON")
    ap.add_argument("--limit", type=int, default=10000, help="Limite máximo preliminar (use 60 p/ operação rápida)")
    ap.add_argument("--all", action="store_true", help="Ignorar limite e buscar todos (até esgotar a paginação)")
    ap.add_argument("--details", action="store_true", help="Enriquecer cada post com URL/SEO via GET por ID")
    ap.add_argument("--only-ids", action="store_true", help="Retorna apenas IDs de posts publicados, mais rápido")
    args = ap.parse_args(argv)

    # Ajuste automático de limite para operação rápida quando --only-ids
    if args.only_ids and "--limit" not in argv:
        args.limit = 60

    print("➡️  Consultando posts publicados no Wix Blog...")
    posts = query_published_posts(limit_total=args.limit, fetch_all=args.all, only_ids=args.only_ids)

    # Garantir que não ultrapasse o limite solicitado (pode vir em blocos de 100)
    if not args.all and len(posts) > args.limit:
        posts = posts[:args.limit]

    # Atalho: quando só IDs, salvar e encerrar
    if args.only_ids:
        ids = [p.get("id") for p in posts if p.get("id")]
        output = {
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
            "total": len(ids),
            "ids": ids,
        }
        out_path = Path(args.out)
        if str(out_path) == "data/published_posts.json":
            out_path = Path("data/published_post_ids.json")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✔️  {len(ids)} IDs salvos em: {out_path}")
        return 0

    if args.details:
        print("➡️  Enriquecendo com detalhes (URL/SEO)...")
        posts = enrich_with_details(posts)

    # Mantém metadados principais no topo, mas preserva demais campos vindo da API
    meta = []
    for p in posts:
        m = pick_metadata(p)
        # Inclui também campos adicionais (URL/SEO) se presentes
        if "seo" in p:
            m["seo"] = p["seo"]
        if "url" in p:
            m["url"] = p["url"]
        # Copia demais campos não listados para não perder informações
        for k, v in p.items():
            if k not in m:
                m[k] = v
        meta.append(m)

    output = {
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "total": len(meta),
        "posts": meta,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✔️  {len(meta)} posts publicados salvos em: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
