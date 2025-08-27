"""
Utilitários de rastreabilidade e dumps de artefatos da migração.

Este módulo fornece helpers simples para:
- Criar um diretório por post (por slug) em `reports/traces/<slug>/`
- Escrever arquivos de texto e JSON nesse diretório
- Registrar eventos estruturados em um arquivo `events.jsonl`

Não há dependências externas; tudo usa a biblioteca padrão.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Callable, Dict, Optional

TRACES_BASE_DIR = os.path.join("reports", "traces")


def _safe_slug(slug: Optional[str]) -> str:
    """Sanitiza o slug para uso como nome de pasta.

    Substitui qualquer caractere não alfanumérico por hífen e normaliza
    sequências para evitar nomes inválidos.
    """
    if not slug:
        return "_no-slug_"
    # Mantém letras, números e hífen. Converte espaços e separadores em hífen.
    s = re.sub(r"[^a-zA-Z0-9\-]+", "-", slug.strip())
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "_no-slug_"


def make_post_trace_dir(slug: Optional[str]) -> str:
    """Garante e retorna o diretório de trace para o slug informado."""
    safe = _safe_slug(slug)
    path = os.path.join(TRACES_BASE_DIR, safe)
    os.makedirs(path, exist_ok=True)
    return path


def write_text(trace_dir: str, filename: str, content: str) -> None:
    """Escreve um arquivo de texto dentro do diretório de trace."""
    path = os.path.join(trace_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content or "")


def write_json(trace_dir: str, filename: str, data: Any) -> None:
    """Escreve um arquivo JSON bonito dentro do diretório de trace."""
    path = os.path.join(trace_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def make_event_logger(trace_dir: str) -> Callable[[Dict[str, Any]], None]:
    """Cria um logger de eventos que anexa linhas JSON em `events.jsonl`.

    Retorna uma função que recebe um dicionário e o persiste como uma linha JSON.
    """
    path = os.path.join(trace_dir, "events.jsonl")

    def _log(ev: Dict[str, Any]) -> None:
        try:
            with open(path, "a", encoding="utf-8") as f:
                json.dump(ev, f, ensure_ascii=False)
                f.write("\n")
        except OSError:
            # Falha de escrita de trace não deve interromper a migração
            pass

    return _log
