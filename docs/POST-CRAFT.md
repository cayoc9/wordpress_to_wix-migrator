Aqui está o conteúdo convertido para **Markdown estruturado**:

````markdown
# Wix API - Documentação

## Índice
- Go Headless  
- Changelog  
- REST  
- Articles  
- Get Started  
- Use the Wix MCP  
- What's New  
- App Management  
  - OAuth 2  
  - App Billing  
  - App Instance  
  - App Permissions  
  - Embedded Scripts  
  - BI Event  
  - Editor Deep Link  
  - Site Plugins  
- Business Solutions  
  - eCommerce  
  - Stores  
  - Bookings  
  - CMS  
  - Events  
  - Restaurants  
  - Blog  
    - Introduction  
    - Sample Flows  
    - Blog Schema for Wix Search  
    - Draft Posts  
      - Introduction  
      - Filter and Sort  
      - Draft Object  
      - **Endpoints**  
        - `GET` List Draft Posts  
        - `POST` Create Draft Post  
        - `POST` Bulk Create Draft Posts  
        - `POST` Bulk Update Draft Posts  
        - `GET` List Deleted Draft Posts  
        - `GET` Get Draft Post  
        - `DELETE` Delete Draft Post  
        - `POST` Update Draft Post  
        - `GET` Get Deleted Draft Post  
        - `DELETE` Remove From Trash Bin  
        - `DELETE` Bulk Delete Draft Posts  
        - `POST` Restore From Trash Bin  
        - `POST` Query Draft Posts  
        - `POST` Publish Draft Post  
      - Events  
        - Draft Post Created  
        - Draft Deleted  
        - Draft Post Updated  
    - Tags  
    - Posts & Stats  
    - Category  
- Forum  
- Pricing Plans  
- Portfolio  
- Benefit Programs  
- Donations  
- Gift Cards  
- Assets  
- Media  
- HTTP Functions  
- Rich Content  
- Pro Gallery  
- CRM  
- Members & Contacts  
- Forms  
- Community  
- Communication  
- Loyalty Program  
- Business Management  
- AI Site-Chat  
- Analytics  
- App Installation  
- Async Job  
- Automations  
- Branches  
- Calendar  
- Captcha  
- Categories  
- Cookie Consent Policy  
- Custom Embeds  
- Data Extension Schema  
- Dashboard  
- FAQ App  
- Get Paid  
- Headless  
- Locations  
- Marketing  
- Multilingual  
- Notifications  
- Payments  
- Site Search  
- Secrets  
- Site Properties  
- Site URLs  
- Tags  
- Account Level  
  - About Account Level APIs  
  - Sites  
  - Resellers  
  - Domains  
  - B2B Site Management  
  - User Management  
- Funnel  
- Site  
- Viewer  
- Wix Backoffice  
- Identity  

---

## Draft Posts - Criar um Post em Rascunho

### Endpoint
```http
POST https://www.wixapis.com/blog/v3/draft-posts
````

### Autenticação

* É necessário estar autenticado como **Wix App** ou **Wix User Identity**.

### Permissões

* `Manage Blog`

### Corpo da Requisição

```json
{
  "draftPost": {
    "title": "Hello, world!",
    "featured": true,
    "categoryIds": ["10a5d26e-5028-4f74-92be-e5163c06b58b"],
    "memberId": "8a8b9b73-4da8-47a5-8268-4396e68a0605",
    "hashtags": ["world"],
    "commentingEnabled": true,
    "tagIds": ["191dcdb7-9319-456d-9a66-eba05ef87bb7"],
    "relatedPostIds": ["07f89894-5ce2-4736-9793-b36ec4719d96"],
    "language": "en",
    "richContent": {
      "nodes": [
        {
          "type": "PARAGRAPH",
          "id": "pvirv1",
          "nodes": [
            {
              "type": "TEXT",
              "textData": { "text": "Hello world", "decorations": [] }
            }
          ]
        }
      ]
    }
  },
  "fieldsets": ["URL", "RICH_CONTENT"]
}
```

### Exemplo - cURL

```bash
curl -X POST \
  'https://www.wixapis.com/blog/v3/draft-posts/' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: <AUTH>' \
  -d '{
        "draftPost": {
          "title": "Hello, world!",
          "featured": true,
          "categoryIds": ["10a5d26e-5028-4f74-92be-e5163c06b58b"],
          "memberId": "8a8b9b73-4da8-47a5-8268-4396e68a0605",
          "hashtags": ["world"],
          "commentingEnabled": true,
          "tagIds": ["191dcdb7-9319-456d-9a66-eba05ef87bb7"],
          "relatedPostIds": ["07f89894-5ce2-4736-9793-b36ec4719d96"],
          "language": "en"
        },
        "fieldsets": ["URL", "RICH_CONTENT"]
      }'
```

### Resposta - JSON

```json
{
  "draftPost": {
    "id": "90216f8c-92a2-42ba-9665-8845358f76c9",
    "title": "Hello, world!",
    "featured": true,
    "categoryIds": ["10a5d26e-5028-4f74-92be-e5163c06b58b"],
    "memberId": "8a8b9b73-4da8-47a5-8268-4396e68a0605",
    "commentingEnabled": true,
    "status": "UNPUBLISHED",
    "url": {
      "base": "https://hello.wixsite.com/blog",
      "path": "/post/hello-world"
    },
    "createdDate": "2024-03-01T14:41:29.991Z",
    "richContent": {
      "nodes": [
        {
          "type": "PARAGRAPH",
          "id": "pvirv1",
          "nodes": [
            {
              "type": "TEXT",
              "textData": { "text": "Hello world", "decorations": [] }
            }
          ]
        }
      ]
    }
  }
}
```

### Eventos Disparados

* **Draft Post Created**
* **Draft Deleted**
* **Draft Post Updated**

---

## Erros

Este método não retorna erros personalizados, apenas os **erros padrão do Wix**.

---

📌 **Referência:** [Documentação Oficial Wix API](https://dev.wix.com/)

```

---

Quer que eu já quebre esse **Markdown em múltiplos arquivos (ex: `overview.md`, `draft-posts.md`, etc.)** ou prefere tudo em um só documento?
```
