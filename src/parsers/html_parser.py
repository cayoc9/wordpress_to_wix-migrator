from bs4 import BeautifulSoup, NavigableString, Tag
from src.migrators.wix_migrator import upload_image # Importa a função de upload

def _parse_text_nodes_recursive(element) -> list:
    """
    Função auxiliar recursiva para processar nós de texto e decorações aninhadas
    (negrito, itálico, links).
    """
    nodes = []
    if isinstance(element, NavigableString):
        # Se for apenas uma string, cria um nó de texto simples.
        if element.strip():
            nodes.append({
                "type": "TEXT",
                "nodes": [],
                "textData": {"text": element.strip(), "decorations": []}
            })
        return nodes

    # Mapeia tags HTML para decorações do Wix
    decoration_map = {
        'b': 'BOLD', 'strong': 'BOLD',
        'i': 'ITALIC', 'em': 'ITALIC',
        'u': 'UNDERLINE'
    }

    child_nodes = []
    for child in element.contents:
        child_nodes.extend(_parse_text_nodes_recursive(child))

    # Aplica a decoração apropriada aos nós filhos
    if element.name in decoration_map:
        decoration_type = decoration_map[element.name]
        for node in child_nodes:
            node['textData']['decorations'].append({"type": decoration_type})
    elif element.name == 'a' and element.has_attr('href'):
        for node in child_nodes:
            node['textData']['decorations'].append({
                "type": "LINK",
                "linkData": {"link": {"url": element['href']}}
            })
    
    return child_nodes


def convert_html_to_rich_content(html_string: str, wix_config: dict) -> dict:
    """
    Converte uma string de conteúdo HTML do WordPress para o formato
    Wix Rich Content (JSON), incluindo parágrafos, cabeçalhos, listas,
    formatação de texto e imagens.
    """
    if not html_string:
        return {"nodes": []}

    soup = BeautifulSoup(html_string, 'html.parser')
    wix_nodes = []

    for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'figure'], recursive=False):
        wix_node = None
        
        # Lida com imagens, que podem estar dentro de <figure> ou <p>
        if element.name == 'figure' and element.find('img'):
            img_tag = element.find('img')
        elif element.name == 'p' and element.find('img'):
             img_tag = element.find('img')
        else:
            img_tag = None

        if img_tag:
            src = img_tag.get('src')
            if src:
                new_wix_url = upload_image(wix_config, src)
                if new_wix_url:
                    wix_node = {
                        "type": "IMAGE",
                        "nodes": [],
                        "imageData": {
                            "image": {
                                "src": { "url": new_wix_url }
                            },
                            "altText": img_tag.get('alt', '')
                        }
                    }
        
        # Mapeia Cabeçalhos e Parágrafos
        elif element.name.startswith('h'):
            level = int(element.name[1])
            wix_node = {
                "type": "HEADING", "nodes": [],
                "headingData": {"level": level}
            }
            wix_node["nodes"].extend(_parse_text_nodes_recursive(element))
        
        elif element.name == 'p':
            wix_node = {
                "type": "PARAGRAPH", "nodes": [],
                "paragraphData": {"textStyle": {"textAlignment": "AUTO"}, "indentation": 0}
            }
            wix_node["nodes"].extend(_parse_text_nodes_recursive(element))

        # Mapeia Listas
        elif element.name in ['ul', 'ol']:
            list_type = "BULLETED_LIST" if element.name == 'ul' else "ORDERED_LIST"
            wix_node = {"type": list_type, "nodes": []}
            
            for li in element.find_all('li', recursive=False):
                list_item_node = {
                    "type": "LIST_ITEM", "nodes": [],
                    "listItemData": {"textStyle": {"textAlignment": "AUTO"}}
                }
                # O conteúdo de um <li> é um parágrafo dentro do item da lista
                paragraph_in_list = {
                    "type": "PARAGRAPH", "nodes": [],
                    "paragraphData": {"textStyle": {"textAlignment": "AUTO"}, "indentation": 0}
                }
                paragraph_in_list["nodes"].extend(_parse_text_nodes_recursive(li))
                list_item_node["nodes"].append(paragraph_in_list)
                wix_node["nodes"].append(list_item_node)

        if wix_node and (wix_node.get("nodes") or wix_node.get("type") == "IMAGE"):
            wix_nodes.append(wix_node)

    return {"nodes": wix_nodes}
