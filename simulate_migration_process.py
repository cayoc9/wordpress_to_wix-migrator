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
    s = _re.sub(r"[^a-z0-9\\-]", "-", s)
    s = _re.sub(r"-+", "-", s).strip("-")
    return s

# Configuração de teste (dry-run)
config = {
    "wix": {
        "access_token": "test_token",
        "base_url": "https://www.wixapis.com"
    },
    "migration": {
        "dry_run": True,
        "limit": 10,
        "default_author_email": "default@example.com"
    }
}

tool = WordPressMigrationTool(config=config)

# Extrair posts do CSV
posts = extract_posts_from_csv('docs/posts_wordpress.csv')

print("Simulando processo completo de migração com verificação de slugs:")
print("=" * 70)

# Simular o processo de migração para verificar slugs
for i, post in enumerate(posts):
    if i >= 10:  # Limitar a 10 posts
        break
        
    original_slug = post.get("Slug") or ""
    
    # Aplicar a sanitização como no migrate_posts
    def _sanitize_slug_func(s: str) -> str:
        s = unicodedata.normalize("NFKD", s)
        s = s.encode("ascii", "ignore").decode("ascii")
        s = s.lower().strip().replace(" ", "-")
        import re as _re
        s = _re.sub(r"[^a-z0-9\\-]", "-", s)
        s = _re.sub(r"-+", "-", s).strip("-")
        return s
    
    sanitized = _sanitize_slug_func(original_slug)
    
    # Verificar se o slug seria atualizado
    if sanitized != original_slug:
        print(f"Post {i+1}:")
        print(f"  Title: {post.get('Title') or 'N/A'}")
        print(f"  Slug original: \"{original_slug}\"")
        print(f"  Slug sanitizado: \"{sanitized}\"")
        print(f"  *** Slug seria atualizado no processo de migração ***")
        # Simular a atualização
        post["Slug"] = sanitized
        print(f"  Slug atualizado no post: \"{post['Slug']}\"")
        print()
    else:
        print(f"Post {i+1}: Slug já sanitizado ou não precisa de sanitização")
        print(f"  Title: {post.get('Title') or 'N/A'}")
        print(f"  Slug: \"{original_slug}\"")
        print()

print("Processo de simulação concluído.")