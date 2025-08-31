# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a WordPress to Wix blog migration tool that extracts posts from WordPress export files (CSV/XML) and migrates them to Wix as draft posts, preserving content formatting, SEO data, images, categories, and tags.

## Development Commands

```bash
# Setup environment
python -m venv .venv && source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate  # On Windows
pip install -r requirements.txt

# Run migration (main entry point)
python main.py                    # Full end-to-end migration
./run_migration.sh               # Alternative wrapper script

# Run tests
pytest -q                        # Run all tests quietly
pytest testes/test_ricos_parser.py  # Run specific test file

# Update Wix posts (scripts)
python scripts/update_wix_post.py --post-id <uuid> --file data/posts/<file>.json
python scripts/update_wix_post.py --post-id <uuid> --file data/posts/<file>.json --publish
node scripts/update_wix_post.js --post-id <uuid> --file data/posts/<file>.json --publish
```

## Architecture

The codebase follows a modular pipeline architecture:

- **`src/migration_tool.py`**: Main orchestrator class (`WordPressMigrationTool`)
- **`src/extractors/`**: WordPress data extraction from CSV/XML exports
- **`src/parsers/`**: HTML to Ricos (Wix rich content format) conversion
  - `ricos_parser.py`: Core parser with handlers for different HTML elements
  - `handlers/`: Specialized handlers for paragraphs, headings, lists, images, etc.
- **`src/migrators/`**: Wix API integration for creating/updating posts
- **`models/`**: Pydantic data models for validation (e.g., `wix_post.py`)
- **`scripts/`**: Utility scripts for post updates, token generation, etc.

## Configuration

- **`config/migration_config.json`**: Contains Wix API credentials and migration settings
- Required Wix API fields: `site_id`, `api_key`, `base_url`
- Migration settings: `dry_run`, `limit`, `wordpress_domain`, `wix_site_url`
- **Never commit API keys or tokens to version control**

## Data Flow

1. WordPress export files placed in `docs/` directory
2. `WordPressMigrationTool` extracts posts via `extractors`
3. HTML content converted to Ricos format via `parsers`
4. Posts uploaded to Wix as drafts via `migrators`
5. Migration logs saved to `reports/migration/`
6. URL redirect mapping generated as `reports/redirect_map.csv`

## Key Integration Points

- **Wix API**: Blog Posts API v3, Members API v1, Media Manager API v1
- **Content Format**: Converts HTML to Wix Ricos rich content format
- **Media Handling**: Downloads and uploads images from WordPress to Wix
- **Taxonomy**: Maps WordPress categories/tags to Wix taxonomy system

## Testing Structure

- Tests located in `testes/` directory using pytest framework
- Test files correspond to main modules: `test_migration_tool.py`, `test_ricos_parser.py`, etc.
- Includes tests for HTML parsing, Wix payload assembly, and error handling
- Configuration in `pytest.ini` with pythonpath set to project root

## AI Integration

- **Gemini AI Service**: Located in `services/agente_ia/gemini_client.py`
- Used for generating alt-text descriptions and SEO metadata enhancement
- Integrated into the migration pipeline for content enrichment

## Important Development Notes

- **API Credentials**: Never commit API keys or tokens to version control
- **Environment**: Use `.venv` virtual environment for isolation
- **Dependencies**: Core dependencies include requests, beautifulsoup4, google-genai, Pillow, pandas
- **File Structure**: WordPress exports go in `docs/`, processed posts saved to `data/posts/`
- **Logs and Reports**: Migration logs in `reports/migration/`, redirect mapping in `reports/redirect_map.csv`