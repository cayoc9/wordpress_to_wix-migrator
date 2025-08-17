# Qwen Code Context for `wordpress_to_wix-migrator`

## Project Overview

This project is a Python-based tool designed to automate the migration of blog posts from a WordPress export (supporting both `.xml` and `.csv` formats) to a Wix website. The primary goal is to preserve content and SEO by accurately transferring post data, including title, rich text content, featured images, slugs, categories, and tags, directly into the Wix platform as draft posts.

The tool orchestrates a complete pipeline: it extracts data from export files, transforms HTML content into Wix's Ricos format, manages Wix taxonomy (tags/categories) and members, uploads media, creates draft posts via the Wix Blog API, publishes them, and generates detailed logs and a URL redirect map.

## Core Technologies & Architecture

- **Language**: Python 3.8+
- **Dependencies**: `requests`, `beautifulsoup4` (managed via `requirements.txt`).
- **Structure**:
  - `main.py`: The entry point. It initializes the `WordPressMigrationTool` and triggers the migration process by finding export files and calling the tool's methods.
  - `src/migration_tool.py`: The core logic. Defines the `WordPressMigrationTool` class, which coordinates all steps of the migration.
  - `src/extractors/`: (Directory) Likely contains modules for parsing WordPress export files (`.csv`, `.xml`).
  - `src/parsers/`: (Directory) Likely contains modules for converting HTML content (e.g., using `beautifulsoup4`) to Wix's Ricos format.
  - `src/migrators/`: (Directory) Likely contains modules with functions to interact with the Wix API (e.g., `upload_image_from_url`, `create_draft_post`).
  - `src/utils/`: (Directory) Likely contains utility modules for error reporting and generating redirect CSVs.
  - `config/migration_config.json`: The main configuration file for Wix API credentials, migration settings (like `dry_run`, `limit`), and site URLs.
  - `requirements.txt`: Lists Python package dependencies.
  - `run_migration.sh`: A shell script to potentially automate the execution.
  - `docs/`: Directory for input WordPress export files.
  - `reports/migration/`: Directory for output logs (`migration.log`) and the redirect map (`redirect_map.csv`).

## Building, Running & Configuration

### Environment Setup

1. Ensure Python 3.8+ and `pip` are installed.
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration (`config/migration_config.json`)

Before running, you must configure the Wix API access:

- `wix`: Contains Wix API connection details.
  - `access_token`: Your Wix App Instance access token (obtained via OAuth2).
  - `base_url`: The Wix API base URL (usually `https://www.wixapis.com`).
- `migration`: Contains migration-specific settings.
  - `wordpress_domain`: (Optional) The original WordPress domain, used for redirect map generation.
  - `wix_site_url`: (Optional) The base URL of your Wix site, used for constructing new post URLs.
  - `dry_run`: If `true`, the tool runs the extraction and conversion steps but skips all network calls to Wix (no media upload, post creation, or member creation). Useful for testing.
  - `limit`: (Optional, integer) Limits the number of posts to migrate.

### Running the Tool

1. Place your WordPress export file(s) (`.xml` or `.csv`) into the `docs/` directory.
2. Ensure `config/migration_config.json` is correctly populated with your Wix credentials and desired settings.
3. Execute the main script:
   ```bash
   python3 main.py
   ```
   Alternatively, you might use the provided shell script:
   ```bash
   ./run_migration.sh
   ```
4. Monitor the console output and the log file at `reports/migration/migration.log`.
5. After completion, check `reports/redirect_map.csv` for the URL mapping.

## Development Conventions

- **Modularity**: Code is organized into specific modules (`extractors`, `parsers`, `migrators`, `utils`) to separate concerns.
- **Configuration-Driven**: Behavior is controlled via the `config/migration_config.json` file.
- **Logging**: Uses a custom `log_message` method within `WordPressMigrationTool` to print to console and write to `reports/migration/migration.log`.
- **Error Handling**: Employs a custom error reporting mechanism (likely via `src/utils/errors.py`) to track successes and failures for individual posts.
- **Wix API Interaction**: Interacts with various Wix APIs (Members, Tags, Categories, Blog) as detailed in `API.md`. Authentication is handled via Bearer token in the `Authorization` header.