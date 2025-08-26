````markdown
# 📚 Wix Blog & Draft Posts API - Documentação, Casos de Uso e Fluxos

---

## 📝 Introdução
A API de **Blog** e **Draft Posts** do Wix permite criar, gerenciar e publicar posts e rascunhos de forma programática.  
Possibilita automações como notificações por e-mail, publicação automática em redes sociais e integração com outros sistemas.

---

## 📌 Objetivo
Exemplos de automações e integrações usando as **Blog APIs** e **Draft Posts APIs** do Wix para aumentar o engajamento de leitores e a visibilidade do blog.

---

## 💡 Casos de Uso

### 1️⃣ Enviar e-mail periódico com as últimas postagens
**Descrição:**  
Notificar assinantes do blog sobre novos posts publicados desde o último envio.

**Fluxo:**
1. Chamar `Query Posts` filtrando por posts recentes:
   ```json
   {
     "filter": {
       "firstPublishedDate": {
         "$gt": "<PREVIOUS_EMAIL_DATETIME>"
       }
     }
   }
````

2. Extrair do payload:

   * `title`
   * `excerpt`
   * `url`
3. Criar um template de e-mail com as informações extraídas.
4. Enviar para a lista de assinantes.

---

### 2️⃣ Publicar nas redes sociais quando um post for marcado como **featured**

**Descrição:**
Criar automaticamente postagens nas redes sociais sempre que um post for destacado no blog.

**Fluxo:**

1. Monitorar o evento `Post Created`.
2. Ao receber o evento, extrair `entityId`.
3. Chamar `Get Post` usando o `entityId`.
4. Verificar se `featured` está definido como `true`.
5. Caso positivo, extrair:

   * `title`
   * `url`
   * `excerpt`
   * `minutesToRead`
   * `media`
6. Criar e publicar post nas redes sociais com essas informações.

---

## 🛠 Observações

* É necessário ter **permissões** para acessar as contas de redes sociais ao integrar o segundo caso de uso.
* As integrações podem ser executadas periodicamente via **cron job** ou acionadas por eventos (**webhooks**).

---

## ⚙️ Funcionalidades Principais - Draft Posts API

* Criar e atualizar rascunhos (`Create Draft Post`, `Update Draft Post`).
* Publicar rascunhos (`Publish Draft Post`).
* Listar e consultar rascunhos (`List Draft Posts`, `Query Draft Posts`).
* Criar, atualizar e deletar múltiplos rascunhos (`Bulk Create`, `Bulk Update`, `Bulk Delete`).
* Remover rascunhos para a lixeira (`Delete Draft Post`) e restaurar (`Restore From Trash Bin`).
* Acessar posts excluídos (`List Deleted Draft Posts`, `Get Deleted Draft Post`).

---

## 🚫 Limitações

* **Tamanho máximo:** 400KB por rascunho.
* **Categorias:** máximo de 10 por post.
* `translationId` disponível apenas com o app **Multilingual**.
* **Limite de posts no blog:** até 100.000.

---

## 👥 Papéis no Blog

* **Blog editor:** gerencia completamente o blog.
* **Blog writer:** cria e publica seus próprios posts.
* **Guest writer:** cria posts, mas não publica.

---

## 📖 Terminologia

* **Post:** Artigo publicado.
* **Draft Post:** Artigo em rascunho.
* **Category:** Agrupamento de posts.
* **Tag:** Marcador para filtragem de posts.

---

## 🔍 Filtros e Ordenação Suportados

| Campo                     | Filtros Suportados                                                                                                | Ordenável |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------- | --------- |
| **id**                    | `$eq`, `$ne`, `$hasSome`, `$not`                                                                                  | Sim       |
| **title**                 | `$eq`, `$ne`, `$contains`, `$startsWith`, `$endsWith`, `$hasSome`, `$lt`, `$lte`, `$gt`, `$gte`, `$exists`, `$in` | Sim       |
| **excerpt**               | `$eq`, `$ne`, `$contains`, `$startsWith`, `$endsWith`, `$hasSome`, `$lt`, `$lte`, `$gt`, `$gte`, `$exists`, `$in` | Sim       |
| **featured**              | `$eq`, `$ne`                                                                                                      | Sim       |
| **categoryIds**           | `$hasSome`, `$hasAll`                                                                                             | Não       |
| **memberId**              | `$eq`, `$ne`, `$hasSome`                                                                                          | Não       |
| **hashtags**              | `$hasSome`, `$hasAll`                                                                                             | Não       |
| **commentingEnabled**     | `$eq`, `$ne`                                                                                                      | Sim       |
| **minutesToRead**         | `$eq`, `$ne`, `$lt`, `$lte`, `$gt`, `$gte`, `$in`                                                                 | Não       |
| **tagIds**                | `$hasSome`, `$hasAll`                                                                                             | Não       |
| **pricingPlanIds**        | `$hasSome`, `$hasAll`                                                                                             | Não       |
| **translationId**         | `$eq`, `$ne`, `$contains`, `$startsWith`, `$endsWith`, `$hasSome`, `$lt`, `$lte`, `$gt`, `$gte`, `$exists`, `$in` | Não       |
| **language**              | `$eq`, `$ne`, `$contains`, `$startsWith`, `$endsWith`, `$hasSome`, `$lt`, `$lte`, `$gt`, `$gte`, `$exists`, `$in` | Não       |
| **status**                | `$eq`, `$ne`, `$contains`, `$startsWith`, `$endsWith`, `$hasSome`, `$lt`, `$lte`, `$gt`, `$gte`, `$exists`, `$in` | Não       |
| **hasUnpublishedChanges** | `$eq`, `$ne`                                                                                                      | Não       |
| **editedDate**            | `$lt`, `$lte`, `$gt`, `$gte`                                                                                      | Sim       |
| **scheduledPublishDate**  | `$lt`, `$lte`, `$gt`, `$gte`                                                                                      | Sim       |

---

## 🗂 Estrutura do Objeto Draft Post

| Propriedade               | Tipo / Restrições             | Descrição                            |
| ------------------------- | ----------------------------- | ------------------------------------ |
| **id**                    | string, read-only, máx. 38    | ID do rascunho                       |
| **title**                 | string, máx. 200              | Título                               |
| **excerpt**               | string, máx. 500              | Resumo (auto-gerado se não definido) |
| **featured**              | boolean                       | Destaque                             |
| **categoryIds**           | array string, máx. 10 itens   | IDs de categorias                    |
| **memberId**              | string GUID                   | ID do dono                           |
| **hashtags**              | array string, máx. 100        | Hashtags                             |
| **commentingEnabled**     | boolean                       | Comentários habilitados              |
| **minutesToRead**         | integer, read-only            | Tempo estimado de leitura            |
| **heroImage**             | objeto HeroImage              | Imagem principal                     |
| **tagIds**                | array string, máx. 30         | IDs de tags                          |
| **relatedPostIds**        | array string, máx. 3          | IDs de posts relacionados            |
| **pricingPlanIds**        | array string GUID, máx. 100   | IDs de planos pagos                  |
| **translationId**         | string GUID                   | ID de tradução                       |
| **language**              | string (IETF BCP 47)          | Idioma                               |
| **richContent**           | objeto RichContent            | Conteúdo estruturado                 |
| **status**                | string                        | Status do rascunho                   |
| **hasUnpublishedChanges** | boolean, read-only            | Alterações não publicadas            |
| **editedDate**            | string (date-time), read-only | Data última edição                   |
| **scheduledPublishDate**  | string (date-time)            | Data agendada                        |
| **firstPublishedDate**    | string (date-time)            | Data da primeira publicação          |
| **seoData**               | objeto SeoData                | Metadados SEO                        |
| **url**                   | objeto Url                    | Prévia da URL                        |
| **createdDate**           | string (date-time), read-only | Data de criação                      |
| **seoSlug**               | string, máx. 100              | Slug SEO                             |
| **media**                 | objeto Media                  | Mídia de capa                        |
| **previewTextParagraph**  | integer ≥ 0                   | Parágrafos visíveis na prévia paga   |

---

## 📌 Casos de Uso para Automação com Draft Posts

### 1️⃣ Enviar e-mail para assinantes ao criar um post

**Objetivo:** Notificar assinantes automaticamente quando um novo post for criado.

**Fluxo:**

1. **Monitorar evento** `Post Created`.
2. Obter `entityId` do evento.
3. Chamar **Get Post** com `entityId`.
4. Extrair:

   * `title`
   * `excerpt`
   * `url`
5. Criar template de e-mail com as informações.
6. Enviar para assinantes.

---

### 2️⃣ Publicar nas redes sociais quando um post for destacado

**Objetivo:** Criar postagens automáticas nas redes sociais para posts destacados.

**Fluxo:**

1. **Monitorar evento** `Post Created`.
2. Obter `entityId` do evento.
3. Chamar **Get Post** com `entityId`.
4. Verificar se `featured` é **true**.
5. Se sim, extrair:

   * `title`
   * `url`
   * `excerpt`
   * `minutesToRead`
   * `media`
6. Criar e publicar post nas redes sociais.

---

## 🛠 Observações Importantes

* É necessário ter permissões para acessar redes sociais ao usar o segundo caso.
* Integrações podem ser executadas periodicamente (**cron**) ou acionadas por eventos (**webhooks**).

```

Se quiser, posso **acrescentar agora um bloco com os endpoints REST e exemplos de requisição prontos** para esses dois fluxos, para que sua IA consiga já executar as chamadas automaticamente. Quer que eu já adicione isso na mesma estrutura?
```
