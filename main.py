import json
from src.migration_tool import WordPressMigrationTool

def main() -> None:
    """Função principal para rodar a ferramenta de migração WordPress para Wix."""
    tool = WordPressMigrationTool(config_file="config/migration_config.json")
    tool.log_message("Iniciando a migração WordPress para Wix.")

    # Pede as credenciais do Wix se não estiverem no arquivo de configuração
    if not tool.config["wix"].get("site_id") or not tool.config["wix"].get("api_key"):
        tool.log_message(
            "Credenciais Wix não encontradas no arquivo de configuração.",
            level="ERROR",
        )
        tool.config["wix"]["site_id"] = input("Por favor, insira seu Wix Site ID: ")
        tool.config["wix"]["api_key"] = input("Por favor, insira sua Wix API Key: ")
        with open("config/migration_config.json", "w") as f:
            json.dump(tool.config, f, indent=2)
        tool.log_message("Credenciais Wix salvas no arquivo de configuração.")

    # Extrai os posts dos arquivos de exportação
    posts_csv_path = "docs/Posts-Export-2025-July-25-1838.csv"
    posts_xml_path = "docs/Posts-Export-2025-July-24-2047.xml"
    posts = tool.extract_posts(csv_path=posts_csv_path, xml_path=posts_xml_path)

    if not posts:
        tool.log_message(
            "Nenhum post encontrado nos arquivos de exportação.", level="ERROR"
        )
        return

    tool.log_message(f"Encontrados {len(posts)} posts para migrar.")

    new_base_url = input(
        "Por favor, insira a URL base do novo site Wix (ex: https://exemplo.com): "
    ).strip()

    tool.migrate_posts(posts, new_base_url=new_base_url)
    tool.log_message("Processo de migração finalizado.")

if __name__ == "__main__":
    main()

