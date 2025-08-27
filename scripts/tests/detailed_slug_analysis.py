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

# Criar uma versão modificada da função _sanitize_slug para adicionar logs
def _sanitize_slug_with_logging(s: str) -> str:
    original = s
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower().strip().replace(" ", "-")
    import re as _re
    s = _re.sub(r"[^a-z0-9\-]", "-", s)
    s = _re.sub(r"-+", "-", s).strip("-")
    
    if s != original:
        print(f"  [LOG] Slug sanitizado: '{original}' => '{s}'")
    
    return s

# Configuração de teste (dry-run)
config = {
    "wix": {
        "access_token": "test_token",
        "base_url": "https://www.wixapis.com"
    },
    "migration": {
        "dry_run": True,
        "limit": 20,  # Aumentar para encontrar slugs que precisam de sanitização
        "default_author_email": "default@example.com"
    }
}

tool = WordPressMigrationTool(config=config)

# Extrair posts do CSV
posts = extract_posts_from_csv('docs/posts_wordpress.csv')

print("Analisando processo de sanitização de slugs em detalhe:")
print("=" * 60)

# Contadores
total_posts = 0
sanitized_posts = 0

# Verificar cada post
for i, post in enumerate(posts):
    if i >= 20:  # Limitar a 20 posts
        break
        
    total_posts += 1
    slug = post.get("Slug") or ""
    
    # Aplicar a sanitização e verificar se houve mudança
    sanitized = _sanitize_slug_with_logging(slug)
    
    if sanitized != slug:
        sanitized_posts += 1
        print(f"Post {i+1}:")
        print(f"  Title: {post.get('Title') or 'N/A'}")
        print(f"  Slug original: \"{slug}\"")
        print(f"  Slug sanitizado: \"{sanitized}\"")
        print()

print(f"\nResumo:")
print(f"Total de posts analisados: {total_posts}")
print(f"Posts com slugs sanitizados: {sanitized_posts}")
print(f"Posts sem necessidade de sanitização: {total_posts - sanitized_posts}")

if sanitized_posts > 0:
    print(f"\nPercentual de slugs que precisaram de sanitização: {(sanitized_posts/total_posts)*100:.2f}%")
else:
    print(f"\nNenhum slug precisou de sanitização nos primeiros {total_posts} posts.")
    print("Isso pode indicar que os slugs no CSV já estão corretamente formatados.")