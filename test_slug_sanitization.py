#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unicodedata
import re

def _sanitize_slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower().strip().replace(" ", "-")
    s = re.sub(r"[^a-z0-9\-]", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s

# Test cases
test_cases = [
    "café",
    "música-e-álbum",
    "teste de slug",
    "Café & Música",
    "ação-e-reação",
    "número-único",
    "título-com-caracteres-especiais-!@#$%",
    "slug-com---muitos---hífens",
    "  espaços no início e fim  ",
    "simple-slug"
]

print("Testando a função _sanitize_slug:")
print("=" * 50)

for test in test_cases:
    sanitized = _sanitize_slug(test)
    print(f"Original: '{test}'")
    print(f"Sanitizado: '{sanitized}'")
    print("-" * 30)