# Repository Guidelines

## Project Structure & Module Organization
- `src/`: código-fonte principal
  - `src/migrators/`: chamadas à Wix API (blog v3, members v1, media v1)
  - `src/parsers/`: conversão HTML → Ricos (rich content)
  - `src/extractors/`: importadores WordPress (CSV/XML)
- `scripts/`: utilitários CLI (ex.: atualizar/publish drafts)
- `models/`: modelos de validação (ex.: `wix_post.py`, Pydantic v2)
- `data/`: insumos/saídas temporárias (posts, cache)
- `docs/`: dumps WordPress de entrada
- `reports/`: logs e artefatos de migração
- `testes/`: testes (pytest)

## Build, Test, and Development Commands
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py                              # roda migração end-to-end
bash run_migration.sh                       # wrapper conveniente
python scripts/update_wix_post.py --help    # atualizar/publicar draft
pytest -q                                   # executar testes
```

## Coding Style & Naming Conventions
- Python 3.x; 4 espaços; siga PEP 8; use type hints.
- Nomes: arquivos/variáveis em `snake_case`, classes em `PascalCase`.
- Pydantic v2 nos modelos em `models/` (ex.: `ConfigDict`, `field_validator`).
- Mantenha funções coesas e módulos com uma única responsabilidade.

## Testing Guidelines
- Framework: `pytest`.
- Estrutura de testes: `testes/test_*.py` correspondendo aos módulos alvo.
- Inclua casos para: parsing Ricos, montagem de payloads Wix, e tratamento de erros/retry.
- Rodar localmente: `pytest -q`. Adicione fixtures leves e evite dependências externas.

## Commit & Pull Request Guidelines
- Commits: prefira Conventional Commits (ex.: `feat(migrator): suporte a publish`, `fix(parser): corrige listas`).
- Mensagens curtas, no imperativo, com escopo quando útil.
- Pull Requests devem incluir:
  - Resumo objetivo e motivação.
  - Passos de teste manuais (comandos) e evidências (logs/prints).
  - Itens afetados (arquivos, endpoints) e riscos conhecidos.

## Security & Configuration Tips
- Nunca versione tokens. Use `config/migration_config.json` (chave `wix.access_token`) e/ou variáveis `WIX_APP_ID`, `WIX_APP_SECRET`, `WIX_INSTANCE_ID`.
- Respeite limites de taxa: use as helpers de retry/rate limit em `src/migrators/wix_migrator.py`.
- Faça “dry-run” antes de publicar em produção (`migration.dry_run` e flags dos scripts).

