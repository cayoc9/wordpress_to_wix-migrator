# Novo Diagrama de Classe e Payload

## Diagrama de Classe Atualizado

```mermaid
classDiagram
    class WordPressMigrationTool {
        +config: Dict
        +member_map_file: str
        +email_to_member_id_map: Dict[str, str]
        +default_member_id: Optional[str]
        +__init__(config: Dict, config_file: str)
        +log_message(message: str, level: str)
        +extract_posts(csv_path: str, xml_path: str) List[Dict]
        +migrate_posts(posts: List[Dict], new_base_url: str)
    }
    
    class WordPressExtractor {
        +extract_posts_from_csv(csv_path: str) List[Dict]
        +extract_posts_from_xml(xml_path: str) List[Dict]
    }
    
    class RicosParser {
        +convert_html_to_ricos(html: str, embed_strategy: str, image_importer: Callable, paragraph_spacing_px: int) Dict
        +strip_html_nodes(ricos: Dict) Dict
    }
    
    class WixMigrator {
        +import_image_from_url(cfg: Dict, image_url: str) Optional[str]
        +get_or_create_terms(cfg: Dict, kind: str, labels: Iterable[str]) List[str]
        +create_draft_post(cfg: Dict, post: Dict, ricos: Dict, member_id: str, allow_html_iframe: bool) Dict
        +publish_post(cfg: Dict, draft_id: str) Dict
        +list_members(cfg: Dict) List[Dict]
        +create_member(cfg: Dict, email: str) Optional[Dict]
    }
    
    class WixPost {
        +title: str
        +excerpt: Optional[str]
        +member_id: Optional[str]
        +rich_content: Optional[Dict]
        +media: Optional[PostMedia]
        +category_ids: Optional[List[str]]
        +tag_ids: Optional[List[str]]
        +featured: Optional[bool]
        +commenting_enabled: Optional[bool]
        +slug: Optional[str]
        +seo_data: Optional[Dict]
        +language: Optional[str]
        +first_published_date: Optional[datetime]
        +to_wix_draft_payload(publish: Optional[bool]) Dict
    }
    
    class Utils {
        +report_error(error_type: str, post: Dict, exception: Exception)
        +report_ok(status: str, post: Dict, details: Dict)
        +generate_redirects_csv(migrated: List[Dict], old_domain: str, new_base: str)
    }
    
    WordPressMigrationTool --> WordPressExtractor : uses
    WordPressMigrationTool --> RicosParser : uses
    WordPressMigrationTool --> WixMigrator : uses
    WordPressMigrationTool --> WixPost : validates
    WordPressMigrationTool --> Utils : uses
```

## Payload Sugerido para Criação de Post no Wix

```json
{
  "draftPost": {
    "title": "Título do Post",
    "memberId": "member-id-aqui",
    "richContent": {
      "nodes": [
        {
          "type": "PARAGRAPH",
          "nodes": [
            {
              "type": "TEXT",
              "textData": {
                "text": "Conteúdo do post em formato Ricos",
                "decorations": []
              }
            }
          ],
          "paragraphData": {
            "textStyle": {
              "textAlignment": "JUSTIFY"
            }
          }
        }
      ]
    },
    "excerpt": "Resumo do post (até 3000 caracteres)",
    "categoryIds": ["categoria-id-1", "categoria-id-2"],
    "tagIds": ["tag-id-1", "tag-id-2"],
    "slug": "slug-do-post",
    "seoData": {
      "title": "Título SEO",
      "description": "Descrição SEO (até 156 caracteres)"
    },
    "media": {
      "wixMedia": {
        "image": {
          "id": "media-id-aqui"
        }
      },
      "displayed": true,
      "custom": true
    }
  },
  "publish": true
}
```

## Explicação do Payload

1. **draftPost**: Objeto principal que contém todos os dados do post
   - **title**: Título do post (obrigatório)
   - **memberId**: ID do autor do post (obrigatório)
   - **richContent**: Conteúdo formatado do post em formato Ricos
   - **excerpt**: Resumo do post
   - **categoryIds**: IDs das categorias do post
   - **tagIds**: IDs das tags do post (limite de 30)
   - **slug**: Slug do post
   - **seoData**: Dados para SEO
   - **media**: Imagem de destaque do post

2. **publish**: Booleano que indica se o post deve ser publicado imediatamente após a criação do rascunho

## Recomendações

1. **Tratamento de Erros**: Implementar um mecanismo robusto de tratamento de erros para lidar com:
   - Falhas na criação de membros
   - Erros no upload de imagens
   - Limites da API do Wix (rate limiting)
   - Validação de dados

2. **Mapeamento de Membros**: Manter um mapeamento de e-mails para IDs de membros para evitar a criação duplicada de membros.

3. **Limites da API**: Respeitar os limites da API do Wix usando o RateLimiter implementado.

4. **Validação de Dados**: Validar os dados antes de enviar para a API do Wix, especialmente:
   - Tamanho máximo de campos
   - Formato de datas
   - Estrutura do conteúdo Ricos