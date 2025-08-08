from src.migration_tool import WordPressMigrationTool
from src.extractors.wordpress_extractor import extract_posts_from_csv, extract_posts_from_xml
from src.migrators.wix_migrator import create_draft_post
import os

def main():
    """
    Main function to run the WordPress to Wix migration tool.
    """
    tool = WordPressMigrationTool(config_file='wix_migration_tool/config/migration_config.json')
    tool.log_message("Starting WordPress to Wix migration.")

    # Get Wix API credentials from the user
    if not tool.config['wix']['site_id'] or not tool.config['wix']['api_key']:
        tool.log_message("Wix API credentials not found in the configuration file.", level='ERROR')
        tool.config['wix']['site_id'] = input("Please enter your Wix Site ID: ")
        tool.config['wix']['api_key'] = input("Please enter your Wix API Key: ")
        with open('wix_migration_tool/config/migration_config.json', 'w') as f:
            import json
            json.dump(tool.config, f, indent=2)
        tool.log_message("Wix API credentials saved to the configuration file.")


    # Extract posts from the export file
    posts_csv_path = 'wix_migration_tool/docs/Posts-Export-2025-July-25-1838.csv'
    posts_xml_path = 'wix_migration_tool/docs/Posts-Export-2025-July-24-2047.xml'
    
    posts = []
    if os.path.exists(posts_csv_path):
        tool.log_message(f"Extracting posts from {posts_csv_path}...")
        posts.extend(extract_posts_from_csv(posts_csv_path))
    
    if os.path.exists(posts_xml_path):
        tool.log_message(f"Extracting posts from {posts_xml_path}...")
        posts.extend(extract_posts_from_xml(posts_xml_path))

    if not posts:
        tool.log_message("No posts found in the export files.", level='ERROR')
        return

    tool.log_message(f"Found {len(posts)} posts to migrate.")

    # Migrate posts to Wix
    for post in posts:
        tool.log_message(f"Migrating post: {post.get('Title')}")
        response = create_draft_post(tool.config['wix'], post)
        if response:
            tool.log_message(f"Post '{post.get('Title')}' created successfully in Wix.", level='SUCCESS')
        else:
            tool.log_message(f"Failed to create post '{post.get('Title')}' in Wix.", level='ERROR')

    tool.log_message("Migration process finished.")

if __name__ == "__main__":
    main()
