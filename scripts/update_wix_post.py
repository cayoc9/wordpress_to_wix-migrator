#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Atualiza um post do Wix Blog via REST API.

Este script lida com a atualização de posts, quer estejam em estado de rascunho
ou já publicados.

- Se o post estiver publicado, ele primeiro cria uma nova versão de rascunho
  com as atualizações e, opcionalmente, publica essa nova versão.
- Se o post já for um rascunho, ele simplesmente o atualiza.

Pré-requisitos:
- Python 3.8+
- Dependências: requests (ver requirements.txt)
- Arquivo de configuração: config/migration_config.json com wix.api_key e wix.site_id
  ou variáveis de ambiente WIX_API_KEY e WIX_SITE_ID.

Uso:
  python scripts/update_wix_post.py \
    --post-id <uuid-do-post> \
    --file data/posts/<uuid-do-post>.json \
    [--publish]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import requests

# A API de Blog v3 é o padrão moderno.
BASE_URL = "https://www.wixapis.com/blog/v3"


def die(msg: str, code: int = 1) -> None:
    """Imprime uma mensagem de erro para stderr e encerra o script."""
    print(f"ERRO: {msg}", file=sys.stderr)
    sys.exit(code)


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Analisa os argumentos da linha de comando."""
    p = argparse.ArgumentParser(
        description=(
            "Atualiza um post do Wix Blog (publicado ou rascunho).\n\n"
            "Exemplo de uso:\n"
            "python scripts/update_wix_post.py --post-id 774b42ef-b746-4b6f-8239-4e6f3f39841f "
            "--file data/posts/774b42ef-b746-4b6f-8239-4e6f3f39841f.json --publish"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p.add_argument("--post-id", help="ID do post (UUID) a ser atualizado.")
    p.add_argument(
        "--file",
        help="Caminho para o arquivo JSON local com os dados do post. "
        "Se não for fornecido, o padrão é data/posts/<post-id>.json.",
    )
    p.add_argument(
        "--publish",
        action="store_true",
        help="Publica o post imediatamente após a atualização. "
        "Se o post já estava publicado, isto publica as novas alterações.",
    )
    return p.parse_args(argv)


def load_wix_config() -> Dict[str, Any]:
    """Carrega a configuração do arquivo migration_config.json."""
    cfg_path = Path(__file__).parent.parent / "config" / "migration_config.json"
    if cfg_path.exists():
        try:
            return json.loads(cfg_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError) as e:
            print(f"Aviso: Não foi possível ler o arquivo de configuração: {e}")
            return {}
    return {}


def resolve_auth() -> tuple[str, str]:
    """
    Resolve o token de autenticação e o ID do site.

    A ordem de prioridade é:
    1. Variáveis de ambiente (WIX_API_KEY, WIX_SITE_ID).
    2. Arquivo de configuração (config/migration_config.json).

    Retorna:
        Uma tupla contendo (cabeçalho_de_autorização, site_id).
    """
    cfg = load_wix_config()
    wix_cfg = cfg.get("wix", {})

    # Usa a API Key que é mais segura para operações de escrita.
    api_key = os.getenv("WIX_API_KEY") or wix_cfg.get("api_key")
    site_id = os.getenv("WIX_SITE_ID") or wix_cfg.get("site_id")

    if not api_key:
        die(
            "API Key não encontrada. Defina WIX_API_KEY ou configure 'wix.api_key' "
            "em config/migration_config.json."
        )

    if not site_id:
        die(
            "Site ID não encontrado. Defina WIX_SITE_ID ou configure 'wix.site_id' "
            "em config/migration_config.json."
        )

    # O cabeçalho de autorização é a própria chave.
    return api_key, site_id


def wix_request(
    method: str,
    path: str,
    *, 
    json_body: Dict[str, Any] | None = None,
    params: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Envia uma requisição para a API do Wix e trata a resposta.

    Args:
        method: Método HTTP (GET, POST, PATCH, etc.).
        path: Caminho da API (ex: /posts/some-id).
        json_body: Corpo da requisição em formato de dicionário.
        params: Parâmetros de consulta (query string).

    Returns:
        A resposta da API em formato de dicionário.
    """
    authorization, site_id = resolve_auth()
    url = f"{BASE_URL}{path}"
    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json",
        "wix-site-id": site_id,
    }

    try:
        resp = requests.request(
            method, url, headers=headers, json=json_body, params=params, timeout=30
        )
        resp.raise_for_status()  # Lança uma exceção para respostas de erro (4xx ou 5xx)
        if resp.content:
            return resp.json()
        return {}
    except requests.exceptions.RequestException as e:
        # Tenta extrair uma mensagem de erro mais clara do corpo da resposta
        try:
            error_data = e.response.json()
            message = error_data.get("message", e.response.text)
            details = error_data.get("details", {})
            die(f"Falha na API ({e.response.status_code}): {message}\nDetalhes: {details}")
        except (json.JSONDecodeError, AttributeError):
            die(f"Falha na comunicação com a API do Wix: {e}")


def get_post(post_id: str) -> Dict[str, Any]:
    """Busca os dados de um post (publicado ou rascunho)."""
    # A API de Posts consegue ler tanto publicados quanto rascunhos pelo mesmo ID.
    data = wix_request("GET", f"/posts/{post_id}")
    # A resposta pode vir aninhada em { "post": {...} }
    return data.get("post", data)


def update_post(
    post_id: str,
    payload: Dict[str, Any],
    is_published: bool
) -> Dict[str, Any]:
    """
    Atualiza um post, seja ele um rascunho ou um post já publicado.

    Args:
        post_id: O ID do post a ser atualizado.
        payload: O dicionário com os campos a serem atualizados.
        is_published: Um booleano que indica se o post está atualmente publicado.

    Returns:
        O post atualizado.
    """
    params = {}
    if is_published:
        # Se o post já está publicado, usamos a ação 'UPDATE_PUBLICATION'.
        # Isso cria um novo rascunho com as alterações, mantendo o post original no ar.
        params["action"] = "UPDATE_PUBLICATION"
        print("INFO: Post está publicado. Criando rascunho com as alterações...")
    else:
        print("INFO: Atualizando rascunho existente...")

    # A atualização é sempre feita no endpoint de 'draft-posts'.
    # A API do Wix é inteligente o suficiente para lidar com isso usando o mesmo ID.
    data = wix_request(
        "PATCH", f"/draft-posts/{post_id}", json_body={"draftPost": payload}, params=params
    )
    return data.get("draftPost", data)


def publish_post(post_id: str) -> None:
    """Publica a versão mais recente de um rascunho de post."""
    wix_request("POST", f"/posts/{post_id}/publish", json_body={})


def build_update_payload(local_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filtra o JSON local para incluir apenas os campos permitidos para atualização.
    """
    allowed_fields = {
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
        "seoData",
        "seoSlug",
    }
    # Retorna um novo dicionário contendo apenas as chaves permitidas que existem no JSON local.
    return {key: local_json[key] for key in allowed_fields if key in local_json}


def main(argv: list[str]) -> int:
    """Função principal do script."""
    args = parse_args(argv)

    post_id = args.post_id
    if not post_id:
        try:
            post_id = input("Informe o ID do post Wix (UUID): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nOperação cancelada.")
            return 1
    if not post_id:
        die("O ID do post é obrigatório.")

    file_path_str = args.file or f"data/posts/{post_id}.json"
    json_path = Path(file_path_str)

    if not json_path.is_file():
        die(f"Arquivo JSON não encontrado em: {json_path}")

    try:
        local_json = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        die(f"Falha ao decodificar o JSON do arquivo {json_path}: {e}")
    except IOError as e:
        die(f"Falha ao ler o arquivo {json_path}: {e}")

    print(f"➡️  Buscando post '{post_id}' no Wix...")
    current_post = get_post(post_id)
    status = current_post.get("status", "UNKNOWN").upper()
    print(f"✔️  Post localizado. Status atual: {status}")

    is_published = status == "PUBLISHED"

    # Monta o payload apenas com os campos que queremos (e podemos) atualizar.
    payload = build_update_payload(local_json)
    if not payload:
        print("ℹ️  Nenhum campo válido para atualização encontrado no arquivo JSON. Nada a fazer.")
        return 0

    print("➡️  Enviando atualização para o Wix...")
    updated_post = update_post(post_id, payload, is_published)
    new_status = updated_post.get("status", "UNKNOWN").upper()
    print(f"✔️  Post atualizado com sucesso. Novo status do rascunho: {new_status}")

    if args.publish:
        print(f"➡️  Publicando alterações para o post '{post_id}'...")
        publish_post(post_id)
        print("✔️  Post publicado com sucesso!")
    else:
        print("\nℹ️  As alterações foram salvas como um rascunho.")
        print("   Para publicá-las, execute o comando novamente com a flag --publish.")

    return 0


if __name__ == "__main__":
    # Permite que o script seja executado diretamente, passando os argumentos da linha de comando.
    # sys.argv[1:] exclui o nome do próprio script da lista de argumentos.
    raise SystemExit(main(sys.argv[1:]))
