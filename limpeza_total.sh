#!/bin/bash

# --- CONFIGURAÇÃO ---
# Token de autorização. Se o script falhar, pode ser que ele tenha expirado.
TOKEN="OauthNG.JWS.eyJraWQiOiJZSEJzdUpwSCIsImFsZyI6IkhTMjU2In0.eyJkYXRhIjoie1wiaW5zdGFuY2VcIjp7XCJpbnN0YW5jZUlkXCI6XCI5YzFlNjRhNS1kMmEyLTRjZmItYWVmMS05YjliNWNhNWQ5OWZcIixcImFwcERlZklkXCI6XCIwNTNjYmM4MS1mMWIyLTQwY2QtYWY5Ni00MjEzN2E2MWVhNDNcIixcInNpZ25EYXRlXCI6XCIyMDI1LTA4LTIwVDE0OjAyOjI0LjA3MVpcIixcInBlcm1pc3Npb25zXCI6XCJcIixcImRlbW9Nb2RlXCI6ZmFsc2UsXCJzaXRlT3duZXJJZFwiOlwiOGVmNzdhY2QtNjRiMS00NWUwLTgxOWUtYmM1MTY2NDA5MGM1XCIsXCJtZXRhU2l0ZUlkXCI6XCJkOWJlNjM5NS1lN2E3LTQ5YzEtYWMzOC1hOTFiZGEzMWI3OGVcIixcImV4cGlyYXRpb25EYXRlXCI6XCIyMDI1LTA4LTIwVDE4OjAyOjI0LjA3MVpcIixcInBzXCI6XCIwNTNjYmM4MS1mMWIyLTQwY2QtYWY5Ni00MjEzN2E2MWVhNDM6XjQuMC4wXCJ9fSIsImlhdCI6MTc1NTY5ODU0NCwiZXhwIjoxNzU1NzEyOTQ0fQ.rndSOrIumlM4ZMu9H4im_fZ0LZaFsTZLAmBJyTNCNhE"

# Endpoints da API
PUBLISHED_ENDPOINT="https://www.wixapis.com/blog/v3/posts?paging.limit=100&paging.offset=0"
DRAFTS_ENDPOINT="https://www.wixapis.com/blog/v3/draft-posts?paging.limit=100&paging.offset=0"
TRASH_ENDPOINT="https://www.wixapis.com/blog/v3/draft-posts/trash-bin"
# --- FIM DA CONFIGURAÇÃO ---


# 1. Verifica se a ferramenta 'jq' está instalada
if ! command -v jq &> /dev/null
then
    echo "ERRO: A ferramenta 'jq' é necessária para este script."
    echo "Por favor, instale-a para continuar (ex: 'sudo apt-get install jq')."
    exit 1
fi

# --- TAREFA 1: MOVER POSTS PUBLICADOS PARA A LIXEIRA ---
echo "====================================================="
echo "ETAPA 1: MOVENDO POSTS PUBLICADOS PARA A LIXEIRA"
echo "====================================================="
while true; do
    echo "Buscando lote de posts publicados..."
    RESPONSE=$(curl -s "$PUBLISHED_ENDPOINT" -H "Authorization: Bearer $TOKEN")
    POST_IDS=($(echo "$RESPONSE" | jq -r '.posts[].id'))

    if [ ${#POST_IDS[@]} -eq 0 ]; then
        echo "✅ Nenhum post publicado encontrado."
        break
    fi

    echo "Encontrados ${#POST_IDS[@]} posts publicados. Movendo para a lixeira..."
    for id in "${POST_IDS[@]}"; do
        echo "   -> Movendo post $id para a lixeira..."
        # O comando DELETE sem 'permanent=true' move para a lixeira
        curl -s -f -X DELETE "https://www.wixapis.com/blog/v3/draft-posts/$id" -H "Authorization: Bearer $TOKEN"
        if [ $? -ne 0 ]; then echo "      ...ERRO ao mover o post $id."; fi
    done
    echo "Lote movido. Verificando novamente..."
    sleep 2
done


# --- TAREFA 2: APAGAR RASCUNHOS PERMANENTEMENTE ---
echo -e "\n====================================================="
echo "ETAPA 2: APAGANDO RASCUNHOS PERMANENTEMENTE"
echo "====================================================="
while true; do
    echo "Buscando lote de rascunhos..."
    RESPONSE=$(curl -s "$DRAFTS_ENDPOINT" -H "Authorization: Bearer $TOKEN")
    POST_IDS=($(echo "$RESPONSE" | jq -r '.draftPosts[].id'))

    if [ ${#POST_IDS[@]} -eq 0 ]; then
        echo "✅ Nenhum rascunho encontrado."
        break
    fi

    echo "Encontrados ${#POST_IDS[@]} rascunhos. Apagando permanentemente..."
    for id in "${POST_IDS[@]}"; do
        echo "   -> Apagando rascunho $id..."
        curl -s -f -X DELETE "https://www.wixapis.com/blog/v3/draft-posts/$id?permanent=true" -H "Authorization: Bearer $TOKEN"
        if [ $? -ne 0 ]; then echo "      ...ERRO ao apagar o rascunho $id."; fi
    done
    echo "Lote apagado. Verificando novamente..."
    sleep 2
done


# --- TAREFA 3: LIMPAR A LIXEIRA PERMANENTEMENTE ---
echo -e "\n====================================================="
echo "ETAPA 3: LIMPANDO A LIXEIRA PERMANENTEMENTE"
echo "====================================================="
while true; do
    echo "Buscando lote de itens na lixeira..."
    RESPONSE=$(curl -s "$TRASH_ENDPOINT" -H "Authorization: Bearer $TOKEN")
    POST_IDS=($(echo "$RESPONSE" | jq -r '.draftPosts[].id'))

    if [ ${#POST_IDS[@]} -eq 0 ]; then
        echo "✅ Lixeira vazia."
        break
    fi

    echo "Encontrados ${#POST_IDS[@]} itens na lixeira. Apagando permanentemente..."
    for id in "${POST_IDS[@]}"; do
        echo "   -> Apagando item da lixeira: $id"
        curl -s -f -X DELETE "https://www.wixapis.com/blog/v3/draft-posts/trash-bin/$id" -H "Authorization: Bearer $TOKEN"
        if [ $? -ne 0 ]; then echo "      ...ERRO ao apagar o item $id da lixeira."; fi
    done
    echo "Lote da lixeira apagado. Verificando novamente..."
    sleep 2
done

echo -e "\n🎉 PROCESSO CONCLUÍDO! Todos os posts publicados, rascunhos e itens da lixeira foram apagados."
