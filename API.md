Perfeito 🔥 então vamos fechar isso de vez:

Para você conseguir **usar o POST `Create Draft Post` no Blog**, precisa ter em mãos **todos os objetos relacionados** que o Blog exige como referência. Eu já te mostrei a documentação de cada parte, mas aqui vai o **pacote consolidado só com o que realmente é necessário para Blog**.

---

# 📖 Guia — Tudo necessário para usar `Create Draft Post`

---

## 🔑 1. Autenticação

Antes de qualquer chamada:

* Criar App no [Wix Developers](https://dev.wix.com/).
* Ativar **App Instance**.
* Instalar em um site (gera `instance_id`).
* Obter **Access Token** via OAuth2:

```bash
curl -X POST \
  'https://www.wixapis.com/oauth/access' \
  -H 'Content-Type: application/json' \
  -d '{
    "grant_type": "client_credentials",
    "client_id": "<APP_ID>",
    "client_secret": "<APP_SECRET>",
    "instance_id": "<INSTANCE_ID>"
  }'
```

Esse token vai no header:

```http
Authorization: Bearer <ACCESS_TOKEN>
```

---

## 👤 2. Members API (obrigatório → `memberId`)

O `memberId` identifica quem criou o post.
Você precisa criar ou listar membros.

### Criar Membro

```bash
curl -X POST \
  'https://www.wixapis.com/members/v1/members' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>' \
  -d '{
    "member": { "loginEmail": "john@example.com" }
  }'
```

### Listar Membros

```bash
curl -X GET \
  'https://www.wixapis.com/members/v1/members' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>'
```

> ⚠️ Pegue o campo `"id"` do membro e use como `"memberId"` no Blog.

---

## 🏷 3. Tags API (opcional → `tagIds`)

Usado para categorizar posts por tags. Se quiser usar `tagIds`, primeiro crie as tags.

### Criar Tag

```bash
curl -X POST \
  'https://www.wixapis.com/tags/v1/tags' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>' \
  -d '{
    "tag": { "name": "Promoção" }
  }'
```

### Listar Tags

```bash
curl -X GET \
  'https://www.wixapis.com/tags/v1/tags?fqdn=wix.ecom.v1.order' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>'
```

> ⚠️ Pegue o `"id"` da tag para usar em `"tagIds"` no Blog.

---

## 📂 4. Categories API (opcional → `categoryIds`)

Categorias também precisam existir antes.

### Criar Categoria

```bash
curl -X POST \
  'https://www.wixapis.com/faq/v2/categories' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>' \
  -d '{
    "category": {
      "title": "Shipping & Delivery",
      "sort_order": 1.0
    }
  }'
```

### Listar Categorias

```bash
curl -X GET \
  'https://www.wixapis.com/faq/v2/categories' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>'
```

> ⚠️ Pegue o `"id"` da categoria e use em `"categoryIds"` no Blog.

---

## 📝 5. Criar Draft Post (final)

Depois de ter `memberId`, e opcionalmente `categoryIds` e `tagIds`, você pode criar o post:

```bash
curl -X POST \
  'https://www.wixapis.com/blog/v3/draft-posts' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <ACCESS_TOKEN>' \
  -d '{
    "draftPost": {
      "title": "Meu primeiro post via API!",
      "memberId": "8a8b9b73-4da8-47a5-8268-4396e68a0605",
      "categoryIds": ["10a5d26e-5028-4f74-92be-e5163c06b58b"],
      "tagIds": ["191dcdb7-9319-456d-9a66-eba05ef87bb7"],
      "richContent": {
        "nodes": [
          {
            "type": "PARAGRAPH",
            "nodes": [
              {
                "type": "TEXT",
                "textData": { "text": "Olá mundo, esse é meu post automático!" }
              }
            ]
          }
        ]
      }
    },
    "fieldsets": ["URL"]
  }'
```

---

## ✅ Resumindo: o que já precisa existir

1. 🔑 **Access Token** válido (App Instance + OAuth2).
2. 👤 **Membro** (obrigatório → `memberId`).
3. 📂 **Categoria(s)** (opcional → `categoryIds`).
4. 🏷 **Tag(s)** (opcional → `tagIds`).

Com esses elementos em mãos → você já consegue criar posts no Blog.

---

👉 Quer que eu agora monte um **workflow completo passo a passo** (com ordem certinha: criar membro → criar categoria → criar tag → criar post), como se fosse um guia de execução na prática?
