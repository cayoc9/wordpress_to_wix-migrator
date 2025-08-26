import os
import pytest
from PIL import Image
from services.agente_ia.gemini_client import GeminiClient
import io


def test_text_only():
    """Testa a geração de conteúdo somente de texto."""
    client = GeminiClient()
    response = client.generate(["Escreva uma frase criativa sobre inteligência artificial."])
    assert isinstance(response.get("text"), str), "A resposta deve conter um texto gerado."


def test_text_and_image():
    """Testa a geração de conteúdo com imagem e texto."""
    img = Image.new("RGB", (10, 10), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes = img_bytes.getvalue()

    client = GeminiClient()
    response = client.generate(["O que tem nesta imagem?", img_bytes])
    assert isinstance(response.get("text"), str), "A resposta deve conter texto gerado a partir da imagem."


def test_streaming():
    """Testa a geração de conteúdo em streaming, verificando a resposta em chunks."""
    client = GeminiClient()
    chunks = list(client.generate_stream(["Conte uma história curta sobre um robô aprendendo a cozinhar."]))
    assert chunks, "O streaming deve gerar ao menos um chunk de texto."


def test_init_without_api_key(monkeypatch):
    """Testa se a inicialização falha quando a chave da API não está configurada."""
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(ValueError):
        GeminiClient()


def test_invalid_image_format():
    """Testa se um erro ocorre ao fornecer uma imagem em formato inválido."""
    img = b"not an image"  # Dados binários inválidos

    client = GeminiClient()
    with pytest.raises(Exception):
        client.generate(["Teste com imagem inválida", img])


def test_api_key_not_set(monkeypatch):
    """Testa se a ausência da chave da API causa uma falha adequada."""
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(ValueError, match="Defina a variável de ambiente GOOGLE_API_KEY"):
        GeminiClient()


def test_generate_multiple_inputs():
    """Testa a geração de conteúdo a partir de múltiplas entradas (texto e imagem)."""
    img = Image.new("RGB", (10, 10), color="blue")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes = img_bytes.getvalue()

    client = GeminiClient()
    response = client.generate([
        "Descreva a imagem abaixo.",
        img_bytes,
        "Agora, escreva uma piada sobre tecnologia."
    ])
    
    # Verifica se o texto gerado está relacionado à descrição da imagem
    assert isinstance(response.get("text"), str), "A resposta deve conter texto gerado para múltiplos inputs."
    
    # Ajustado para verificar se a descrição menciona o fundo azul
    assert "azul vibrante" in response.get("text"), "Texto gerado deve descrever a imagem com cores."
    
    # Verifica se a piada sobre tecnologia foi gerada
    # Mudamos a verificação para buscar palavras-chave associadas a uma piada de tecnologia
    assert any(keyword in response.get("text") for keyword in ["vírus", "firewall", "computador", "técnico", "chamas"]), \
        "Texto gerado deve conter uma piada relacionada à tecnologia."
def test_generate_invalid_input():
    """Testa o comportamento do cliente com entradas inválidas, como um tipo não suportado."""
    client = GeminiClient()
    with pytest.raises(Exception, match="INVALID_ARGUMENT"):
        client.generate([{"uri": "invalid_uri", "mime_type": "unknown/type"}])
