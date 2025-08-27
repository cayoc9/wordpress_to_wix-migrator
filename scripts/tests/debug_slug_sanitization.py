#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
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

# Extrair posts do CSV
posts = extract_posts_from_csv('docs/posts_wordpress.csv')

print("Verificando a sanitização de slugs no processo de migração:")
print("=" * 60)

# Verificar os primeiros 10 posts
for i, post in enumerate(posts[:10]):
    slug = post.get("Slug") or ""
    sanitized = _sanitize_slug(slug)
    
    print(f"Post {i+1}:")
    print(f"  Title: {post.get('Title')}")
    print(f"  Slug original: \"{slug}\"")
    print(f"  Slug sanitizado: \"{sanitized}\"")
    
    if sanitized != slug:
        print(f"  *** DIFERENÇA IDENTIFICADA ***")
    print()