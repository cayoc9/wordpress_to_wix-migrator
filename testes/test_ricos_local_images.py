import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
pytest.importorskip("bs4")

from src.parsers.ricos_local import convert_html_to_ricos_local


def test_image_importer_produces_image_node():
    html = '<p>Foto: <img src="http://ex.com/img.jpg" alt="Legenda" /></p>'

    def fake_importer(url: str):
        assert url == "http://ex.com/img.jpg"
        return "media-123"

    doc = convert_html_to_ricos_local(html, image_importer=fake_importer)
    # Expect a paragraph (for "Foto:") and an IMAGE node
    types = [n.get("type") for n in doc.get("nodes", [])]
    assert "PARAGRAPH" in types
    assert "IMAGE" in types
    img = next(n for n in doc["nodes"] if n.get("type") == "IMAGE")
    assert img.get("data", {}).get("src", {}).get("id") == "media-123"

