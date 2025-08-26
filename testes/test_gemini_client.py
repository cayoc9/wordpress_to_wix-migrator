import sys
import pytest
import types
import pathlib

from types import SimpleNamespace

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

# --- dummy google-genai modules to avoid external dependency ---

class DummyPart:
    @staticmethod
    def from_bytes(data, mime_type):
        return {"data": data, "mime_type": mime_type}

    @staticmethod
    def from_uri(file_uri, mime_type):
        return {"uri": file_uri, "mime_type": mime_type}

class DummyModels:
    def __init__(self):
        self.called_with = None

    def generate_content(self, model, contents):
        self.called_with = (model, contents)
        return SimpleNamespace(text="dummy-text")

    def generate_content_stream(self, model, contents):
        self.called_with = (model, contents)
        yield SimpleNamespace(text="chunk1")
        yield SimpleNamespace(text="chunk2")

class DummyClient:
    def __init__(self, api_key, http_options=None):
        self.api_key = api_key
        self.http_options = http_options
        self.models = DummyModels()

# Monta estrutura de módulos simulados
google_module = types.ModuleType("google")
google_genai_module = types.ModuleType("google.genai")
google_genai_types_module = types.ModuleType("google.genai.types")

google_genai_types_module.Part = DummyPart
google_genai_module.Client = DummyClient
google_genai_module.types = google_genai_types_module
google_module.genai = google_genai_module

sys.modules["google"] = google_module
sys.modules["google.genai"] = google_genai_module
sys.modules["google.genai.types"] = google_genai_types_module

from services.agente_ia.gemini_client import GeminiClient


def test_generate_builds_contents_and_returns_text():
    client = GeminiClient(api_key="test-key")
    data = b"binary-data"
    result = client.generate(["hello", data])

    assert result["text"] == "dummy-text"
    model_used, contents_used = client.client.models.called_with
    assert model_used == client.model
    assert contents_used[0] == "hello"
    assert contents_used[1]["mime_type"] == "image/jpeg"


def test_generate_stream_yields_chunks_in_order():
    client = GeminiClient(api_key="test-key")
    chunks = list(client.generate_stream(["hi"]))

    assert chunks == ["chunk1", "chunk2"]
    model_used, contents_used = client.client.models.called_with
    assert model_used == client.model
    assert contents_used == ["hi"]


def test_build_contents_unsupported_type_raises():
    client = GeminiClient(api_key="test-key")
    with pytest.raises(TypeError):
        client._build_contents([123])
