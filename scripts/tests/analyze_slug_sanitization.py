#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from src.migration_tool import WordPressMigrationTool
from src.extractors.wordpress_extractor import extract_posts_from_csv
import unicodedata
import re

# Função de sanitização do migration_tool.py
def _sanitize_slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower().strip().replace(" ", "-")
    import re as _re
    s = _re.sub(r"[^a-z0-9\-]", "-", s)
    s = _re.sub(r"-+", "-", s).strip("-")
    return s

# Configuração de teste
config = {
    "wix": {
        "access_token": "test_token",
        "base_url": "https://www.wixapis.com"
    },
    "migration": {
        "dry_run": True,
        "limit": 20,  # Aumentar o limite para encontrar slugs que precisam de sanitização
        "default_author_email": "default@example.com"
    }
}

tool = WordPressMigrationTool(config=config)

# Extrair posts do CSV
posts = extract_posts_from_csv('docs/posts_wordpress.csv')

print("Analisando processo de sanitização de slugs na migração:")
print("=" * 60)

# Contador de slugs sanitizados
sanitized_count = 0

# Verificar os posts em busca de slugs que precisam de sanitização
for i, post in enumerate(posts):
    original_slug = post.get("Slug") or ""
    sanitized = _sanitize_slug(original_slug)
    
    if sanitized != original_slug:
        sanitized_count += 1
        print(f"Post {i+1}:")
        print(f"  Title: {post.get('Title')}")
        print(f"  Slug original: \"{original_slug}\"")
        print(f"  Slug sanitizado: \"{sanitized}\"")
        print(f"  *** SERIA ATUALIZADO ***")
        print()
        
        # Verificar se o log de sanitização estaria sendo gerado
        # (simulando a lógica do migrate_posts)
        if sanitized != original_slug:
            print(f"  [LOG] Slug sanitizado: '{original_slug}' => '{sanitized}'")
        
        print()

print(f"Total de slugs que precisariam de sanitização: {sanitized_count}")

if sanitized_count == 0:
    print("\nNenhum slug encontrado que precise de sanitização.")
    print("Isso pode indicar que:")
    print("1. Todos os slugs no CSV já estão sanitizados")
    print("2. O problema pode estar em outro lugar do pipeline")
    print("3. O problema pode estar relacionado à extração dos slugs do XML")