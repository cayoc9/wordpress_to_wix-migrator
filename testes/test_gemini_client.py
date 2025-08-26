import os

import pytest

pytest.importorskip("google.genai")

from services.agente_ia.gemini_client import GeminiClient


def test_init_without_api_key(monkeypatch):
    """Deve falhar se a chave da API não estiver configurada."""
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(ValueError):
        GeminiClient()

