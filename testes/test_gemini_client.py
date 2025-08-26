"""Script para testar o cliente Gemini."""

import os
import sys
from pathlib import Path

import pytest

# Ajusta path para importar o cliente real
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "agente_ia"))

try:  # pragma: no cover - depende de pacote externo
    from gemini_client import GeminiClient  # type: ignore
except Exception:  # pragma: no cover - ausência de dependências
    GeminiClient = None


@pytest.mark.skipif(GeminiClient is None, reason="GeminiClient não disponível")
def test_gemini_client_instantiation(monkeypatch):
    """Garante que o cliente é instanciado quando dependências existem."""
    monkeypatch.setenv("GOOGLE_API_KEY", "dummy")
    client = GeminiClient()
    assert client.model
