#!/usr/bin/env python3
"""
Mapea todas as tags HTML presentes na coluna "Content" de um arquivo CSV
e exporta um resumo (tag, count) para a pasta "data/".
Quando encontra tags "script", também gera um arquivo detalhado com títulos dos posts.

Uso:
  python scripts/map_html_tags.py \\
    --input docs/Posts-Export-2025-July-25-1838.csv \\
    --column Content \\
    --output data/html_tags_counts.csv

Se os argumentos não forem informados, os padrões acima serão usados.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable, List, Tuple

from bs4 import BeautifulSoup


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mapear tags HTML da coluna de conteúdo em um CSV."
    )
    parser.add_argument(
        "--input",
        default="docs/Posts-Export-2025-July-25-1838.csv",
        help="Caminho do arquivo CSV de entrada",
    )
    parser.add_argument(
        "--column",
        default="Content",
        help="Nome da coluna que contém o HTML (padrão: Content)",
    )
    parser.add_argument(
        "--output",
        default="data/html_tags_counts.csv",
        help="Caminho do arquivo CSV de saída com (tag,count)",
    )
    return parser.parse_args()


def iter_html_rows(csv_path: Path, content_column: str) -> Iterable[Tuple[str, str]]:
    """Itera sobre linhas do CSV, retornando (título, conteúdo HTML)"""
    # Aumenta limite de tamanho de campo para lidar com HTMLs grandes
    try:
        csv.field_size_limit(sys.maxsize)
    except (OverflowError, ValueError):
        # Fallback razoável caso sys.maxsize não seja aceito
        csv.field_size_limit(10_000_000)

    # Usa utf-8-sig para lidar com BOM no cabeçalho se existir
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if content_column not in reader.fieldnames:
            raise SystemExit(
                f"Coluna '{content_column}' não encontrada. Disponíveis: {reader.fieldnames}"
            )
        
        # Determina a coluna de título (procura por variações comuns)
        title_column = None
        for col in reader.fieldnames:
            if col.lower() in ['title', 'titulo', 'título']:
                title_column = col
                break
        
        if not title_column:
            title_column = 'Title'  # Valor padrão
        
        for row in reader:
            title = row.get(title_column, "Título não encontrado")
            content = row.get(content_column) or ""
            if isinstance(content, str) and content.strip():
                yield title, content


def count_html_tags_and_find_scripts(csv_path: Path, content_column: str) -> Tuple[Counter, List[Tuple[str, str]]]:
    """Conta tags HTML e coleta informações sobre tags script"""
    counter: Counter[str] = Counter()
    script_entries: List[Tuple[str, str]] = []  # [(title, script_src), ...]
    
    for title, html in iter_html_rows(csv_path, content_column):
        soup = BeautifulSoup(html, "html.parser")
        for el in soup.find_all(True):  # True encontra quaisquer tags
            counter[el.name] += 1
            
            # Coleta informações de tags script
            if el.name == 'script':
                src = el.get('src', '')
                script_type = el.get('type', 'text/javascript')
                # Adiciona entrada se tiver src ou se for script inline significativo
                if src or (el.string and len(el.string.strip()) > 20):
                    script_entries.append((title, src or '[inline script]'))
    
    return counter, script_entries


def write_counts_csv(counter: Counter, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["tag", "count"])
        for tag, count in sorted(counter.items(), key=lambda x: (-x[1], x[0])):
            writer.writerow([tag, count])


def write_script_details_csv(script_entries: List[Tuple[str, str]], out_path: Path) -> None:
    """Escreve detalhes das tags script em um arquivo CSV"""
    script_details_path = out_path.with_name(out_path.stem + '_script_details.csv')
    script_details_path.parent.mkdir(parents=True, exist_ok=True)
    
    with script_details_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "script_src"])
        for title, src in script_entries:
            writer.writerow([title, src])
    
    print(f"Detalhes de scripts salvos em: {script_details_path}")


def main() -> None:
    args = parse_args()
    in_path = Path(args.input)
    out_path = Path(args.output)

    if not in_path.exists():
        raise SystemExit(f"Arquivo de entrada não encontrado: {in_path}")

    counts, script_entries = count_html_tags_and_find_scripts(in_path, args.column)
    write_counts_csv(counts, out_path)
    
    # Se encontrou tags script, gera arquivo detalhado
    if script_entries:
        write_script_details_csv(script_entries, out_path)
    
    print(f"Tags únicas: {len(counts)}")
    print(f"Tags 'script' encontradas: {counts.get('script', 0)}")
    print(f"Arquivo gerado: {out_path}")


if __name__ == "__main__":
    main()
