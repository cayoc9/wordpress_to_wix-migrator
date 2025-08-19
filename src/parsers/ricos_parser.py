"""
Ricos parser for converting HTML into the Wix Rich Content format.

This module is a copy of the standalone ``ricos_parser.py`` at the
repository root.  It is provided here to satisfy the import path
``src.parsers.ricos_parser``.  See the root-level module for detailed
documentation.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Callable
from bs4 import BeautifulSoup, NavigableString

__all__ = [
    "convert_html_to_ricos",
]

def convert_html_to_ricos(html: str, *, embed_strategy: str = "html_iframe", image_importer: Optional[Callable[[str], Optional[str]]] = None) -> Dict[str, Any]:
    """
    Converte HTML para o formato Ricos do Wix de forma recursiva.
    
    Esta versão processa a árvore HTML inteira e cria nodes Ricos correspondentes,
    preservando a estrutura e formatação.
    """
    print(f"DEBUG: convert_html_to_ricos called with HTML (length {len(html) if html else 0}): {html[:200] if html else ''}...")
    
    if not html or not html.strip():
        print("DEBUG: HTML is empty, returning empty nodes")
        return {"nodes": []}

    soup = BeautifulSoup(html, "html.parser")
    nodes: List[Dict[str, Any]] = []

    # Processar cada elemento filho do body (ou da raiz do soup)
    for child in soup.children:
        child_nodes = process_element_recursive(child, image_importer)
        if child_nodes:
            nodes.extend(child_nodes)
            
    # Filtrar nodes vazios
    nodes = [node for node in nodes if is_valid_node(node)]
    
    print(f"DEBUG: Final nodes: {nodes}")
    return {"nodes": nodes}

def is_valid_node(node: Dict[str, Any]) -> bool:
    """Verifica se um node é válido (não vazio)."""
    if not node:
        return False
        
    if node.get("type") == "PARAGRAPH":
        # Verificar se o parágrafo tem texto
        paragraph_nodes = node.get("nodes", [])
        if not paragraph_nodes:
            return False
        # Verificar se há texto nos nós filhos
        for p_node in paragraph_nodes:
            if p_node.get("type") == "TEXT":
                text_data = p_node.get("textData", {})
                text = text_data.get("text", "").strip()
                if text:
                    return True
        return False
        
    return True

def process_element_recursive(element, image_importer: Optional[Callable[[str], Optional[str]]] = None) -> List[Dict[str, Any]]:
    """
    Processa um elemento HTML recursivamente e retorna uma lista de nodes Ricos.
    """
    # print(f"DEBUG: process_element_recursive called with element: {element.name if hasattr(element, 'name') else type(element)}")
    
    # Se for um NavigableString (texto puro)
    if isinstance(element, NavigableString):
        text = str(element).strip()
        if text:
            return [{
                "type": "PARAGRAPH",
                "nodes": [{
                    "type": "TEXT",
                    "textData": {"text": text, "decorations": []}
                }]
            }]
        return []
        
    # Se for uma tag
    if hasattr(element, 'name'):
        # Ignorar tags de script e style
        if element.name in ['script', 'style']:
            return []
            
        # Processar conteúdo da tag
        children_nodes: List[Dict[str, Any]] = []
        for child in element.children:
            child_nodes = process_element_recursive(child, image_importer)
            if child_nodes:
                children_nodes.extend(child_nodes)
                
        # Criar node baseado na tag
        if element.name in ['p', 'div']:
            # Para div, vamos tratar como parágrafo também, a menos que tenha filhos de bloco
            if children_nodes:
                return [{
                    "type": "PARAGRAPH",
                    "nodes": children_nodes
                }]
            else:
                # Se não tem filhos, criar um nó de texto vazio
                return [{
                    "type": "PARAGRAPH",
                    "nodes": [{
                        "type": "TEXT",
                        "textData": {"text": "", "decorations": []}
                    }]
                }]
                
        elif element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            if children_nodes:
                return [{
                    "type": "HEADING",
                    "level": int(element.name[1]),
                    "nodes": children_nodes
                }]
            else:
                return [{
                    "type": "HEADING",
                    "level": int(element.name[1]),
                    "nodes": [{
                        "type": "TEXT",
                        "textData": {"text": "", "decorations": []}
                    }]
                }]
                
        elif element.name in ['b', 'strong']:
            # Aplicar decoração BOLD a todos os nós de texto filhos
            for node in flatten_text_nodes(children_nodes):
                if "decorations" in node.get("textData", {}):
                    node["textData"]["decorations"].append({"type": "BOLD"})
            return children_nodes
            
        elif element.name in ['i', 'em']:
            # Aplicar decoração ITALIC a todos os nós de texto filhos
            for node in flatten_text_nodes(children_nodes):
                if "decorations" in node.get("textData", {}):
                    node["textData"]["decorations"].append({"type": "ITALIC"})
            return children_nodes
            
        elif element.name == 'a':
            # Aplicar decoração LINK a todos os nós de texto filhos
            href = element.get('href')
            if href:
                for node in flatten_text_nodes(children_nodes):
                    if "decorations" in node.get("textData", {}):
                        node["textData"]["decorations"].append({
                            "type": "LINK",
                            "linkData": {
                                "link": {
                                    "url": href,
                                    "target": "BLANK" if element.get('target') == '_blank' else "SELF"
                                }
                            }
                        })
            return children_nodes
            
        elif element.name == 'br':
            # Quebra de linha - adicionar um texto vazio ou tratar de outra forma
            # Vamos adicionar uma quebra de linha ao último nó de texto, se existir
            # Por enquanto, vamos retornar um nó de texto vazio
            return [{
                "type": "PARAGRAPH",
                "nodes": [{
                    "type": "TEXT",
                    "textData": {"text": "\n", "decorations": []}
                }]
            }]
            
        elif element.name == 'img':
            # Tratar imagem
            src = element.get('src')
            if src and image_importer:
                media_id = image_importer(src)
                if media_id:
                    return [{
                        "type": "IMAGE",
                        "imageData": {
                            "image": {
                                "mediaId": media_id
                            }
                        }
                    }]
            # Se não conseguir importar, ignora a imagem
            return []
            
        else:
            # Para outras tags, processar os filhos
            # Isso lida com tags como span, etc.
            return children_nodes
            
    return []

def flatten_text_nodes(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Achata a lista de nodes para encontrar todos os nodes de texto.
    """
    text_nodes = []
    for node in nodes:
        if node.get("type") == "TEXT":
            text_nodes.append(node)
        elif "nodes" in node:
            text_nodes.extend(flatten_text_nodes(node["nodes"]))
    return text_nodes