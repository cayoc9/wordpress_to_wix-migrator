#!/usr/bin/env python3
"""
Script para testar a conversão de scripts RDStation.
"""

import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.parsers.ricos_parser import convert_html_to_ricos

def main():
    # Ler o arquivo de exemplo
    with open('data/script_example.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print("HTML de entrada:")
    print(html_content)
    print("\n" + "="*50 + "\n")
    
    # Converter para Ricos
    ricos_result = convert_html_to_ricos(html_content)
    
    print("Resultado da conversão Ricos:")
    print(f"Número de nós: {len(ricos_result['nodes'])}")
    print("\nNós gerados:")
    for i, node in enumerate(ricos_result['nodes']):
        print(f"\nNó {i+1}:")
        if isinstance(node, dict):
            print(f"  Tipo: {node.get('type', 'N/A')}")
            if node.get('type') == 'HTML':
                print(f"  HTML: {node['htmlData']['html'][:100]}...")
            elif node.get('type') == 'PARAGRAPH':
                # Para nós de parágrafo, mostrar o conteúdo de texto
                if 'nodes' in node:
                    for j, subnode in enumerate(node['nodes']):
                        if subnode.get('type') == 'TEXT':
                            print(f"    Texto {j+1}: {subnode['textData']['text'][:100]}...")
            else:
                print(f"  Conteúdo: {json.dumps(node, indent=2, ensure_ascii=False)[:10]}...")
        else:
            print(f"  Conteúdo: {str(node)[:100]}...")

if __name__ == "__main__":
    main()