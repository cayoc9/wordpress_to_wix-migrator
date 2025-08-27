import pytest
from src.parsers.ricos_parser import convert_html_to_ricos
from src.parsers.handlers.utils import extract_video_info
from src.parsers.shortcode_parser import parse_shortcodes

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

# --- Testes para o shortcode_parser ---

class TestShortcodeParsing:
    """Testes para o novo parser de shortcodes."""

    def test_button_shortcode_basic(self):
        """Testa o shortcode [button] básico."""
        html = '[button href="https://example.com"]Click Me[/button]'
        expected = '<a href="https://example.com" target="_self" class="wp-block-button__link">Click Me</a>'
        result = parse_shortcodes(html)
        assert expected in result

    def test_button_shortcode_with_target(self):
        """Testa o shortcode [button] com atributo target."""
        html = '[button href="https://example.com" target="_blank"]Click Me[/button]'
        expected = '<a href="https://example.com" target="_blank" class="wp-block-button__link">Click Me</a>'
        result = parse_shortcodes(html)
        assert expected in result

    def test_embed_shortcode_youtube(self):
        """Testa o shortcode [embed] com URL do YouTube."""
        html = '[embed]https://www.youtube.com/watch?v=dQw4w9WgXcQ[/embed]'
        expected = '<iframe src="https://www.youtube.com/watch?v=dQw4w9WgXcQ"></iframe>'
        result = parse_shortcodes(html)
        assert expected in result

    def test_unknown_shortcode_ignored(self):
        """Testa se shortcodes desconhecidos são ignorados."""
        html = 'Texto antes [unknown_shortcode]Conteúdo[/unknown_shortcode] texto depois.'
        expected = html  # Deve permanecer inalterado
        result = parse_shortcodes(html)
        assert result == expected

    def test_combined_shortcodes_and_html(self):
        """Testa a integração de múltiplos shortcodes e HTML normal."""
        html = """
        <p>Texto normal antes.</p>
        [button href="https://example.com"]Botão[/button]
        <p>Mais texto normal.</p>
        [caption id="attachment_100" align="aligncenter" width="300"]<img src="image.jpg" alt="Imagem" /> Legenda da Imagem[/caption]
        <p>Texto final.</p>
        """
        # Chama o conversor principal que lida com todos os pré-processadores
        ricos_result = convert_html_to_ricos(html)

        # Verifica se o nó de parágrafo com o botão foi criado
        # Esperamos 5 nós: p, p(a), p, figure(html), p
        assert len(ricos_result["nodes"]) == 5, f"Esperado 5 nós, mas obteve {len(ricos_result['nodes'])}"

        # 1. Parágrafo inicial
        assert ricos_result["nodes"][0]["type"] == "PARAGRAPH"
        assert "Texto normal antes." in ricos_result["nodes"][0]["nodes"][0]["textData"]["text"]

        # 2. Botão (convertido para link em um parágrafo)
        button_node = ricos_result["nodes"][1]
        assert button_node["type"] == "PARAGRAPH"
        assert button_node["nodes"][0]["type"] == "LINK"
        assert button_node["nodes"][0]["linkData"]["url"] == "https://example.com"
        assert button_node["nodes"][0]["nodes"][0]["textData"]["text"] == "Botão"
        
        # 3. Segundo parágrafo
        assert ricos_result["nodes"][2]["type"] == "PARAGRAPH"
        assert "Mais texto normal." in ricos_result["nodes"][2]["nodes"][0]["textData"]["text"]

        # 4. Legenda (convertida para nó HTML)
        assert ricos_result["nodes"][3]["type"] == "HTML"
        assert '<figure class="wp-caption">' in ricos_result["nodes"][3]["htmlData"]["html"]
        
        # 5. Parágrafo final
        assert ricos_result["nodes"][4]["type"] == "PARAGRAPH"
        assert "Texto final." in ricos_result["nodes"][4]["nodes"][0]["textData"]["text"]