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
from bs4 import BeautifulSoup

__all__ = [
    "convert_html_to_ricos",
]

def convert_html_to_ricos(html: str, *, embed_strategy: str = "html_iframe", image_importer: Optional[Callable[[str], Optional[str]]] = None) -> Dict[str, Any]:
    print(f"DEBUG: convert_html_to_ricos called with HTML: {html}")
    if not html:
        print("DEBUG: HTML is empty, returning empty nodes")
        return {"nodes": []}

    soup = BeautifulSoup(html or "", "html.parser")
    nodes: List[Dict[str, Any]] = []
    print(f"DEBUG: Parsed HTML with BeautifulSoup: {soup}")

    # Processar todos os elementos de texto
    for el in soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "span", "b", "strong", "i", "em", "a"]):
        # Ignorar elementos vazios ou que são apenas espaços
        if not el.get_text(strip=True):
            continue
            
        print(f"DEBUG: Processing element: {el.name} - {el.get_text()}")
        # Extrair o texto e processar as decorações
        process_element(el, nodes)
        print(f"DEBUG: Nodes after processing element: {nodes}")

    print(f"DEBUG: Final nodes: {nodes}")
    return {"nodes": nodes}

def process_element(element, nodes):
    """Processa um elemento HTML e seus filhos para criar nodes Ricos."""
    text = element.get_text()
    print(f"DEBUG: process_element called with element {element.name}, text: '{text}'")
    
    # Ignorar elementos vazios
    if not text or not text.strip():
        return
        
    decorations = []
    
    # Verificar negrito
    if element.name in ['b', 'strong'] or element.find_parent(['b', 'strong']):
        print("DEBUG: Found bold decoration")
        decorations.append({"type": "BOLD"})
        
    # Verificar itálico
    if element.name in ['i', 'em'] or element.find_parent(['i', 'em']):
        print("DEBUG: Found italic decoration")
        decorations.append({"type": "ITALIC"})
    
    # Verificar links
    if element.name == 'a':
        href = element.get('href')
        if href:
            print(f"DEBUG: Found link decoration: {href}")
            decorations.append({
                "type": "LINK",
                "linkData": {
                    "link": {
                        "url": href,
                        "target": "BLANK" if element.get('target') == '_blank' else "SELF"
                    }
                }
            })
    elif element.find('a'):
        # Se o elemento contém links, precisamos processá-los de forma mais complexa
        # Esta é uma simplificação - uma implementação completa seria mais complexa
        links = element.find_all('a')
        for link in links:
            href = link.get('href')
            if href:
                print(f"DEBUG: Found link decoration in child: {href}")
                decorations.append({
                    "type": "LINK",
                    "linkData": {
                        "link": {
                            "url": href,
                            "target": "BLANK" if link.get('target') == '_blank' else "SELF"
                        }
                    }
                })
    
    # Somente adicionar o node se houver texto
    if text.strip():
        node = {
            "type": "PARAGRAPH",
            "nodes": [{
                "type": "TEXT",
                "textData": {"text": text.strip(), "decorations": decorations}
            }]
        }
        print(f"DEBUG: Created node: {node}")
        nodes.append(node)