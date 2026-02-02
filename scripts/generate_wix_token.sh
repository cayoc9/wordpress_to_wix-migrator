#!/bin/bash
#
# Este script gera um token de acesso da API do Wix usando curl
# e o salva em 'wix_token.json' no diretório raiz do projeto.

# Garante que o script seja executado a partir do diretório raiz do projeto
cd "$(dirname "$0")/.." || exit

# Executa o comando curl para obter o token
curl -s -X POST 'https://www.wixapis.com/oauth2/token' \
  -H 'Content-Type: application/json' \
  -d '{
    "grant_type": "client_credentials",
    "client_id": "053cbc81-f1b2-40cd-af96-42137a61ea43",
    "client_secret": "21360a2c-c4d6-497e-aa7d-f0fc74e6462d",
    "instance_id": "9c1e64a5-d2a2-4cfb-aef1-9b9b5ca5d99f"
  }' -o wix_token.json

# Verifica se o arquivo de token foi criado e não está vazio
if [ -s "wix_token.json" ]; then
  echo "Token do Wix gerado e salvo com sucesso em wix_token.json."
else
  echo "Erro: Falha ao gerar o token do Wix."
  exit 1
fi    