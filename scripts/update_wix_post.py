#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Atualiza posts do Wix Blog via REST API (rascunho → update → publish).

Pré-requisitos:
- Python 3.8+
- Dependências: requests (ver requirements.txt)
- Variáveis de ambiente:
  - WIX_API_KEY: API Key com escopo wix-blog.manage-posts
  - WIX_SITE_ID: ID do site Wix alvo

Uso:
  python scripts/update_wix_post.py \
    --post-id <uuid> \
    --file data/posts/774b42ef-b746-4b6f-8239-4e6f3f39841f.json \
    [--publish]

Notas:
- O ID do post é estável entre rascunho e publicado.
- Para alterar um post publicado, garanta um rascunho, atualize e publique.
- A API usa controle otimista via `revision`; envie sempre a revisão atual.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import requests


BASE_URL = "https://www.wixapis.com/blog/v3"


def die(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    sys.exit(code)


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Atualiza post do Wix Blog (draft → update → publish)",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p.add_argument("--post-id", required=True, help="ID do post (UUID)")
    p.add_argument("--file", required=True, help="Arquivo JSON local com os campos do post")
    p.add_argument("--publish", action="store_true", help="Publicar após atualizar")
    return p.parse_args(argv)


def wix_request(method: str, path: str, *, json_body: Dict[str, Any] | None = None) -> Dict[str, Any] | None:
    api_key = os.getenv("WIX_API_KEY")
    site_id = os.getenv("WIX_SITE_ID")
    if not api_key:
        die("WIX_API_KEY não definido no ambiente.")
    if not site_id:
        die("WIX_SITE_ID não definido no ambiente.")

    url = f"{BASE_URL}{path}"
    headers = {
        "Authorization": api_key,
        "wix-site-id": site_id,
        "Content-Type": "application/json",
    }

    resp = requests.request(method, url, headers=headers, json=json_body, timeout=30)
    if not resp.ok:
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
    try:
        return resp.json()
    except Exception:
        return None


def get_post(post_id: str) -> Dict[str, Any]:
    data = wix_request("GET", f"/posts/{post_id}")
    if not data:
        die("Resposta vazia ao buscar post.")
    # Algumas respostas vêm embrulhadas em { post: {...} }
    return data.get("post") or data


def ensure_draft(post_id: str) -> None:
    # Nem todos os tenants expõem create-draft; se falhar, seguimos com o fluxo.
    try:
        wix_request("POST", f"/posts/{post_id}/create-draft", json_body={})
    except SystemExit:
        # Repassa apenas erros fatais; caso 404 tenha sido tratado como fatal acima.
        # Para ser resiliente, não encerramos aqui: apenas avisamos.
        print("Aviso: create-draft indisponível; seguindo com atualização do rascunho.")


def update_post(post_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    data = wix_request("PATCH", f"/posts/{post_id}", json_body=payload)
    return data.get("post") or data or {}


def publish_post(post_id: str) -> None:
    wix_request("POST", f"/posts/{post_id}/publish", json_body={})


def pick_update_payload(local_json: Dict[str, Any], current_post: Dict[str, Any]) -> Dict[str, Any]:
    allowed = [
        "title",
        "excerpt",
        "slug",
        "featured",
        "pinned",
        "categoryIds",
        "coverMedia",
        "hashtags",
        "minutesToRead",
        "tagIds",
        "language",
        "media",
        "richContent",
    ]
    payload: Dict[str, Any] = {
        "id": current_post.get("id"),
        "revision": current_post.get("revision"),
    }
    for k in allowed:
        if k in local_json:
            payload[k] = local_json[k]
    return payload


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    json_path = Path(args.file)
    if not json_path.exists():
        die(f"Arquivo não encontrado: {json_path}")
    try:
        local_json = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as e:
        die(f"Falha ao ler JSON local: {e}")

    print("➡️  Buscando post atual no Wix...")
    post = get_post(args.post_id)
    post_id = post.get("id")
    status = post.get("status") or post.get("state")
    if not post_id:
        die("Resposta inesperada ao buscar post (sem id).")
    print(f"✔️  Post localizado: {post_id} | status: {status or '(desconhecido)'}")

    is_published = (status == "PUBLISHED") or (post.get("published") is True)
    if is_published:
        print("➡️  Post está publicado. Garantindo rascunho para edição...")
        try:
            ensure_draft(post_id)
        except Exception:
            # Não falhar o fluxo por aqui; continuar.
            print("Aviso: falha ao garantir rascunho; tentando atualizar assim mesmo.")
        print("✔️  Rascunho pronto (ou já existente).")

    payload = pick_update_payload(local_json, post)
    if not payload.get("revision"):
        print("⚠️  Revision ausente; a API pode rejeitar por concorrência.")

    print("➡️  Enviando atualização do rascunho...")
    updated = update_post(post_id, payload)
    new_rev = updated.get("revision")
    print(f"✔️  Atualizado. Nova revision: {new_rev or '(indisponível)'}")

    if args.publish:
        print("➡️  Publicando rascunho atualizado...")
        publish_post(post_id)
        print("✔️  Publicado com sucesso.")
    else:
        print("ℹ️  Atualização aplicada no rascunho. Use --publish para publicar.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

