import os
import json
import csv
from src.migration_tool import WordPressMigrationTool
from src.extractors.wordpress_extractor import extract_posts_from_csv, extract_posts_from_xml
from src.migrators.wix_migrator import create_draft_post
from src.parsers.html_parser import convert_html_to_rich_content

def main():
    """
    Função principal para rodar a ferramenta de migração WordPress para Wix.
    """
    # Inicializa a ferramenta, que carrega ou cria o config/migration_config.json
    tool = WordPressMigrationTool(config_file='config/migration_config.json')
    tool.log_message("Iniciando a migração WordPress para Wix.")

    # Pede as credenciais do Wix se não estiverem no arquivo de configuração
    if not tool.config['wix'].get('site_id') or not tool.config['wix'].get('api_key'):
        tool.log_message("Credenciais Wix não encontradas no arquivo de configuração.", level='ERROR')
        tool.config['wix']['site_id'] = input("Por favor, insira seu Wix Site ID: ")
        tool.config['wix']['api_key'] = input("Por favor, insira sua Wix API Key: ")
        with open('config/migration_config.json', 'w') as f:
            json.dump(tool.config, f, indent=2)
        tool.log_message("Credenciais Wix salvas no arquivo de configuração.")

    # Extrai os posts dos arquivos de exportação
    posts_csv_path = 'docs/Posts-Export-2025-July-25-1838.csv'
    posts_xml_path = 'docs/Posts-Export-2025-July-24-2047.xml'
    
    posts = []
    if os.path.exists(posts_csv_path):
        tool.log_message(f"Extraindo posts de {posts_csv_path}...")
        posts.extend(extract_posts_from_csv(posts_csv_path))
    
    if os.path.exists(posts_xml_path):
        tool.log_message(f"Extraindo posts de {posts_xml_path}...")
        posts.extend(extract_posts_from_xml(posts_xml_path))

    if not posts:
        tool.log_message("Nenhum post encontrado nos arquivos de exportação.", level='ERROR')
        return

    tool.log_message(f"Encontrados {len(posts)} posts para migrar.")

    # Prepara o arquivo de mapeamento de redirecionamento
    redirect_map_path = 'reports/redirect_map.csv'
    os.makedirs('reports', exist_ok=True)
    with open(redirect_map_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Old WordPress URL', 'New Wix URL'])

    # Migra os posts para o Wix
    for post in posts:
        tool.log_message(f"Migrando post: {post.get('Title')}")

        # Converte o conteúdo HTML para o formato Rich Content do Wix
        html_content = post.get('Content', '')
        rich_content = convert_html_to_rich_content(html_content, tool.config['wix'])

        if not rich_content.get("nodes"):
            tool.log_message(f"Conteúdo de '{post.get('Title')}' resultou em 0 nós. Pulando post.", level='WARNING')
            continue

        response = create_draft_post(tool.config['wix'], post, rich_content)
        if response:
            new_url = response.get('draftPost', {}).get('url', {}).get('base', '') + response.get('draftPost', {}).get('url', {}).get('path', '')
            tool.log_message(f"Post '{post.get('Title')}' criado com sucesso no Wix. Nova URL: {new_url}", level='SUCCESS')
            
            # Registra o mapeamento de URLs
            with open(redirect_map_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([post.get('Permalink'), new_url])
        else:
            tool.log_message(f"Falha ao criar o post '{post.get('Title')}' no Wix.", level='ERROR')

    tool.log_message("Processo de migração finalizado.")

if __name__ == "__main__":
    main()
