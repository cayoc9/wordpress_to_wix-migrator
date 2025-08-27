import pytest
from src.parsers.ricos_parser import convert_html_to_ricos
from src.parsers.handlers.utils import extract_video_info

# --- Testes para a função extract_video_info ---

@pytest.mark.parametrize("url, expected", [
    # YouTube URLs
    ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", {"platform": "youtube", "id": "dQw4w9WgXcQ"}),
    ("https://www.youtube.com/embed/dQw4w9WgXcQ", {"platform": "youtube", "id": "dQw4w9WgXcQ"}),
    ("https://youtu.be/dQw4w9WgXcQ", {"platform": "youtube", "id": "dQw4w9WgXcQ"}),
    
    # Vimeo URLs
    ("https://vimeo.com/123456789", {"platform": "vimeo", "id": "123456789"}),
    ("https://www.vimeo.com/123456789", {"platform": "vimeo", "id": "123456789"}),
    ("https://vimeo.com/embed/123456789", {"platform": "vimeo", "id": "123456789"}),
    
    # Invalid URLs
    ("https://example.com", None),
    ("", None),
    (None, None),
])
def test_extract_video_info(url, expected):
    """Testa a função extract_video_info com várias URLs."""
    result = extract_video_info(url)
    assert result == expected

# --- Testes para o iframe_handler ---

# URLs de exemplo para testes parametrizados
YOUTUBE_URLS = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://www.youtube.com/embed/dQw4w9WgXcQ",
    "https://youtu.be/dQw4w9WgXcQ"
]

VIMEO_URLS = [
    "https://vimeo.com/123456789",
    "https://www.vimeo.com/123456789",
    "https://vimeo.com/embed/123456789"
]

@pytest.mark.parametrize("youtube_url", YOUTUBE_URLS)
def test_handle_youtube_iframe_native(youtube_url):
    """Testa a estratégia NATIVE para iframes do YouTube."""
    html = f'<iframe src="{youtube_url}"></iframe>'
    ricos = convert_html_to_ricos(html, embed_strategy="NATIVE")
    
    assert ricos["nodes"][0]["type"] == "video"
    assert ricos["nodes"][0]["data"]["videoId"] == "dQw4w9WgXcQ"
    assert ricos["nodes"][0]["data"]["provider"] == "YOUTUBE"

@pytest.mark.parametrize("youtube_url", YOUTUBE_URLS)
def test_handle_youtube_iframe_html(youtube_url):
    """Testa a estratégia HTML para iframes do YouTube."""
    html = f'<iframe src="{youtube_url}"></iframe>'
    ricos = convert_html_to_ricos(html, embed_strategy="HTML")
    
    assert ricos["nodes"][0]["type"] == "html"
    assert 'src="https://www.youtube.com/embed/dQw4w9WgXcQ"' in ricos["nodes"][0]["data"]["html"]

@pytest.mark.parametrize("youtube_url", YOUTUBE_URLS)
def test_handle_youtube_iframe_link(youtube_url):
    """Testa a estratégia LINK para iframes do YouTube."""
    html = f'<iframe src="{youtube_url}"></iframe>'
    ricos = convert_html_to_ricos(html, embed_strategy="LINK")
    
    assert ricos["nodes"][0]["type"] == "paragraph"
    assert ricos["nodes"][0]["nodes"][0]["text"] == "▶ "
    assert ricos["nodes"][0]["nodes"][1]["type"] == "link"
    assert ricos["nodes"][0]["nodes"][1]["data"]["url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert ricos["nodes"][0]["nodes"][1]["nodes"][0]["text"] == "Assistir no YouTube"

@pytest.mark.parametrize("vimeo_url", VIMEO_URLS)
def test_handle_vimeo_iframe_native(vimeo_url):
    """Testa a estratégia NATIVE para iframes do Vimeo."""
    html = f'<iframe src="{vimeo_url}"></iframe>'
    ricos = convert_html_to_ricos(html, embed_strategy="NATIVE")
    
    assert ricos["nodes"][0]["type"] == "video"
    assert ricos["nodes"][0]["data"]["videoId"] == "123456789"
    assert ricos["nodes"][0]["data"]["provider"] == "VIMEO"

@pytest.mark.parametrize("vimeo_url", VIMEO_URLS)
def test_handle_vimeo_iframe_html(vimeo_url):
    """Testa a estratégia HTML para iframes do Vimeo."""
    html = f'<iframe src="{vimeo_url}"></iframe>'
    ricos = convert_html_to_ricos(html, embed_strategy="HTML")
    
    assert ricos["nodes"][0]["type"] == "html"
    assert 'src="https://player.vimeo.com/video/123456789"' in ricos["nodes"][0]["data"]["html"]

@pytest.mark.parametrize("vimeo_url", VIMEO_URLS)
def test_handle_vimeo_iframe_link(vimeo_url):
    """Testa a estratégia LINK para iframes do Vimeo."""
    html = f'<iframe src="{vimeo_url}"></iframe>'
    ricos = convert_html_to_ricos(html, embed_strategy="LINK")
    
    assert ricos["nodes"][0]["type"] == "paragraph"
    assert ricos["nodes"][0]["nodes"][0]["text"] == "▶ "
    assert ricos["nodes"][0]["nodes"][1]["type"] == "link"
    assert ricos["nodes"][0]["nodes"][1]["data"]["url"] == "https://vimeo.com/123456789"
    assert ricos["nodes"][0]["nodes"][1]["nodes"][0]["text"] == "Assistir no Vimeo"

def test_handle_other_iframe_html():
    """Testa a estratégia HTML para iframes não reconhecidos."""
    html = '<iframe src="https://www.example.com/video"></iframe>'
    ricos = convert_html_to_ricos(html, embed_strategy="HTML")
    
    # Deve cair no fallback de link
    assert ricos["nodes"][0]["type"] == "paragraph"
    assert ricos["nodes"][0]["nodes"][0]["type"] == "link"
    assert ricos["nodes"][0]["nodes"][0]["data"]["url"] == "https://www.example.com/video"

def test_handle_other_iframe_link():
    """Testa a estratégia LINK para iframes não reconhecidos."""
    html = '<iframe src="https://www.example.com/video"></iframe>'
    ricos = convert_html_to_ricos(html, embed_strategy="LINK")
    
    # Deve cair no fallback de link
    assert ricos["nodes"][0]["type"] == "paragraph"
    assert ricos["nodes"][0]["nodes"][0]["type"] == "link"
    assert ricos["nodes"][0]["nodes"][0]["data"]["url"] == "https://www.example.com/video"

