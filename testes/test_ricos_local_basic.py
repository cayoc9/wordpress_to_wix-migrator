import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
pytest.importorskip("bs4")

from src.parsers.ricos_local import convert_html_to_ricos_local


def nodes_of_type(doc, t):
    return [n for n in doc.get("nodes", []) if n.get("type") == t]


def test_paragraph_and_heading_and_link():
    html = """
    <h2>Title</h2>
    <p>Hello <strong>world</strong> <a href="https://ex.com">link</a>.</p>
    """
    doc = convert_html_to_ricos_local(html)
    hs = nodes_of_type(doc, "HEADING")
    ps = nodes_of_type(doc, "PARAGRAPH")
    assert len(hs) == 1 and hs[0]["level"] == 2
    assert len(ps) >= 1
    # Paragraph must contain TEXT nodes
    texts = ps[0]["nodes"]
    assert any(t.get("type") == "TEXT" for t in texts)
    # Link decoration present on some text
    assert any(
        any(d.get("type") == "LINK" for d in (t.get("decorations") or []))
        for t in texts if t.get("type") == "TEXT"
    )


def test_list_and_blockquote_and_divider():
    html = """
    <ul><li>um</li><li>dois</li></ul>
    <blockquote>frase</blockquote>
    <hr/>
    """
    doc = convert_html_to_ricos_local(html)
    blists = nodes_of_type(doc, "BULLETED_LIST")
    assert len(blists) == 1
    assert all(item.get("type") == "LIST_ITEM" for item in blists[0]["nodes"])
    bq = nodes_of_type(doc, "BLOCKQUOTE")
    assert len(bq) == 1
    dv = nodes_of_type(doc, "DIVIDER")
    assert len(dv) == 1


def test_code_block_and_image_placeholder():
    html = """
    <pre><code>line1\nline2</code></pre>
    <p><img src="http://ex.com/a.jpg" alt="A"/></p>
    """
    doc = convert_html_to_ricos_local(html)
    codes = nodes_of_type(doc, "CODE_BLOCK")
    assert len(codes) == 1
    ps = nodes_of_type(doc, "PARAGRAPH")
    assert any("Imagem:" in (t.get("text") or "") for p in ps for t in p.get("nodes", []))


def test_table_as_html_node():
    html = """
    <table><tr><td>A</td><td>B</td></tr></table>
    """
    doc = convert_html_to_ricos_local(html, table_mode="html")
    html_nodes = nodes_of_type(doc, "HTML")
    assert len(html_nodes) == 1
    assert "<table" in html_nodes[0].get("data", {}).get("html", "")
