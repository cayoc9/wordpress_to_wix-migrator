"""
Entry point for the WordPress to Wix migration tool.
"""

import glob
import json
import os
from src.migration_tool import WordPressMigrationTool
from src.utils.pre_flight_checks import run_wix_pre_flight_checks, PreFlightCheckError

CONFIG_FILE = "config/migration_config.json"

def prompt_for_config(tool: WordPressMigrationTool):
    """
    Prompts the user for missing configuration values and saves them.
    """
    config_changed = False
    if not tool.config["wix"].get("site_id") or not tool.config["wix"].get("api_key"):
        tool.log_message("Wix credentials not found in config file.", level="ERROR")
        tool.config["wix"]["site_id"] = input("Please enter your Wix Site ID: ")
        tool.config["wix"]["api_key"] = input("Please enter your Wix API Key: ")
        config_changed = True

    if not tool.config["migration"].get("wix_site_url"):
        tool.log_message("Wix site URL not found in config file.", level="WARNING")
        tool.config["migration"]["wix_site_url"] = input(
            "Please enter your full Wix site URL (e.g., https://www.mysite.com): "
        )
        config_changed = True

    if not tool.config["migration"].get("wordpress_domain"):
        tool.log_message("WordPress domain not found in config file.", level="WARNING")
        tool.config["migration"]["wordpress_domain"] = input(
            "Please enter your old WordPress domain (e.g., myblog.wordpress.com): "
        )
        config_changed = True

    if config_changed:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(tool.config, f, indent=2)
        tool.log_message("Configuration saved.", level="INFO")

def main():
    """
    Main function to run the WordPress to Wix migration tool.
    """
    tool = WordPressMigrationTool(config_file=CONFIG_FILE)
    tool.log_message("Starting WordPress to Wix migration.")

    # Prompt for any missing configuration
    prompt_for_config(tool)

    # Run pre-flight checks to validate configuration before starting migration
    try:
        run_wix_pre_flight_checks(tool.config)
    except PreFlightCheckError as e:
        tool.log_message(f"Pre-flight check failed: {e}", level="ERROR")
        tool.log_message("Migration aborted.", level="ERROR")
        return

    # Dynamically find export files in the 'docs' directory
    docs_path = "docs/"
    csv_files = glob.glob(os.path.join(docs_path, "*.csv"))
    xml_files = glob.glob(os.path.join(docs_path, "*.xml"))

    if not csv_files and not xml_files:
        tool.log_message(
            f"No WordPress export files (.csv or .xml) found in '{docs_path}' directory.",
            level="ERROR",
        )
        return

    # Extract posts from the first available CSV or XML file
    csv_path = csv_files[0] if csv_files else None
    xml_path = xml_files[0] if xml_files else None
    posts = tool.extract_posts(csv_path=csv_path, xml_path=xml_path)

    if not posts:
        tool.log_message("No posts found in the export files.", level="ERROR")
        return

    tool.log_message(f"Found {len(posts)} posts to migrate.")

    # Run the full migration process
    tool.migrate_posts(
        posts,
        new_base_url=tool.config["migration"]["wix_site_url"]
    )

    tool.log_message("Migration process finished.")

if __name__ == "__main__":
    main()