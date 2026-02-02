#!/usr/bin/env python3
"""
Extrai todas as tags do CSV de export do WordPress, normaliza os rótulos
e exporta um JSON compatível com a API de Tags do Wix Blog (createTag).

Uso:
  python scripts/extract_tags_to_wix_json.py \
    --input docs/Posts-Export-2025-July-25-1838.csv \
    --output data/tags_wix.json \
    --language pt-BR

Saída (exemplo simplificado):
{
  "generated_at": "2025-08-20T15:04:05Z",
  "source_file": "docs/Posts-Export-2025-July-25-1838.csv",
  "site_language": "pt-BR",
  "tags": [
    {"label": "Cartões de crédito", "slug": "cartoes-de-credito", "language": "pt-BR", "id": null}
  ]
}

Observações:
- O campo "label" é usado diretamente no POST para criar a tag no Wix.
- O campo "slug" é opcional (o Wix pode gerar a partir do label). Mantemos pré-calculado para auditoria.
- O campo "id" começa nulo e será preenchido por scripts que criarem as tags via REST e derem update neste JSON.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Set

# Permite importar src/ quando executado como script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.tags import parse_tags_field  # type: ignore  # reaproveita normalização já existente


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extrair e normalizar tags do CSV e gerar JSON para Wix Blog Tags API.",
    )
    parser.add_argument(
        "--input",
        default="docs/Posts-Export-2025-July-25-1838.csv",
        help="Caminho do arquivo CSV de entrada (export do WordPress)",
    )
    parser.add_argument(
        "--output",
        default="data/tags_wix.json",
        help="Caminho do arquivo JSON de saída",
    )
    parser.add_argument(
        "--language",
        default="pt-BR",
        help="Código de idioma BCP-47 para as tags (ex: pt-BR)",
    )
    parser.add_argument(
        "--tags-column",
        default="Tags",
        help="Nome da coluna que contém as tags no CSV (padrão: Tags)",
    )
    return parser.parse_args()


def iter_csv_rows(csv_path: Path) -> Iterable[dict]:
    """Itera as linhas do CSV com ajuste de limite e BOM utf-8-sig."""
    try:
        csv.field_size_limit(sys.maxsize)
    except (OverflowError, ValueError):
        csv.field_size_limit(10_000_000)

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise SystemExit("Cabeçalho do CSV não encontrado.")
        for row in reader:
            yield row


def slugify(value: str) -> str:
    """Gera um slug previsível: minúsculo, sem acento, separador '-'."""
    value = value.strip().lower()
    # remove acentos
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    # substitui não alfanumérico por '-'
    out = []
    prev_dash = False
    for ch in value:
        if ch.isalnum():
            out.append(ch)
            prev_dash = False
        else:
            if not prev_dash:
                out.append("-")
                prev_dash = True
    slug = "".join(out).strip("-")
    return slug


def main() -> None:
    args = parse_args()
    in_path = Path(args.input)
    out_path = Path(args.output)
    language = args.language
    tags_column = args.tags_column

    if not in_path.exists():
        raise SystemExit(f"Arquivo de entrada não encontrado: {in_path}")

    unique_labels: List[str] = []
    seen: Set[str] = set()  # dedupe casefold

    for row in iter_csv_rows(in_path):
        raw_field = row.get(tags_column) or ""
        labels = parse_tags_field(raw_field)
        for label in labels:
            key = label.casefold()
            if key not in seen:
                seen.add(key)
                unique_labels.append(label)

    tags_payload = [
        {
            "label": label,
            "slug": slugify(label) if label else None,
            "language": language,
            "id": None,
        }
        for label in unique_labels
        if label
    ]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_file": str(in_path),
        "site_language": language,
        "count": len(tags_payload),
        "tags": tags_payload,
    }
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)

    print(f"Tags únicas: {len(tags_payload)}")
    print(f"Arquivo gerado: {out_path}")


if __name__ == "__main__":
    main()
