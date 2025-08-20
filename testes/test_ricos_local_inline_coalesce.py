import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
pytest.importorskip("bs4")

from src.parsers.ricos_local import convert_html_to_ricos_local


def test_top_level_inline_siblings_coalesce_into_one_paragraph():
    html = '<span>Olá</span> <a href="https://x">mundo</a> <span>!</span>'
    doc = convert_html_to_ricos_local(html)
    nodes = doc.get("nodes", [])
    # Expect a single paragraph containing all three pieces
    assert len(nodes) == 1 and nodes[0]["type"] == "PARAGRAPH"
    full_text = "".join(t.get("text", "") for t in nodes[0]["nodes"] if t.get("type") == "TEXT")
    assert "Olá" in full_text and "mundo" in full_text and "!" in full_text


def test_top_level_img_becomes_image_block_when_importer_available():
    html = '<img src="http://ex.com/a.jpg" alt="Cap"/>'
    doc = convert_html_to_ricos_local(html, image_importer=lambda url: "mid-1")
    types = [n.get("type") for n in doc.get("nodes", [])]
    assert "IMAGE" in types

