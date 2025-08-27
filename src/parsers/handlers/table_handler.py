"""
Handler para converter tabelas HTML para o formato de nó Ricos TABLE.
"""

from typing import Any, Dict, List
from bs4.element import Tag
from ..ricos_parser import convert_html_to_ricos
from ..utils import generate_ricos_id

def handle_table(element: Tag, **kwargs) -> List[Dict[str, Any]]:
    """
    Converte uma tag <table> HTML em um nó Ricos TABLE.

    :param element: O elemento BeautifulSoup da tabela.
    :param kwargs: Argumentos adicionais (como image_importer).
    :return: Uma lista contendo o nó da tabela Ricos.
    """
    rows = []
    # Itera sobre todas as linhas da tabela (em thead, tbody, tfoot)
    for tr in element.find_all('tr'):
        cells = []
        # Itera sobre todas as células da linha (td e th)
        for td_or_th in tr.find_all(['td', 'th']):
            # O conteúdo da célula é um documento Ricos completo
            cell_content_html = td_or_th.decode_contents()
            cell_ricos_content = convert_html_to_ricos(cell_content_html, **kwargs)
            
            cells.append({
                "id": generate_ricos_id(),
                "content": cell_ricos_content,
                # Atributos como colspan/rowspan podem ser adicionados aqui se necessário
            })
        
        if cells:
            rows.append({
                "id": generate_ricos_id(),
                "cells": cells
            })

    if not rows:
        return []

    table_node = {
        "type": "TABLE",
        "id": generate_ricos_id(),
        "tableData": {
            "rows": rows,
            # Configurações de dimensões e propriedades da tabela podem ser definidas aqui
            "dimensions": {},
            "properties": {
                "textAlignment": "AUTO"
            }
        }
    }
    
    return [table_node]
