"""
Entry point for the WordPress to Wix migration tool.
"""

import glob
import json
import os
from src.migration_tool import WordPressMigrationTool

CONFIG_FILE = "config/migration_config.json"



def main():
    """
    Main function to run the WordPress to Wix migration tool.
    """
    tool = WordPressMigrationTool(config_file=CONFIG_FILE)
    tool.log_message("Starting WordPress to Wix migration.")

    

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