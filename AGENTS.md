# Repository Guidelines

## Project Structure & Module Organization

- `src/`: Core migration code. Key entry: `src/migration_tool.py`; submodules: `extractors/`, `parsers/`, `migrators/`, `utils/`.
- `main.py`: CLI entry that auto-detects WordPress exports in `docs/` and runs the migration.
- `config/`: Runtime settings (e.g., `migration_config.json`).
- `docs/`: Source exports from WordPress (`*.csv`, `*.xml`).
- `data/`: Generated outputs and analysis artifacts.
- `scripts/`: Utility scripts (e.g., `map_html_tags.py`).
- `testes/`: Pytest suite for categories/tags and related logic.
- `run_migration.sh`: Convenience wrapper to run the tool.

## Build, Test, and Development Commands

- Setup: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Run migration: `python main.py` or `bash ./run_migration.sh`
- Analyze HTML tags: `python scripts/map_html_tags.py --input docs/<file>.csv --column Content --output data/html_tags_counts.csv`
- Tests: `pytest -q` (runs tests under `testes/`).

## Coding Style & Naming Conventions

- Python 3; follow PEP 8 (4 spaces, 100–120 col soft limit).
- Names: `snake_case` for modules/functions, `PascalCase` for classes, constants in `UPPER_SNAKE_CASE`.
- Prefer type hints where practical and concise docstrings for public functions.
- Keep functions cohesive; avoid side effects. File paths should use `pathlib.Path` when feasible.

## Testing Guidelines

- Framework: `pytest`.
- Location: tests live in `testes/` and follow `test_*.py` naming.
- Write unit tests for parsers/extractors/migrators; use small fixtures from `docs/` or inlined strings.
- Run `pytest -q` locally before opening a PR. Add tests when fixing bugs.

## Commit & Pull Request Guidelines

- Commits: short imperative title (≤72 chars), followed by a brief body explaining the “why” and notable implementation choices. Group related changes.
- PRs: clear description, link related issues, include reproduction steps and before/after notes (logs, sample outputs in `data/`). Ensure tests pass and scripts (`main.py`, relevant tools) run locally.

## Security & Configuration Tips

- Do not commit secrets or tokens. Configure endpoints/keys via `config/migration_config.json` or environment variables.
- Treat files in `docs/` as sensitive exports; avoid distributing PII. Scrub or sample when sharing.
- Large CSV fields: prefer `utf-8-sig` and increase CSV field limits where needed (see `scripts/map_html_tags.py`).
