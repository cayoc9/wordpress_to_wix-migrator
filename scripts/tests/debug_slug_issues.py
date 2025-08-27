#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

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

# Testar com slugs que contenham underscores (como vimos no CSV)
test_cases = [
    "regismes_tributarios_no_brasil_simples_lucro_real_lucro_presumido",
    "reforma_tributaria_brasil",
    "café_com_música",
    "ação_&_reação",
    "número_único",
    "título_com_caracteres_especiais_!@#$%"
]

print("Testando sanitização de slugs com underscores e outros caracteres:")
print("=" * 70)

for slug in test_cases:
    sanitized = _sanitize_slug(slug)
    print(f"Original: \"{slug}\"")
    print(f"Sanitizado: \"{sanitized}\"")
    
    if sanitized != slug:
        print("*** DIFERENÇA IDENTIFICADA ***")
    print()

# Agora vamos verificar se há algum log no arquivo de migração
print("\nVerificando logs de migração para identificar slugs sanitizados:")
print("=" * 70)

# Verificar se há logs de sanitização no arquivo de log
try:
    with open("reports/migration/migration.log", "r", encoding="utf-8") as f:
        logs = f.read()
        if "Slug sanitizado" in logs:
            print("Encontrados logs de sanitização de slugs:")
            # Procurar as últimas 5 linhas com "Slug sanitizado"
            lines = logs.split("\n")
            sanitized_logs = [line for line in lines if "Slug sanitizado" in line]
            for log in sanitized_logs[-5:]:  # Mostrar as últimas 5
                print(f"  {log}")
        else:
            print("Nenhum log de sanitização de slugs encontrado.")
except FileNotFoundError:
    print("Arquivo de log não encontrado.")
except Exception as e:
    print(f"Erro ao ler o arquivo de log: {e}")