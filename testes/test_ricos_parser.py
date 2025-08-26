import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.parsers.ricos_parser import convert_html_to_ricos


def test_paragraph_conversion() -> None:
    html = "<p>Hello world</p>"
    expected = {
        "nodes": [
            {
                "type": "PARAGRAPH",
                "nodes": [
                    {
                        "type": "TEXT",
                        "textData": {"text": "Hello world", "decorations": []},
                    }
                ],
                "paragraphData": {"textStyle": {"textAlignment": "LEFT"}},
            }
        ]
    }
    assert convert_html_to_ricos(html) == expected


def test_heading_conversion() -> None:
    html = "<h2>Heading</h2>"
    expected = {
        "nodes": [
            {
                "type": "HEADING",
                "nodes": [
                    {
                        "type": "TEXT",
                        "textData": {"text": "Heading", "decorations": []},
                    }
                ],
                "headingData": {
                    "level": 2,
                    "textStyle": {"textAlignment": "LEFT"},
                },
            }
        ]
    }
    assert convert_html_to_ricos(html) == expected


def test_nested_list_conversion() -> None:
    html = "<ul><li>Item 1<ul><li>Subitem 1</li></ul></li><li>Item 2</li></ul>"
    result = convert_html_to_ricos(html)
    # Estrutura básica do topo
    assert result["nodes"][0]["type"] == "BULLETED_LIST"
    top_items = result["nodes"][0]["nodes"]
    assert top_items[0]["listItemData"] == {"depth": 0, "indentation": 0}
    # Item aninhado deve ter profundidade 1
    nested_list = top_items[0]["nodes"][1]
    assert nested_list["type"] == "BULLETED_LIST"
    nested_item = nested_list["nodes"][0]
    assert nested_item["listItemData"] == {"depth": 1, "indentation": 1}
    # Texto do subitem deve estar presente
    sub_paragraph = nested_item["nodes"][0]
    text_node = sub_paragraph["nodes"][0]
    assert text_node["textData"]["text"] == "Subitem 1"


def test_image_without_figcaption() -> None:
    def importer(_: str) -> str:
        return "m1"

    html = '<img src="img.png" alt="Alt" width="100" height="200" />'
    expected = {
        "nodes": [
            {
                "type": "IMAGE",
                "nodes": [],
                "imageData": {
                    "containerData": {
                        "width": {"size": "CONTENT"},
                        "alignment": "CENTER",
                    },
                    "image": {
                        "src": {"id": "m1"},
                        "altText": "Alt",
                        "width": 100,
                        "height": 200,
                    },
                },
            }
        ]
    }
    assert convert_html_to_ricos(html, image_importer=importer) == expected


def test_image_with_figcaption() -> None:
    def importer(_: str) -> str:
        return "m1"

    html = '<figure><img src="img.png" alt="Alt"/><figcaption>Caption</figcaption></figure>'
    expected = {
        "nodes": [
            {
                "type": "IMAGE",
                "nodes": [],
                "imageData": {
                    "containerData": {
                        "width": {"size": "CONTENT"},
                        "alignment": "CENTER",
                    },
                    "image": {"src": {"id": "m1"}, "altText": "Alt"},
                },
            },
            {
                "type": "PARAGRAPH",
                "nodes": [
                    {
                        "type": "TEXT",
                        "textData": {"text": "Caption", "decorations": []},
                    }
                ],
                "paragraphData": {"textStyle": {"textAlignment": "CENTER"}},
            },
        ]
    }
    assert convert_html_to_ricos(html, image_importer=importer) == expected


def test_blockquote_conversion() -> None:
    html = "<blockquote><p>Quote here</p></blockquote>"
    expected = {
        "nodes": [
            {
                "type": "BLOCKQUOTE",
                "nodes": [
                    {
                        "type": "PARAGRAPH",
                        "nodes": [
                            {
                                "type": "TEXT",
                                "textData": {
                                    "text": "Quote here",
                                    "decorations": [],
                                },
                            }
                        ],
                        "paragraphData": {"textStyle": {"textAlignment": "LEFT"}},
                    }
                ],
                "blockquoteData": {"indentation": 0},
            }
        ]
    }
    assert convert_html_to_ricos(html) == expected


def test_line_break_conversion() -> None:
    html = "<p>line1<br/>line2</p>"
    expected = {
        "nodes": [
            {
                "type": "PARAGRAPH",
                "nodes": [
                    {
                        "type": "TEXT",
                        "textData": {"text": "line1", "decorations": []},
                    }
                ],
                "paragraphData": {"textStyle": {"textAlignment": "LEFT"}},
            },
            {"type": "LINE_BREAK", "nodes": [], "lineBreakData": {}},
            {
                "type": "PARAGRAPH",
                "nodes": [
                    {
                        "type": "TEXT",
                        "textData": {"text": "line2", "decorations": []},
                    }
                ],
                "paragraphData": {"textStyle": {"textAlignment": "LEFT"}},
            },
        ]
    }
    assert convert_html_to_ricos(html) == expected


def test_horizontal_rule_fallback() -> None:
    html = "<p>before</p><hr/><p>after</p>"
    result = convert_html_to_ricos(html)
    assert result["nodes"][1]["type"] == "HTML"
    assert result["nodes"][1]["htmlData"]["html"] == "<hr/>"
    assert result["nodes"][0]["nodes"][0]["textData"]["text"] == "before"
    assert result["nodes"][2]["nodes"][0]["textData"]["text"] == "after"
