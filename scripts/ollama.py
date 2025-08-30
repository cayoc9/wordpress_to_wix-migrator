import base64, json, requests, tempfile, urllib.request
import pandas as pd

OLLAMA = "http://192.168.1.9:11434"

def ollama_generate(model, prompt, fmt=None, temperature=0.2, system=None):
    payload = {"model": model, "prompt": prompt, "options": {"temperature": temperature}, "stream": False}
    if fmt: payload["format"] = fmt
    if system: payload["system"] = system
    r = requests.post(f"{OLLAMA}/api/generate", json=payload, timeout=120)

    # Verifique se o conteúdo é um JSON válido
    try:
        return r.json()["response"]
    except json.decoder.JSONDecodeError as e:
        print("Erro ao decodificar JSON:", e)
        print("Resposta completa:", r.text)  # Mostrar a resposta completa para depuração
        raise


def ollama_chat_vision(model, prompt, image_url):
    import os
    try:
        # baixa a imagem usando delete=False para evitar conflitos de permissão
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            temp_file_path = f.name
            urllib.request.urlretrieve(image_url, temp_file_path)
        
        # carrega base64 após fechar o arquivo temporário
        with open(temp_file_path, "rb") as img_file:
            b64 = base64.b64encode(img_file.read()).decode()
        
        # remove arquivo temporário manualmente
        os.unlink(temp_file_path)
        payload = {"model": model, "messages":[{"role":"user","content":prompt,"images":[b64]}],
                    "options":{"temperature":0.2}, "stream": False}
        r = requests.post(f"{OLLAMA}/api/chat", json=payload, timeout=120)
        r.raise_for_status()
        
        print(f"DEBUG: Resposta da API de visão: {repr(r.text)}")
        
        # Parse robusto da resposta JSON da API chat
        try:
            response_data = r.json()
            print(f"DEBUG: JSON da API de visão parseado: {response_data}")
            return response_data["message"]["content"]
        except json.JSONDecodeError as e:
            print(f"DEBUG: Erro JSON na API de visão: {e}")
            print(f"DEBUG: Tentando parsing robusto...")
            
            # Mesmo sistema de parsing robusto
            import re
            json_match = re.search(r'\{.*\}', r.text, re.DOTALL)
            if json_match:
                try:
                    response_data = json.loads(json_match.group())
                    print(f"DEBUG: JSON extraído com sucesso da API de visão")
                    return response_data.get("message", {}).get("content", "")
                except json.JSONDecodeError:
                    print(f"DEBUG: Falha no parsing robusto da API de visão")
                    return ""
            return ""
    except urllib.error.HTTPError as e:
        print(f"AVISO: Não foi possível baixar a imagem de {image_url}. Erro: {e}")
        return ""
    except Exception as e:
        print(f"AVISO: Ocorreu um erro inesperado ao processar a imagem {image_url}. Erro: {e}")
        return ""

def generate_excerpt_meta_pt(title, text):
    system_prompt = """Você é um assistente de SEO especialista em português do Brasil. 

REGRAS OBRIGATÓRIAS:
1. Retorne SOMENTE um objeto JSON válido com as chaves "excerpt" e "metaDescription"
2. Não adicione texto explicativo, markdown ou comentários
3. O excerpt deve ter 40-60 palavras, ser persuasivo e não repetir o título
4. A metaDescription deve ter no máximo 160 caracteres, ser otimizada para SEO e não conter aspas

FORMATO EXATO:
{
  "excerpt": "texto aqui",
  "metaDescription": "texto aqui"
}"""
    
    prompt = f"""TÍTULO: {title}

CONTEÚDO: {text}"""
    try:
        print(f"DEBUG: Enviando prompt para o título '{title}'...")
        resp = ollama_generate("qwen2.5:7b-instruct", prompt, fmt="json", temperature=0.2, system=system_prompt)
        print(f"DEBUG: Resposta bruta do Ollama: {repr(resp)}")
        
        # Tenta extrair JSON válido da resposta
        data = None
        
        # Estratégia 1: JSON direto
        try:
            data = json.loads(resp)
            print(f"DEBUG: JSON parseado com sucesso (estratégia 1)")
        except json.JSONDecodeError:
            # Estratégia 2: Procurar por JSON entre chaves
            import re
            json_match = re.search(r'\{.*\}', resp, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                    print(f"DEBUG: JSON extraído com sucesso (estratégia 2)")
                except json.JSONDecodeError:
                    pass
            
            # Estratégia 3: Pegar apenas a primeira linha se múltiplas
            if data is None:
                lines = resp.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('{') and line.endswith('}'):
                        try:
                            data = json.loads(line)
                            print(f"DEBUG: JSON da linha extraído com sucesso (estratégia 3)")
                            break
                        except json.JSONDecodeError:
                            continue
        
        if data is None:
            print(f"AVISO: Não foi possível extrair JSON válido da resposta")
            return {"excerpt": "", "metaDescription": ""}
        
        print(f"DEBUG: JSON final parseado: {data}")
        
        # Usa .get() para evitar KeyError e retornar um valor padrão se a chave não existir.
        result = {
            "excerpt": data.get("excerpt", ""),
            "metaDescription": data.get("metaDescription", "")
        }
        print(f"DEBUG: Resultado final: {result}")
        return result
        
    except Exception as e:
        print(f"AVISO: Ocorreu um erro inesperado em generate_excerpt_meta_pt para o título '{title}'. Erro: {e}")
        print(f"DEBUG: Resposta que causou erro: {resp if 'resp' in locals() else 'N/A'}")
        return {"excerpt": "", "metaDescription": ""}

def alt_text(image_url):
    return ollama_chat_vision("moondream", "Alt-text PT-BR, objetivo, ≤150 caracteres.", image_url)

def repair_ricos_nodes(html, ricos_json):
    prompt = f"""Você é um validador de JSON Ricos.
Tarefa: Corrija a estrutura para aderir ao SCHEMA mínimo (tipos: PARAGRAPH, TEXT, HEADING, BULLETED_LIST, ORDERED_LIST, LIST_ITEM, IMAGE, VIDEO), mantendo conteúdo.
Retorne somente JSON no formato {{"nodes":[...]}}.

ENTRADA_HTML:
{html}

ENTRADA_RICOS_ATUAL:
{json.dumps(ricos_json, ensure_ascii=False)}
"""
    resp = ollama_generate("qwen2.5:7b-instruct", prompt, fmt="json", temperature=0.1)
    return json.loads(resp)


# Carregar o CSV
df = pd.read_csv("scripts/posts_wordpress.csv")

# Função para gerar alt-text para imagens
def generate_image_alt_text(image_url):
    return ollama_chat_vision("moondream", "Alt-text PT-BR, objetivo, ≤150 caracteres.", image_url)

# Processar cada post no CSV
for index, row in df.iterrows():
    title = row['Title']
    content = row['Content']
    image_url = row['ImageURL'].split("|")[0]

    
    # Gerar o excerpt e meta description para cada post
    result = generate_excerpt_meta_pt(title, content)
    
    # Gerar alt-text para a imagem (se disponível)
    image_alt_text = ""
    if pd.notna(image_url) and image_url != "":
        image_alt_text = generate_image_alt_text(image_url)
    
    # Exibir os resultados
    print(f"Título: {title}")
    print(f"Excerpt: {result['excerpt']}")
    print(f"Meta Description: {result['metaDescription']}")
    print(f"Alt Text da Imagem: {image_alt_text}")
    print("-" * 40)
    
    # Se você quiser salvar em um novo CSV:
    df.at[index, 'Excerpt'] = result['excerpt']
    df.at[index, 'MetaDescription'] = result['metaDescription']
    df.at[index, 'ImageAltText'] = image_alt_text

# Salvar em um novo CSV com os resultados
df.to_csv("posts_with_meta_and_alt.csv", index=False)