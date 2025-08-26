#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gera um token de acesso da API do Wix usando as credenciais do cliente
e o salva em 'wix_token.json' no diretório raiz.
"""

from __future__ import annotations

import json
from pathlib import Path

import requests
  
# -- Credenciais e configurações --
CLIENT_ID = "053cbc81-f1b2-40cd-af96-42137a61ea43"
CLIENT_SECRET = "21360a2c-c4d6-497e-aa7d-f0fc74e6462d"
INSTANCE_ID = "9c1e64a5-d2a2-4cfb-aef1-9b9b5ca5d99f"
TOKEN_URL = "https://www.wixapis.com/oauth2/token"
OUTPUT_FILE = Path(__file__).parent.parent / "wix_token.json"


def generate_token() -> dict | None:
    """
    Envia uma requisição para a API do Wix para obter um novo token de acesso.

    Returns:
        dict | None: O JSON da resposta se for bem-sucedido, caso contrário None.
    """
    headers = {"Content-Type": "application/json"}
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "instance_id": INSTANCE_ID,
    }

    print(f"Solicitando token de '{TOKEN_URL}'...")
    try:
        response = requests.post(TOKEN_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()  # Lança exceção para respostas 4xx/5xx
        print("Token recebido com sucesso.")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao solicitar o token: {e}")
        if e.response is not None:
            print(f"Resposta do servidor ({e.response.status_code}): {e.response.text}")
        return None


def save_token_to_file(token_data: dict, file_path: Path) -> None:
    """
    Salva os dados do token em um arquivo JSON.

    Args:
        token_data (dict): O dicionário contendo os dados do token.
        file_path (Path): O caminho para o arquivo de saída.
    """
    try:
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(token_data, f, indent=2)
        print(f"Token salvo com sucesso em: {file_path}")
    except IOError as e:
        print(f"Erro ao salvar o token no arquivo: {e}")


def main():
    """Função principal para gerar e salvar o token."""
    token_data = generate_token()
    if token_data:
        save_token_to_file(token_data, OUTPUT_FILE)
    else:
        print("Falha ao gerar o token. O arquivo não foi atualizado.")


if __name__ == "__main__":
    main()