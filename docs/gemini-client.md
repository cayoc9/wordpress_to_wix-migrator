# Cliente Gemini (Google Gen AI)

Este projeto inclui um cliente Python para o Gemini API, focado em geração multimodal (texto + imagens), em `services/gemini_client.py`.

## Instalação

1) Dependências (no virtualenv do projeto):

```
pip install -r requirements.txt
```

2) Configure a chave da API do Google AI Studio (Developer API):

```
export GOOGLE_API_KEY="SUA_CHAVE_AQUI"
```

## Modelos recomendados

- Texto/Multimodal (geral): `gemini-2.5-flash`
- Raciocínio/código: `gemini-2.5-pro`

Fonte: Google Gen AI SDK (python-genai).

## Uso rápido

```python
from services.gemini_client import GeminiClient

client = GeminiClient()  # usa GOOGLE_API_KEY do ambiente

# Geração não-streaming (texto + imagem local)
result = client.generate([
    "Descreva a imagem em 1 frase:",
    "./exemplos/exemplo.jpg",
])
print(result["text"])  # texto gerado

# Geração em streaming
for chunk in client.generate_stream([
    "Explique a cena:",
    "./exemplos/exemplo.jpg",
]):
    print(chunk, end="")

# Também aceita bytes de imagem, PIL.Image.Image, e URIs GCS:
# client.generate([{"uri": "gs://bucket/imagem.jpg", "mime_type": "image/jpeg"}, "Pergunta..."])
```

## Notas

- `Pillow` é opcional, mas habilita enviar `PIL.Image.Image` diretamente.
- Para conteúdos apenas de texto, basta passar strings na lista de `inputs`.
- Para arquivos locais, o cliente detecta MIME automaticamente com `mimetypes`.

