#!/usr/bin/env python3
"""
Auditoria e limpeza de mídias Wix vinculadas à migração WordPress → Wix.

Funcionalidades principais:
- Varrer imagens de origem (CSV WordPress + HTML) e dos posts Wix locais (data/posts/*.json).
- Inventariar a mídia do Wix (Site Media API) com paginação.
- Mapear uso atual em posts (coverMedia e richContent -> image.src.id).
- Detectar duplicatas por chave canônica (basename normalizado).
- Gerar relatórios em reports/media_audit/:
  * media_map.json: mapa origem → (id/url/displayName/used/usedBy/duplicates)
  * unused_media.csv: mídias órfãs (não usadas)
  * duplicates.csv: grupos de duplicatas

Observação: Para segurança, a deleção não é executada por padrão. Este script gera um plano.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import unicodedata
from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from bs4 import BeautifulSoup

# Reuso de utilidades existentes (rate limit, retries, headers)
try:
    from src.migrators.wix_migrator import wix_headers, with_retries, RateLimiter
except Exception:
    wix_headers = None  # type: ignore
    with_retries = None  # type: ignore
    RateLimiter = None  # type: ignore


MEDIA_AUDIT_DIR = os.path.join("reports", "media_audit")


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def read_config(config_path: str = "config/migration_config.json") -> Dict[str, Any]:
    if not os.path.exists(config_path):
        return {"wix": {"base_url": "https://www.wixapis.com", "access_token": ""}}
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    if not isinstance(cfg, dict):
        return {"wix": {"base_url": "https://www.wixapis.com", "access_token": ""}}
    cfg.setdefault("wix", {})
    cfg["wix"].setdefault("base_url", "https://www.wixapis.com")
    cfg["wix"].setdefault("access_token", "")
    return cfg


def _strip_query(url: str) -> str:
    return url.split("?")[0]


def _basename(path_or_url: str) -> str:
    s = _strip_query(path_or_url)
    s = s.rstrip("/")
    return s.split("/")[-1]


def _normalize_filename(name: str) -> str:
    # Remove tamanho padrão WordPress -1024x768 e similares
    name = re.sub(r"-(\d+)x(\d+)(?=\.[a-zA-Z0-9]+$)", "", name)
    # Remover sufixos ~mv2 antes da extensão (Wix)
    name = re.sub(r"~mv2", "", name)
    # NFKD → ASCII minúsculo
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower()
    # Colapsar separadores
    name = re.sub(r"\s+", "-", name)
    name = re.sub(r"[^a-z0-9_.-]", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return name


def canonical_key_from_url(url: str) -> str:
    return _normalize_filename(_basename(url))


def canonical_key_from_display_name(display_name: str) -> str:
    return _normalize_filename(display_name)


def collect_wordpress_sources(csv_path: str) -> Dict[str, Set[str]]:
    """Coleta imagens de origem do CSV do WordPress.

    Retorna: dict origem_key -> set(urls)
    """
    sources: Dict[str, Set[str]] = {}
    if not os.path.exists(csv_path):
        return sources
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Coluna padrão "Image URL" (pode conter pipe com múltiplas URLs)
            img_field = (row.get("Image URL") or "").strip()
            if img_field:
                for u in [p.strip() for p in img_field.split("|") if p.strip()]:
                    key = canonical_key_from_url(u)
                    sources.setdefault(key, set()).add(u)
            # Extrair <img src> do HTML se disponível
            html = row.get("Content") or ""
            if html:
                soup = BeautifulSoup(html, "html.parser")
                for img in soup.find_all("img"):
                    src = img.get("src")
                    if not src:
                        continue
                    key = canonical_key_from_url(src)
                    sources.setdefault(key, set()).add(src)
    return sources


def collect_local_wix_posts_used_media(posts_dir: str = "data/posts") -> Tuple[Set[str], Dict[str, List[str]]]:
    """Coleta IDs de mídia usados em posts Wix locais e mapeia quem usa.

    Retorna:
      - used_ids: conjunto de media ids (ex.: '8ef77a_xxx~mv2.jpg')
      - used_by: dict media_id -> [slugs]
    """
    used_ids: Set[str] = set()
    used_by: Dict[str, List[str]] = {}

    def _add_use(mid: Optional[str], slug: Optional[str]) -> None:
        if not mid:
            return
        used_ids.add(mid)
        if slug:
            used_by.setdefault(mid, []).append(slug)

    def _walk_nodes(nodes: Any, slug: Optional[str]) -> None:
        if not isinstance(nodes, list):
            return
        for n in nodes:
            if not isinstance(n, dict):
                continue
            # Imagem inline
            if n.get("type") == "IMAGE":
                image = ((n.get("imageData") or {}).get("image") or {})
                src = image.get("src") or {}
                _add_use(src.get("id"), slug)
            # Nós compostos
            if "nodes" in n:
                _walk_nodes(n["nodes"], slug)

    if not os.path.isdir(posts_dir):
        return used_ids, used_by
    for fn in os.listdir(posts_dir):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(posts_dir, fn)
        try:
            with open(path, "r", encoding="utf-8") as f:
                post = json.load(f)
        except Exception:
            continue
        slug = post.get("slug") or post.get("Slug")
        # Capa
        cover = ((post.get("coverMedia") or {}).get("image") or {})
        _add_use(cover.get("id"), slug)
        # Rich content
        rich = post.get("richContent") or {}
        _walk_nodes(rich.get("nodes") or [], slug)
    return used_ids, used_by


def query_all_wix_media(cfg: Dict[str, Any], *, page_size: int = 200) -> List[Dict[str, Any]]:
    """Lista todos os arquivos do Site Media via API.

    Requer: wix_headers, with_retries, RateLimiter disponíveis.
    """
    if wix_headers is None or with_retries is None or RateLimiter is None:
        print("[WARN] Dependências de rede indisponíveis (wix_migrator). Pulando consulta remota.")
        return []
    import requests
    limiter = RateLimiter(rpm=180)
    base = cfg["wix"].get("base_url", "https://www.wixapis.com")
    media: List[Dict[str, Any]] = []
    offset = 0
    while True:
        limiter.wait()
        def do() -> requests.Response:
            # API de query do Site Media: POST /site-media/v1/files/query
            url = f"{base}/site-media/v1/files/query"
            body = {"query": {"paging": {"limit": page_size, "offset": offset}}}
            return requests.post(url, headers={**wix_headers(cfg["wix"]), "Content-Type": "application/json"}, json=body)
        resp = with_retries(do)
        js = resp.json()
        items = (js.get("files") or [])
        if not items:
            break
        media.extend(items)
        if len(items) < page_size:
            break
        offset += page_size
    return media


def build_media_index(media_items: List[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    """Cria índices por id e por chave canônica do displayName/url."""
    by_id: Dict[str, Dict[str, Any]] = {}
    by_key: Dict[str, List[Dict[str, Any]]] = {}
    for m in media_items:
        mid = m.get("id") or ((m.get("file") or {}).get("id"))
        if not mid:
            continue
        by_id[mid] = m
        display = m.get("displayName") or m.get("filename") or _basename(m.get("url") or m.get("fileUrl") or "")
        if display:
            key = canonical_key_from_display_name(display)
            by_key.setdefault(key, []).append(m)
    return by_id, by_key


def write_json(path: str, data: Any) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_csv(path: str, rows: List[List[Any]], header: Optional[List[str]] = None) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if header:
            w.writerow(header)
        w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description="Auditoria de mídias Wix")
    ap.add_argument("--csv", default="docs/posts_wordpress.csv", help="CSV WordPress de origem")
    ap.add_argument("--posts", default="data/posts", help="Diretório com posts Wix (JSON)")
    ap.add_argument("--no-network", action="store_true", help="Não consultar API do Wix (usa apenas dados locais)")
    ap.add_argument("--config", default="config/migration_config.json", help="Caminho do arquivo de configuração")
    args = ap.parse_args()

    cfg = read_config(args.config)

    # 1) Origens do WordPress
    wp_sources = collect_wordpress_sources(args.csv)  # key -> {urls}

    # 2) Uso atual em posts Wix (locais)
    used_ids, used_by = collect_local_wix_posts_used_media(args.posts)

    # 3) Inventário remotor do Site Media
    media_items: List[Dict[str, Any]] = []
    if not args.no_network:
        try:
            media_items = query_all_wix_media(cfg)
        except Exception as e:
            print(f"[WARN] Falha na query remota do Site Media: {e}")
    else:
        print("[INFO] --no-network habilitado: pulando consulta remota do Site Media.")

    by_id, by_key = build_media_index(media_items)

    # 4) Montar dicionário origem → Wix
    media_map: Dict[str, Any] = {}
    for key, urls in wp_sources.items():
        candidates = by_key.get(key, [])
        chosen: Optional[Dict[str, Any]] = candidates[0] if candidates else None
        entry = {
            "originKey": key,
            "originUrls": sorted(urls),
            "match": {
                "id": (chosen or {}).get("id"),
                "displayName": (chosen or {}).get("displayName") or (chosen or {}).get("filename"),
                "url": (chosen or {}).get("url") or (chosen or {}).get("fileUrl"),
            },
            "duplicates": [m.get("id") for m in candidates[1:]] if len(candidates) > 1 else [],
            "used": bool(chosen and chosen.get("id") in used_ids),
            "usedBy": used_by.get((chosen or {}).get("id", ""), []),
        }
        media_map[key] = entry

    # 5) Listas auxiliares: órfãos e duplicatas
    unused_rows: List[List[Any]] = []
    dup_rows: List[List[Any]] = []
    # Órfãos: itens do inventário que não aparecem em 'used_ids'
    for mid, m in by_id.items():
        if mid not in used_ids:
            display = m.get("displayName") or m.get("filename") or _basename(m.get("url") or m.get("fileUrl") or "")
            url = m.get("url") or m.get("fileUrl")
            unused_rows.append([mid, display, url])
    # Duplicatas por chave
    for key, items in by_key.items():
        if len(items) > 1:
            for m in items:
                display = m.get("displayName") or m.get("filename") or _basename(m.get("url") or m.get("fileUrl") or "")
                url = m.get("url") or m.get("fileUrl")
                dup_rows.append([key, m.get("id"), display, url])

    # 6) Persistência
    write_json(os.path.join(MEDIA_AUDIT_DIR, "media_map.json"), media_map)
    write_csv(os.path.join(MEDIA_AUDIT_DIR, "unused_media.csv"), unused_rows, ["id", "displayName", "url"])
    write_csv(os.path.join(MEDIA_AUDIT_DIR, "duplicates.csv"), dup_rows, ["canonicalKey", "id", "displayName", "url"])

    print(f"[OK] Auditoria concluída. Saídas em {MEDIA_AUDIT_DIR}")


if __name__ == "__main__":
    sys.exit(main())

