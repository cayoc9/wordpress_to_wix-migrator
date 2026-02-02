## Brief overview

Este arquivo define as regras específicas para o projeto de migração do WordPress para Wix. O projeto segue uma estrutura bem definida com módulos especializados para extração, parsing e migração de dados, focado na conversão de conteúdo HTML do WordPress para o formato Rich Content do Wix.

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
- Trate especificamente as tags HTML com base na análise de frequência:
  - Grupo 1 (Conversão Simples): `<p>`, `<b>`, `<strong>`, `<i>`, `<em>`, `<u>`, `<ul>`, `<ol>`, `<li>`, `<br>`, `<h1>` a `<h6>` - podem ser convertidas automaticamente
  - Grupo 2 (Conversão Moderada): `<a>`, `<img>`, `<span>` (com style), `<table>`, `<blockquote>` - requerem parser mais robusto
  - Grupo 3 (Conversão Complexa): `<iframe>`, `<script>`, `<style>`, shortcodes (`[caption]`, `[button]`, `[embed]`) - exigem tratamento especial ou manual
- Para conversão de conteúdo de WordPress para Wix, siga a estratégia de:
  1. Fase 1: Migração em massa automatizada para tags do Grupo 1 e 2
  2. Fase 2: Desenvolvimento de parsers customizados para shortcodes e iframes complexos
  3. Fase 3: Revisão e ajuste manual para posts mais complexos

## Estratégia de Migração de Conteúdo

### Tags HTML mais frequentes

1. `<span>` (principalmente para estilização de fontes) - Requer parser de CSS
2. `<a>` (links) - Requer extração de href e texto
3. `<p>` (parágrafos) - Mapeia diretamente para parágrafos Ricos
4. `<img>` (imagens) - Requer extração de src, alt e classes de alinhamento
5. `<b>` e `<strong>` (negrito) - Mapeia para negrito Ricos
6. `<h4>`, `<h3>`, `<h2>` (títulos) - Mapeia para títulos Ricos
7. `<li>`, `<ul>`, `<ol>` (listas) - Mapeia para listas Ricos
8. `<iframe>` (conteúdo embutido) - Requer tratamento especial para vídeos do YouTube
9. Shortcodes como `[caption]` - Requer parser customizado

### Estratégia de Tratamento

- Para conteúdo de `<span>` com estilo, utilize um parser CSS para extrair propriedades como color, font-size, text-decoration
- Para `<img>` com classes como `aligncenter`, `size-large`, converta para elementos de imagem Ricos com alinhamento apropriado
- Para `<iframe>` de vídeos, extraia a URL e converta para componente de vídeo nativo do Wix
- Para shortcodes, crie parsers específicos para cada tipo de shortcode encontrado
