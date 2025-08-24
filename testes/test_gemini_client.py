#!/usr/bin/env python3
"""
Script para testar o cliente Gemini.
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório 'services' ao path para importar o módulo
sys.path.insert(0, str(Path(__file__).parent / "services"))

from gemini_client import GeminiClient


def test_text_only():
    """Testa a geração de conteúdo com texto apenas."""
    print("--- Teste 1: Texto apenas ---")
    client = GeminiClient()
    try:
        response = client.generate(["Escreva uma frase criativa sobre inteligência artificial."])
        print("Resposta:", response["text"])
        print("Sucesso!\n")
    except Exception as e:
        print(f"Erro: {e}\n")


def test_text_and_image():
    """Testa a geração de conteúdo com texto e imagem."""
    print("--- Teste 2: Texto e Imagem ---")
    # Cria uma imagem de teste simples (quadrado vermelho)
    from PIL import Image
    import io
    import base64

    # Gera uma imagem simples em memória
    img = Image.new('RGB', (100, 100), color = 'red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    client = GeminiClient()
    try:
        response = client.generate([
            "O que tem nesta imagem?",
            img_byte_arr,
        ])
        print("Resposta:", response["text"])
        print("Sucesso!\n")
    except Exception as e:
        print(f"Erro: {e}\n")


def test_streaming():
    """Testa a geração de conteúdo em streaming."""
    print("--- Teste 3: Streaming ---")
    client = GeminiClient()
    try:
        print("Gerando conteúdo em streaming...")
        for chunk in client.generate_stream(["Conte uma história curta sobre um robô aprendendo a cozinhar."]):
            print(chunk, end="", flush=True)
        print("\nStreaming finalizado com sucesso!\n")
    except Exception as e:
        print(f"Erro: {e}\n")


if __name__ == "__main__":
    print("Iniciando testes do GeminiClient...\n")
    test_text_only()
    test_text_and_image()
    test_streaming()
    print("Todos os testes concluídos.")