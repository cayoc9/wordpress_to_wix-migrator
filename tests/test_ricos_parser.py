import pytest
from src.parsers.ricos_parser import convert_html_to_ricos

def test_handle_youtube_iframe():
    html = '<iframe src="https://www.youtube.com/embed/12345678901"></iframe>'
    ricos = convert_html_to_ricos(html)
    assert ricos["nodes"][0]["type"] == "html"
    assert 'src="https://www.youtube.com/embed/12345678901"' in ricos["nodes"][0]["data"]["html"]

def test_handle_other_iframe():
    html = '<iframe src="https://www.vimeo.com/123456789"></iframe>'
    ricos = convert_html_to_ricos(html)
    assert ricos["nodes"][0]["type"] == "paragraph"
    assert ricos["nodes"][0]["nodes"][0]["data"]["url"] == "https://www.vimeo.com/123456789"

def test_handle_paragraph():
    html = "<p>Hello, world!</p>"
    ricos = convert_html_to_ricos(html)
    assert ricos["nodes"][0]["type"] == "paragraph"
    assert ricos["nodes"][0]["nodes"][0]["text"] == "Hello, world!"

def test_handle_heading():
    html = "<h1>Title</h1>"
    ricos = convert_html_to_ricos(html)
    assert ricos["nodes"][0]["type"] == "heading"
    assert ricos["nodes"][0]["data"]["level"] == 1
    assert ricos["nodes"][0]["nodes"][0]["text"] == "Title"

def test_handle_ul_list():
    html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
    ricos = convert_html_to_ricos(html)
    assert ricos["nodes"][0]["type"] == "bulleted-list"
    assert len(ricos["nodes"][0]["nodes"]) == 2
    assert ricos["nodes"][0]["nodes"][0]["nodes"][0]["text"] == "Item 1"

def test_handle_ol_list():
    html = "<ol><li>Item 1</li><li>Item 2</li></ol>"
    ricos = convert_html_to_ricos(html)
    assert ricos["nodes"][0]["type"] == "numbered-list"
    assert len(ricos["nodes"][0]["nodes"]) == 2
    assert ricos["nodes"][0]["nodes"][0]["nodes"][0]["text"] == "Item 1"

def test_handle_image():
    html = '<img src="https://example.com/image.jpg" alt="Example image">'
    ricos = convert_html_to_ricos(html)
    assert ricos["nodes"][0]["type"] == "image"
    assert ricos["nodes"][0]["data"]["src"] == "https://example.com/image.jpg"
    assert ricos["nodes"][0]["data"]["alt"] == "Example image"
