import base64, json, requests, tempfile, urllib.request
import pandas as pd

OLLAMA = "http://192.168.1.9:11434"

def ollama_generate(model, prompt, fmt=None, temperature=0.2):
    payload = {"model": model, "prompt": prompt, "options": {"temperature": temperature}, "stream": False}
    if fmt: payload["format"] = fmt
    r = requests.post(f"{OLLAMA}/api/generate", json=payload, timeout=120)

    # Verifique se o conteúdo é um JSON válido
    try:
        return r.json()["response"]
    except json.decoder.JSONDecodeError as e:
        print("Erro ao decodificar JSON:", e)
        print("Resposta completa:", r.text)  # Mostrar a resposta completa para depuração
        raise


def ollama_chat_vision(model, prompt, image_url):
    try:
        # baixa a imagem
        with tempfile.NamedTemporaryFile(suffix=".jpg") as f:
            urllib.request.urlretrieve(image_url, f.name)
            # carrega base64
            b64 = base64.b64encode(open(f.name, "rb").read()).decode()
            payload = {"model": model, "prompt": prompt, "images": [b64], "stream": False,
                       "options": {"temperature": 0.2}}
            r = requests.post(f"{OLLAMA}/api/generate", json=payload, timeout=120)
            r.raise_for_status()
            return r.json()["response"]
    except urllib.error.HTTPError as e:
        print(f"AVISO: Não foi possível baixar a imagem de {image_url}. Erro: {e}")
        return ""
    except Exception as e:
        print(f"AVISO: Ocorreu um erro inesperado ao processar a imagem {image_url}. Erro: {e}")
        return ""

def generate_excerpt_meta_pt(title, text):
    prompt = f"""# Papel e Objetivo
Você é um assistente de SEO especialista, focado em criar conteúdo otimizado para blogs em português do Brasil. Seu objetivo é gerar resumos (excerpts) e meta descrições que sejam atraentes e sigam as melhores práticas de SEO.

# Tarefa
Sua tarefa é processar o TÍTULO e o CONTEÚDO de um post de blog e gerar um objeto JSON contendo um 'excerpt' e uma 'metaDescription'.

# Instruções Sequenciais
1. Leia o TÍTULO e o CONTEÚDO fornecidos.
2. Crie um `excerpt` (resumo) com aproximadamente 40 a 60 palavras. Ele deve ser persuasivo e não deve repetir o título.
3. Crie uma `metaDescription` (meta descrição) com um máximo de 160 caracteres. Ela deve ser chamativa, otimizada para cliques e não deve conter aspas.
4. Formate sua saída EXCLUSIVAMENTE como um objeto JSON válido. Não inclua nenhum texto, explicação ou formatação markdown antes ou depois do objeto JSON.

# Exemplo de Formato de Saída Obrigatório
{{
  "excerpt": "Um resumo do artigo vai aqui, com cerca de 40 a 60 palavras, de forma atraente e informativa para engajar o leitor.",
  "metaDescription": "Uma meta descrição curta e direta para SEO, otimizada para mecanismos de busca e com no máximo 160 caracteres."
}}

---
# Dados para Processar

TÍTULO: {title}

CONTEÚDO:
{text}"""
    try:
        resp = ollama_generate("qwen2.5:7b-instruct", prompt, fmt="json", temperature=0.2)
        data = json.loads(resp)
        # Usa .get() para evitar KeyError e retornar um valor padrão se a chave não existir.
        return {
            "excerpt": data.get("excerpt", ""),
            "metaDescription": data.get("metaDescription", "")
        }
    except (json.decoder.JSONDecodeError, TypeError):
        print(f"AVISO: Falha ao decodificar a resposta JSON da IA para o título '{title}'.")
        return {"excerpt": "", "metaDescription": ""}
    except Exception as e:
        print(f"AVISO: Ocorreu um erro inesperado em generate_excerpt_meta_pt para o título '{title}'. Erro: {e}")
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
    image_url = row['ImageFeatured']
    
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