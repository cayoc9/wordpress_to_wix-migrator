#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from src.migration_tool import WordPressMigrationTool
from src.extractors.wordpress_extractor import extract_posts_from_csv
import unicodedata
import re
import json

# Criar uma instância do WordPressMigrationTool para testes
config = {
    "wix": {
        "access_token": "test_token",
        "base_url": "https://www.wixapis.com"
    },
    "migration": {
        "dry_run": True,
        "limit": 5,
        "default_author_email": "default@example.com"
    }
}

tool = WordPressMigrationTool(config=config)

# Extrair posts do CSV
posts = extract_posts_from_csv('docs/posts_wordpress.csv')

print("Testando o processo completo de sanitização de slugs:")
print("=" * 60)

# Verificar os primeiros 5 posts
for i, post in enumerate(posts[:5]):
    original_slug = post.get("Slug") or ""
    
    # Aplicar a sanitização como no migration_tool.py
    def _sanitize_slug(s: str) -> str:
        s = unicodedata.normalize("NFKD", s)
        s = s.encode("ascii", "ignore").decode("ascii")
        s = s.lower().strip().replace(" ", "-")
        import re as _re
        s = _re.sub(r"[^a-z0-9\\-]", "-", s)
        s = _re.sub(r"-+", "-", s).strip("-")
        return s
    
    sanitized = _sanitize_slug(original_slug)
    
    print(f"Post {i+1}:")
    print(f"  Title: {post.get('Title')}")
    print(f"  Slug original: \"{original_slug}\"")
    print(f"  Slug sanitizado: \"{sanitized}\"")
    
    if sanitized != original_slug:
        print(f"  *** DIFERENÇA IDENTIFICADA - Slug seria atualizado ***")
        # Simular a atualização do slug no post
        post["Slug"] = sanitized
    
    print()
    
    # Verificar se o slug sanitizado está sendo passado corretamente para a API
    print(f"  Slug que seria enviado para a API: \"{post.get('Slug')}\"")
    print()