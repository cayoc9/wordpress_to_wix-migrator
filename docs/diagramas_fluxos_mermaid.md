# Diagramas Mermaid — Arquitetura e Fluxos da Migração

Este arquivo reúne diagramas em Mermaid para visualizar os módulos principais e o fluxo de migração WordPress → Wix.

## 1) Arquitetura por Módulos (visão de componentes)

```mermaid
flowchart TD
  %% Grupos de componentes
  subgraph Orquestrador
    Tool["WordPressMigrationTool<br>src/migration_tool.py"]
  end

  subgraph Extractors
    WPCSV["extract_posts_from_csv<br>src/extractors/wordpress_extractor.py"]
    WPXML["extract_posts_from_xml<br>src/extractors/wordpress_extractor.py"]
  end

  subgraph Parsers
    Ricos["convert_html_to_ricos<br>src/parsers/ricos_parser.py"]
    Strip["strip_html_nodes (planejado)<br>src/parsers/ricos_parser.py"]
  end

  subgraph Migrators
    ImportImage["import_image_from_url<br>src/migrators/wix_migrator.py"]
    Terms["get_or_create_terms<br>src/migrators/wix_migrator.py"]
    CreateDraft["create_draft_post<br>src/migrators/wix_migrator.py"]
    Publish["publish_post<br>src/migrators/wix_migrator.py"]
    RL["RateLimiter / with_retries<br>src/migrators/wix_migrator.py"]
  end

  subgraph Models
    WixPostModel["WixPost<br>models/wix_post.py"]
  end

  subgraph Utils
    Errors["errors<br>src/utils/errors.py"]
    Redirects["redirects<br>src/utils/redirects.py"]
  end

  subgraph Scripts
    UpdateDraft["scripts/update_wix_post.py"]
    GetPost["scripts/get_wix_post.py"]
  end

  subgraph Config
    CfgFile["config/migration_config.json"]
    Env["WIX_APP_ID / SECRET / INSTANCE_ID"]
  end

  WixAPI[("Wix REST API")]

  %% Fluxos de dependência/uso
  CfgFile --> Tool
  Env --> Tool

  Tool --> WPCSV
  Tool --> WPXML
  WPCSV --> Tool
  WPXML --> Tool

  Tool --> Ricos
  Ricos --> Tool

  Tool --> ImportImage
  ImportImage --> WixAPI

  Tool --> Terms
  Terms --> WixAPI

  Tool --> CreateDraft
  CreateDraft --> WixAPI

  Tool --> Publish
  Publish --> WixAPI

  Tool --> Redirects

  %% Observabilidade/erros
  Tool --> Errors
  CreateDraft -. erro .-> Errors
  Publish -. erro .-> Errors
  ImportImage -. erro .-> Errors
  Terms -. erro .-> Errors

  %% Integração com modelos e scripts
  Tool -. valida payload .-> WixPostModel
  UpdateDraft --> WixAPI
  GetPost --> WixAPI
```

## 2) Fluxo de Migração de um Post (sequência)

```mermaid
sequenceDiagram
  autonumber
  participant CSV as CSV/XML
  participant Tool as WordPressMigrationTool
  participant Parser as ricos_parser.convert_html_to_ricos
  participant Migr as wix_migrator
  participant Wix as Wix REST API
  participant Utils as utils (errors/redirects)

  CSV->>Tool: posts (Title, ContentHTML, Tags, Categories, ...)
  Tool->>Parser: convert_html_to_ricos(html)
  Parser-->>Tool: richContent

  alt tem FeaturedImage e não é dry-run
    Tool->>Migr: import_image_from_url(url)
    Migr->>Wix: POST site-media import
    Wix-->>Migr: media id
    Migr-->>Tool: media id
  end

  Tool->>Migr: get_or_create_terms(categories/tags)
  Migr->>Wix: GET/POST categorias/tags
  Wix-->>Migr: term IDs
  Migr-->>Tool: term IDs

  Tool->>Migr: create_draft_post(richContent, ids, memberId)
  Migr->>Wix: POST /blog/v3/draft-posts
  Wix-->>Migr: draft id
  Migr-->>Tool: draft id

  Tool->>Migr: publish_post(draft id)
  Migr->>Wix: POST /blog/v3/draft-posts/{id}/publish
  Wix-->>Migr: post url
  Migr-->>Tool: post url

  Tool->>Utils: generate_redirects_csv(entries)
  Note over Tool,Utils: Em erros → utils.errors + logs
```

## 3) Observações

- O nó `Strip` (strip_html_nodes) está planejado para habilitar "modo estrito" sem nós `HTML`/embeds.
- `embed_strategy` no parser deve controlar o tratamento de iframes (HTML, vídeo nativo, link).
- Scripts utilitários (`scripts/update_wix_post.py` e `scripts/get_wix_post.py`) interagem diretamente com a API para operações pontuais.
