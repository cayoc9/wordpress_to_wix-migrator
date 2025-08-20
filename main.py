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

    # Log discovered files for debugging
    tool.log_message(f"Discovered CSV files: {csv_files}", level="DEBUG")
    tool.log_message(f"Discovered XML files: {xml_files}", level="DEBUG")

    if not csv_files and not xml_files:
        tool.log_message(
            f"No WordPress export files (.csv or .xml) found in '{docs_path}' directory.",
            level="ERROR",
        )
        return

    posts = []
    # Process all found CSV files
    for csv_path in csv_files:
        posts.extend(tool.extract_posts(csv_path=csv_path))

    # Process all found XML files and add to the list
    for xml_path in xml_files:
        # Extend posts from XML, avoiding duplicates if already processed from CSV
        xml_posts = tool.extract_posts(xml_path=xml_path)
        
        # Simple check to avoid adding duplicate posts if they exist in both sources
        existing_titles = {p.get('title') for p in posts}
        new_posts = [p for p in xml_posts if p.get('title') not in existing_titles]
        if new_posts:
            posts.extend(new_posts)


    if not posts:
        tool.log_message("No posts found in any of the export files.", level="ERROR")
        return

    tool.log_message(f"Found a total of {len(posts)} posts to migrate.")
    
    # Pre-flight check for Wix site URL
    try:
        new_base_url = tool.config["migration"]["wix_site_url"]
        if not new_base_url:
            raise KeyError("Wix site URL is empty.")
        tool.log_message(f"Target Wix site URL: {new_base_url}", level="DEBUG")
    except KeyError:
        tool.log_message(
            "Wix site URL ('wix_site_url') not found or is empty in config/migration_config.json.",
            level="ERROR",
        )
        return

    # Run the full migration process
    tool.migrate_posts(
        posts,
        new_base_url=new_base_url
    )

    tool.log_message("Migration process finished.")

if __name__ == "__main__":
    main()
