import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
pytest.importorskip("bs4")

from src.parsers.ricos_local import convert_html_to_ricos_local


def test_table_as_plugin_simple():
    html = """
    <table>
      <tr><th>H1</th><th>H2</th></tr>
      <tr><td>A</td><td>B</td></tr>
    </table>
    """
    doc = convert_html_to_ricos_local(html, table_mode="plugin")
    tables = [n for n in doc.get("nodes", []) if n.get("type") == "TABLE"]
    assert len(tables) == 1
    data = tables[0].get("data", {})
    assert isinstance(data.get("rows"), list)
    assert data.get("headerRows") in (0, 1)

