#!/usr/bin/env python3
"""
Lê o JSON gerado por extract_tags_to_wix_json.py, cria as tags no Wix Blog via REST
e atualiza o JSON inserindo o "id" retornado para cada tag criada (ou existente).

Requer um token de autorização válido para o site Wix (header Authorization).

Uso:
  python scripts/push_wix_tags.py \
    --input data/tags_wix.json \
    --auth "$WIX_AUTH" \
    [--dry-run] [--limit 50]

Obs.:
- Endpoints usados:
  - POST https://www.wixapis.com/blog/v3/tags            (createTag)
  - GET  https://www.wixapis.com/blog/v3/tags/labels/{label} (getTagByLabel, fallback quando já existe)
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import time


# Base da API do Wix Blog. Será atualizado em tempo de execução a partir do config.
WIX_BLOG_BASE = "https://www.wixapis.com/blog/v3"


@dataclass
class TagItem:
    label: str
    language: str
    slug: Optional[str] = None
    id: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TagItem":
        return cls(
            label=d.get("label", ""),
            language=d.get("language", "pt-BR"),
            slug=d.get("slug"),
            id=d.get("id"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"label": self.label, "language": self.language, "slug": self.slug, "id": self.id}


def parse_args() -> argparse.Namespace:
    """Processa argumentos de CLI.

    Integração com config/migration_config.json:
    - Se não informado via CLI, limite e dry-run serão lidos do config.
    - Token de auth e base_url também serão lidos do config quando ausentes.
    """
    # Primeiro parser mínimo para capturar caminho do config sem validar o restante
    base = argparse.ArgumentParser(add_help=False)
    base.add_argument(
        "--config",
        default="config/migration_config.json",
        help="Caminho do arquivo de configuração JSON",
    )
    # Captura somente --config e argumentos restantes
    base_args, remaining = base.parse_known_args()

    p = argparse.ArgumentParser(
        parents=[base],
        description="Criar tags no Wix Blog e atualizar JSON com IDs",
    )
    p.add_argument("--input", default="data/tags_wix.json", help="Arquivo JSON de entrada/saída")
    # Auth: deixe sem default explícito; resolveremos via env/config depois
    p.add_argument("--auth", default=None, help="Token Authorization para APIs Wix")
    p.add_argument("--limit", type=int, default=None, help="Cria no máximo N tags (para testes)")
    # Suporte a tri-state: --dry-run / --no-dry-run. Se nenhum for passado, será decidido pelo config
    p.add_argument("--dry-run", dest="dry_run", action="store_true", help="Não chama APIs, apenas imprime o plano")
    p.add_argument("--no-dry-run", dest="dry_run", action="store_false", help="Força execução real das chamadas")
    p.set_defaults(dry_run=None)  # None -> decidir com base no config

    return p.parse_args(remaining)


def ensure_auth(auth: Optional[str]) -> str:
    if not auth:
        raise SystemExit(
            "Token de autorização não informado. Use --auth ou defina WIX_AUTH/WIX_AUTH_TOKEN."
        )
    return auth


def load_config(path: Path) -> Dict[str, Any]:
    """Carrega o JSON de configuração.

    Espera a estrutura básica:
    {
      "wix": {"access_token": "...", "api_key": "...", "base_url": "https://www.wixapis.com", ...},
      "migration": {"dry_run": false, "limit": 3}
    }
    """
    if not path.exists():
        raise SystemExit(f"Arquivo de configuração não encontrado: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"Config inválido em {path}: {e}")


def _build_headers(auth: str, site_id: Optional[str]) -> Dict[str, str]:
    headers = {"Authorization": auth, "Content-Type": "application/json"}
    if site_id:
        # Muitos endpoints Wix exigem o identificador do site no header
        headers["wix-site-id"] = site_id
    return headers


def create_tag(
    session: requests.Session,
    auth: str,
    site_id: Optional[str],
    label: str,
    language: str,
    slug: Optional[str],
    *,
    max_retries: int = 5,
    base_sleep: float = 1.0,
) -> Optional[dict]:
    url = f"{WIX_BLOG_BASE}/tags"
    headers = _build_headers(auth, site_id)
    body: Dict[str, Any] = {"label": label, "language": language}
    if slug:
        body["slug"] = slug
    attempt = 0
    while True:
        resp = session.post(url, headers=headers, json=body, timeout=30)
        if resp.status_code == 200:
            return resp.json().get("tag") or resp.json()
        if resp.status_code in (400, 409):
            # Conflito/duplicada: tenta buscar por label
            return None
        if resp.status_code == 429 or 500 <= resp.status_code < 600:
            # Rate limit ou erro transitório: backoff exponencial com Retry-After se houver
            attempt += 1
            if attempt > max_retries:
                break
            retry_after = resp.headers.get("Retry-After")
            if retry_after:
                try:
                    sleep_s = float(retry_after)
                except ValueError:
                    sleep_s = base_sleep * (2 ** (attempt - 1))
            else:
                sleep_s = base_sleep * (2 ** (attempt - 1))
            print(f"Aviso: {resp.status_code} ao criar '{label}', aguardando {sleep_s:.1f}s e tentando novamente ({attempt}/{max_retries})")
            time.sleep(sleep_s)
            continue
        # Erro não tratável
        raise RuntimeError(f"Falha ao criar tag '{label}': {resp.status_code} {resp.text}")
    # Se saiu do loop sem sucesso
    raise RuntimeError(f"Limite de tentativas excedido ao criar tag '{label}': {resp.status_code} {resp.text}")


def get_tag_by_label(
    session: requests.Session,
    auth: str,
    site_id: Optional[str],
    label: str,
    language: Optional[str],
    *,
    max_retries: int = 5,
    base_sleep: float = 1.0,
) -> Optional[dict]:
    # label pode conter '/'; endpoint aceita como path (labels/{label})
    url = f"{WIX_BLOG_BASE}/tags/labels/{label}"
    headers = _build_headers(auth, site_id)
    params = {"language": language} if language else None
    attempt = 0
    while True:
        resp = session.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            # Algumas respostas usam { tag: {...} }
            return data.get("tag") or data
        if resp.status_code == 404:
            return None
        if resp.status_code == 429 or 500 <= resp.status_code < 600:
            attempt += 1
            if attempt > max_retries:
                break
            retry_after = resp.headers.get("Retry-After")
            if retry_after:
                try:
                    sleep_s = float(retry_after)
                except ValueError:
                    sleep_s = base_sleep * (2 ** (attempt - 1))
            else:
                sleep_s = base_sleep * (2 ** (attempt - 1))
            print(f"Aviso: {resp.status_code} ao consultar '{label}', aguardando {sleep_s:.1f}s e tentando novamente ({attempt}/{max_retries})")
            time.sleep(sleep_s)
            continue
        raise RuntimeError(f"Falha ao consultar tag por label '{label}': {resp.status_code} {resp.text}")


def main() -> None:
    args = parse_args()

    # Carrega config
    config_path = Path(args.config)
    cfg = load_config(config_path)

    # Ajusta base URL da API a partir do config
    wix_cfg = cfg.get("wix", {})
    base_url = (wix_cfg.get("base_url") or "https://www.wixapis.com").rstrip("/")
    global WIX_BLOG_BASE
    WIX_BLOG_BASE = f"{base_url}/blog/v3"

    # Resolve token de autorização: CLI > ENV > config.api_key > config.access_token
    # Preferimos api_key (token de app instalada) pois costuma ter escopos necessários para Blog
    auth = (
        args.auth
        or os.getenv("WIX_AUTH")
        or os.getenv("WIX_AUTH_TOKEN")
        or wix_cfg.get("api_key")
        or wix_cfg.get("access_token")
    )
    auth = ensure_auth(auth)

    # Captura site_id quando disponível (necessário por vários endpoints Wix)
    site_id = wix_cfg.get("site_id")

    # Resolve dry_run: CLI (tri-state) > config > default False
    mig_cfg = cfg.get("migration", {})
    dry_run_cfg = bool(mig_cfg.get("dry_run", False))
    dry_run = dry_run_cfg if args.dry_run is None else args.dry_run

    # Resolve limit: CLI > config > None
    limit = args.limit if args.limit is not None else mig_cfg.get("limit")

    in_path = Path(args.input)
    if not in_path.exists():
        raise SystemExit(f"Arquivo não encontrado: {in_path}")

    doc = json.loads(in_path.read_text(encoding="utf-8"))
    tags_data: List[TagItem] = [TagItem.from_dict(t) for t in doc.get("tags", [])]

    session = requests.Session()

    processed = 0
    for item in tags_data:
        if limit is not None and processed >= int(limit):
            break

        if item.id:
            processed += 1
            continue  # já tem id

        if dry_run:
            print(f"[dry-run] Criaria tag: label='{item.label}', lang='{item.language}'")
            processed += 1
            continue

        created = create_tag(session, auth, site_id, item.label, item.language, item.slug)
        if created and created.get("id"):
            item.id = created["id"]
            print(f"Criada: {item.label} -> {item.id}")
        else:
            # Pode já existir: tenta buscar por label
            existing = get_tag_by_label(session, auth, site_id, item.label, item.language)
            if existing and existing.get("id"):
                item.id = existing["id"]
                print(f"Existente: {item.label} -> {item.id}")
            else:
                print(f"Aviso: não foi possível obter ID para tag '{item.label}'")
        processed += 1

    # Persiste de volta no mesmo arquivo, mantendo metadados
    doc["tags"] = [t.to_dict() for t in tags_data]
    in_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Atualizado: {in_path}")
    if dry_run:
        print("Execução em modo dry-run habilitada por configuração/CLI.")
    print(f"API base configurada: {WIX_BLOG_BASE}")


if __name__ == "__main__":
    main()
