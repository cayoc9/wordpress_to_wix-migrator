#!/usr/bin/env python3
"""Tests for Gemini client.

This module exercises the ``GeminiClient`` when available.  If the
client cannot be imported (e.g., optional dependency missing), the
entire test module is skipped.
"""

import sys
from pathlib import Path
import os
import io
from PIL import Image

import pytest

sys.path.insert(0, str(Path(__file__).parent / "services"))

pytest.importorskip("google.genai")

try:  # pragma: no cover - optional dependency
    from services.agente_ia.gemini_client import GeminiClient
except Exception:  # Module not available, skip tests
    pytest.skip("gemini_client not available", allow_module_level=True)


def test_text_only():
    client = GeminiClient()
    response = client.generate(["Escreva uma frase criativa sobre inteligência artificial."])
    assert isinstance(response.get("text"), str)


def test_text_and_image():
    img = Image.new("RGB", (10, 10), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes = img_bytes.getvalue()

    client = GeminiClient()
    response = client.generate(["O que tem nesta imagem?", img_bytes])
    assert isinstance(response.get("text"), str)


def test_streaming():
    client = GeminiClient()
    chunks = list(client.generate_stream(["Conte uma história curta sobre um robô aprendendo a cozinhar."]))
    assert chunks  # Should yield at least one chunk


def test_init_without_api_key(monkeypatch):
    """Deve falhar se a chave da API não estiver configurada."""
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(ValueError):
        GeminiClient()