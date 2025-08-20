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
    p = argparse.ArgumentParser(description="Criar tags no Wix Blog e atualizar JSON com IDs")
    p.add_argument("--input", default="data/tags_wix.json", help="Arquivo JSON de entrada/saída")
    p.add_argument("--auth", default=os.getenv("WIX_AUTH") or os.getenv("WIX_AUTH_TOKEN"), help="Token Authorization")
    p.add_argument("--limit", type=int, default=None, help="Cria no máximo N tags (para testes)")
    p.add_argument("--dry-run", action="store_true", help="Não chama APIs, apenas imprime o plano")
    return p.parse_args()


def ensure_auth(auth: Optional[str]) -> str:
    if not auth:
        raise SystemExit(
            "Token de autorização não informado. Use --auth ou defina WIX_AUTH/WIX_AUTH_TOKEN."
        )
    return auth


def create_tag(session: requests.Session, auth: str, label: str, language: str, slug: Optional[str]) -> Optional[dict]:
    url = f"{WIX_BLOG_BASE}/tags"
    headers = {"Authorization": auth, "Content-Type": "application/json"}
    body: Dict[str, Any] = {"label": label, "language": language}
    if slug:
        body["slug"] = slug
    resp = session.post(url, headers=headers, json=body, timeout=30)
    if resp.status_code == 200:
        return resp.json().get("tag") or resp.json()
    # Conflito/duplicada: tenta buscar por label
    if resp.status_code in (400, 409):
        return None
    # Erro não tratável
    raise RuntimeError(f"Falha ao criar tag '{label}': {resp.status_code} {resp.text}")


def get_tag_by_label(session: requests.Session, auth: str, label: str, language: Optional[str]) -> Optional[dict]:
    # label pode conter '/'; endpoint aceita como path (labels/{label})
    url = f"{WIX_BLOG_BASE}/tags/labels/{label}"
    headers = {"Authorization": auth, "Content-Type": "application/json"}
    params = {"language": language} if language else None
    resp = session.get(url, headers=headers, params=params, timeout=30)
    if resp.status_code == 200:
        data = resp.json()
        # Algumas respostas usam { tag: {...} }
        return data.get("tag") or data
    if resp.status_code == 404:
        return None
    raise RuntimeError(f"Falha ao consultar tag por label '{label}': {resp.status_code} {resp.text}")


def main() -> None:
    args = parse_args()
    in_path = Path(args.input)
    auth = ensure_auth(args.auth)
    if not in_path.exists():
        raise SystemExit(f"Arquivo não encontrado: {in_path}")

    doc = json.loads(in_path.read_text(encoding="utf-8"))
    tags_data: List[TagItem] = [TagItem.from_dict(t) for t in doc.get("tags", [])]

    session = requests.Session()

    processed = 0
    for item in tags_data:
        if args.limit is not None and processed >= args.limit:
            break

        if item.id:
            processed += 1
            continue  # já tem id

        if args.dry_run:
            print(f"[dry-run] Criaria tag: label='{item.label}', lang='{item.language}'")
            processed += 1
            continue

        created = create_tag(session, auth, item.label, item.language, item.slug)
        if created and created.get("id"):
            item.id = created["id"]
            print(f"Criada: {item.label} -> {item.id}")
        else:
            # Pode já existir: tenta buscar por label
            existing = get_tag_by_label(session, auth, item.label, item.language)
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


if __name__ == "__main__":
    main()

