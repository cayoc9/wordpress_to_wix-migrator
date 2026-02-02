#!/usr/bin/env python3
"""
Script para mapear os IDs dos posts do WordPress para os IDs dos posts do Wix
com base nos títulos dos posts.
"""

import csv
import json
import os
from pathlib import Path

def read_wordpress_csv(file_path):
    """Lê o arquivo CSV do WordPress e retorna uma lista de dicionários com ID e Title."""
    posts = []
    with open(file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            posts.append({
                'id': row['ID'],
                'title': row['Title'].strip()
            })
    return posts

def read_wix_json_files(directory_path):
    """Lê todos os arquivos JSON do diretório do Wix e retorna uma lista de dicionários com ID e title."""
    posts = []
    directory = Path(directory_path)
    
    # Itera sobre todos os arquivos .json no diretório
    for json_file in directory.glob('*.json'):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # O nome do arquivo (sem extensão) é o ID do post no Wix
            wix_id = json_file.stem
            title = data.get('title', '').strip()
            posts.append({
                'id': wix_id,
                'title': title
            })
    
    return posts

def create_mapping(wordpress_posts, wix_posts):
    """Cria o mapeamento entre IDs do WordPress e IDs do Wix baseado nos títulos."""
    mapping = {}
    
    # Para cada post do WordPress, procuramos um post correspondente no Wix
    for wp_post in wordpress_posts:
        wp_title = wp_post['title'].lower().strip()
        
        # Procurar por correspondência no título do Wix
        for wix_post in wix_posts:
            wix_title = wix_post['title'].lower().strip()
            
            # Verificar se os títulos são iguais (comparação aproximada)
            if wp_title == wix_title:
                mapping[wp_post['id']] = wix_post['id']
                break
    
    return mapping

def save_mapping(mapping, output_file):
    """Salva o mapeamento em um arquivo JSON."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

def main():
    """Função principal do script."""
    # Caminhos dos arquivos
    csv_file = 'docs/Posts-Export-2025-July-25-1838.csv'
    wix_posts_dir = 'data/posts'
    output_file = 'data/wix_wordpress_mapping.json'
    
    # Verifica se os arquivos existem
    if not os.path.exists(csv_file):
        print(f"Erro: Arquivo CSV não encontrado em {csv_file}")
        return
    
    if not os.path.exists(wix_posts_dir):
        print(f"Erro: Diretório de posts do Wix não encontrado em {wix_posts_dir}")
        return
    
    # Lê os dados
    print("Lendo o arquivo CSV do WordPress...")
    wordpress_posts = read_wordpress_csv(csv_file)
    
    print("Lendo os arquivos JSON do Wix...")
    wix_posts = read_wix_json_files(wix_posts_dir)
    
    print(f"Encontrados {len(wordpress_posts)} posts no WordPress e {len(wix_posts)} posts no Wix.")
    
    # Cria o mapeamento
    print("Criando mapeamento entre posts...")
    mapping = create_mapping(wordpress_posts, wix_posts)
    
    # Salva o mapeamento
    print("Salvando mapeamento em arquivo...")
    save_mapping(mapping, output_file)
    
    print(f"Mapeamento salvo em {output_file}")
    print(f"Total de mapeamentos: {len(mapping)}")

if __name__ == "__main__":
    main()