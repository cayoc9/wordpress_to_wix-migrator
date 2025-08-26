## Brief overview

Este arquivo define as regras específicas para o projeto de migração do WordPress para Wix. O projeto segue uma estrutura bem definida com módulos especializados para extração, parsing e migração de dados.

## Communication style

- Responda em português (pt-BR) conforme instruído pelo usuário
- Use linguagem técnica mas clara, focando em detalhes práticos do projeto
- Evite explicações excessivamente longas, mantenha o foco nas necessidades específicas do projeto

## Development workflow

- Segue o padrão de projeto com módulos separados: extractors, parsers, migrators, utils
- Utiliza Pydantic v2 para validação de modelos em `models/`
- Implementa testes com pytest em `testes/`
- Scripts CLI em `scripts/` para tarefas específicas
- Estrutura de dados em `data/` com arquivos temporários e saídas

## Coding best practices

- Python 3.x com 4 espaços para indentação seguindo PEP 8
- Nomes em snake_case para arquivos/variáveis e PascalCase para classes
- Type hints em todo o código
- Funções coesas com responsabilidade única
- Uso de Pydantic v2 com ConfigDict e field_validator
- Tratamento adequado de erros com classes em `src/utils/errors.py`

## Project context

- Projeto de migração de conteúdo WordPress para Wix
- Componentes principais:
  - `src/extractors/wordpress_extractor.py`: Importação de dados do WordPress
  - `src/parsers/ricos_parser.py`: Conversão HTML para Rich Content Wix
  - `src/migrators/wix_migrator.py`: Chamadas à API Wix
  - `scripts/`: Ferramentas CLI para tarefas específicas
- Arquivos de configuração em `config/`
- Dados temporários em `data/`
- Documentação em `docs/`
- Relatórios em `reports/`

## Other guidelines

- Nunca versione tokens de acesso
- Respeite limites de taxa da API Wix
- Execute dry-run antes de publicar conteúdo
- Utilize `migration.dry_run` e flags nos scripts para testes
- Use python3 quando for rodar algum script python
