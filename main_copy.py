"""
Entry point for debugging WordPress to Wix migration errors.
This copy is specifically for testing failed posts with detailed debugging.
"""

import glob
import json
import os
import traceback
from src.migration_tool import WordPressMigrationTool

CONFIG_FILE = "config/migration_config.json"

def main():
    """
    Main function to debug WordPress to Wix migration errors.
    """
    print("=" * 80)
    print("🐛 MODO DEBUG - MAIN_COPY.PY")
    print("=" * 80)
    
    tool = WordPressMigrationTool(config_file=CONFIG_FILE)
    tool.log_message("Starting WordPress to Wix migration DEBUG mode.")

    # Usar o CSV final dos posts que faltam migrar
    retry_csv = "posts_faltam_migrar_final.csv"
    
    print(f"\n📁 Procurando arquivo de retry: {retry_csv}")
    
    if os.path.exists(retry_csv):
        print(f"✅ Encontrado arquivo de retry: {retry_csv}")
        csv_path = retry_csv
        xml_path = None
    else:
        print(f"❌ Arquivo {retry_csv} não encontrado. Usando arquivos padrão...")
        
        # Fallback para arquivos padrão
        docs_path = "docs/"
        csv_files = glob.glob(os.path.join(docs_path, "*.csv"))
        xml_files = glob.glob(os.path.join(docs_path, "*.xml"))

        if not csv_files and not xml_files:
            tool.log_message(
                f"No WordPress export files (.csv or .xml) found in '{docs_path}' directory.",
                level="ERROR",
            )
            return

        csv_path = csv_files[0] if csv_files else None
        xml_path = xml_files[0] if xml_files else None

    print(f"\n📂 Arquivos a serem processados:")
    print(f"   CSV: {csv_path}")
    print(f"   XML: {xml_path}")
    
    # Extract posts com debug detalhado
    print(f"\n🔍 INICIANDO EXTRAÇÃO DE POSTS...")
    try:
        posts = tool.extract_posts(csv_path=csv_path, xml_path=xml_path)
        print(f"✅ Extração concluída. Posts encontrados: {len(posts)}")
    except Exception as e:
        print(f"❌ ERRO na extração de posts: {e}")
        traceback.print_exc()
        return

    if not posts:
        tool.log_message("No posts found in the export files.", level="ERROR")
        print("❌ Nenhum post encontrado!")
        return

    # Pré-processamento para corrigir dados antes da migração
    print("\n🔧 Aplicando correções de dados antes da migração...")
    for post in posts:
        # Garante que o altText da imagem destacada não seja vazio, usando o título como fallback
        if not post.get("ImageAltText", "").strip():
            post["ImageAltText"] = post.get("Title", "Imagem do post").strip()
    print("✅ Correções de dados aplicadas.")

    print(f"\n📊 RESUMO DOS POSTS EXTRAÍDOS:")
    print(f"   Total de posts: {len(posts)}")
    
    # Mostrar detalhes dos primeiros posts
    print(f"\n📋 PRIMEIROS {min(5, len(posts))} POSTS:")
    for i, post in enumerate(posts[:5]):
        print(f"   {i+1}. ID: {post.get('ID', 'N/A')} | Slug: {post.get('Slug', 'N/A')} | Title: {post.get('Title', 'N/A')[:50]}...")
    
    # Configuração de debug
    config = tool.config
    print(f"\n⚙️ CONFIGURAÇÃO ATUAL:")
    print(f"   Wix Base URL: {config.get('wix', {}).get('base_url', 'N/A')}")
    print(f"   Dry Run: {config.get('migration', {}).get('dry_run', False)}")
    print(f"   Limit: {config.get('migration', {}).get('limit', 'N/A')}")
    print(f"   Access Token: {'✅ Configurado' if config.get('wix', {}).get('access_token') else '❌ Não configurado'}")
    
    # Processar todos os posts (sem limite)
    original_limit = config.get('migration', {}).get('limit')
    # config['migration']['limit'] = None  # Processar todos
    print(f"   🚀 DEBUG: Processando os {len(posts)} posts que faltam migrar")
    
    print(f"\n🚀 INICIANDO PROCESSO DE MIGRAÇÃO...")
    print("=" * 50)

    try:
        # Run the full migration process with detailed logging
        tool.migrate_posts(
            posts,
            new_base_url=config["migration"]["wix_site_url"]
        )
        print("=" * 50)
        print("✅ Processo de migração finalizado!")
    except Exception as e:
        print("=" * 50)
        print(f"❌ ERRO CRÍTICO durante a migração: {e}")
        traceback.print_exc()
    finally:
        # Restaurar limite original
        config['migration']['limit'] = original_limit

    tool.log_message("Migration DEBUG process finished.")
    print("\n🏁 DEBUG FINALIZADO")

if __name__ == "__main__":
    main()