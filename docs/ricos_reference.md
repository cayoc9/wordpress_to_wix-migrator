# Guia de Referência Ricos do Wix

Este documento serve como um guia de referência local para a estrutura de dados Ricos do Wix, com foco na conversão de posts de blog do WordPress.

## Estrutura Base

Um documento Ricos é um objeto JSON com uma estrutura de árvore. A raiz sempre contém uma chave `nodes`, que é um array de "Nós Raiz".

```json
{
  "nodes": [
    // ... Array de Nós Raiz ...
  ],
  "metadata": {
    "version": 1
  },
  "documentStyle": {}
}
```

---

## Nós (Nodes)

Nós são os blocos de construção do conteúdo. Cada nó deve ter um `type` e um `id` único.

### 1. Parágrafo (`PARAGRAPH`)

O nó mais comum, usado para texto simples.

- `type`: `"PARAGRAPH"`
- `nodes`: Um array de `TextNode`s que compõem o parágrafo.
- `paragraphData.textStyle`: Define o alinhamento do texto (`"LEFT"`, `"CENTER"`, `"RIGHT"`).

**Exemplo:**

```json
{
  "type": "PARAGRAPH",
  "id": "p1",
  "nodes": [
    {
      "type": "TEXT",
      "id": "t1",
      "nodes": [],
      "textData": {
        "text": "Este é um parágrafo de exemplo.",
        "decorations": []
      }
    }
  ],
  "paragraphData": {
    "textStyle": {
      "textAlignment": "LEFT"
    }
  }
}
```

### 2. Título (`HEADING`)

Usado para títulos de seção.

- `type`: `"HEADING"`
- `headingData.level`: Nível do título, de `1` (H1) a `6` (H6).
- `nodes`: Array de `TextNode`s.

**Exemplo (H2):**

```json
{
  "type": "HEADING",
  "id": "h1",
  "nodes": [
    {
      "type": "TEXT",
      "id": "t2",
      "nodes": [],
      "textData": {
        "text": "Este é um Título de Nível 2",
        "decorations": []
      }
    }
  ],
  "headingData": {
    "level": 2,
    "textStyle": {
      "textAlignment": "LEFT"
    }
  }
}
```

### 3. Imagem (`IMAGE`)

Para exibir imagens. Requer o plugin de imagem.

- `type`: `"IMAGE"`
- `imageData.containerData`: Define alinhamento, largura e quebra de texto.
- `imageData.image`: Contém a URL da imagem e suas dimensões.
- `imageData.link`: (Opcional) Transforma a imagem em um link.

**Exemplo:**

```json
{
  "type": "IMAGE",
  "id": "img1",
  "nodes": [],
  "imageData": {
    "containerData": {
      "width": {
        "size": "CONTENT"
      },
      "alignment": "CENTER",
      "textWrap": false
    },
    "image": {
      "src": {
        "url": "http://example.com/image.jpg"
      },
      "width": 800,
      "height": 600
    },
    "altText": "Descrição da imagem"
  }
}
```

### 4. Lista com Marcadores (`BULLETED_LIST`)

Cria uma lista não ordenada (`<ul>`).

- `type`: `"BULLETED_LIST"`
- `nodes`: Um array de `ListItemNode`s.

**Exemplo:**

```json
{
  "type": "BULLETED_LIST",
  "id": "ul1",
  "nodes": [
    {
      "type": "LIST_ITEM",
      "id": "li1",
      "nodes": [
        {
          "type": "PARAGRAPH",
          "id": "p2",
          "nodes": [
            {
              "type": "TEXT",
              "id": "t3",
              "nodes": [],
              "textData": { "text": "Item 1", "decorations": [] }
            }
          ]
        }
      ]
    }
  ]
}
```

### 5. Divisor (`DIVIDER`)

Cria uma linha horizontal (`<hr>`).

- `type`: `"DIVIDER"`
- `dividerData.containerData`: Define alinhamento e largura.

**Exemplo:**

```json
{
  "type": "DIVIDER",
  "id": "hr1",
  "nodes": [],
  "dividerData": {
    "containerData": {
      "width": {
        "size": "LARGE"
      },
      "alignment": "CENTER"
    },
    "lineStyle": "SINGLE",
    "width": "LARGE"
  }
}
```

### 6. Bloco de Citação (`BLOCKQUOTE`)

Usado para destacar citações.

- `type`: `"BLOCKQUOTE"`
- `nodes`: Array de `TextNode`s.

**Exemplo:**

```
{
  "type": "BLOCKQUOTE",
  "id": "q1",
  "nodes": [
    {
      "type": "PARAGRAPH",
      "id": "p_in_q1",
      "nodes": [
        { "type": "TEXT", "id": "t_in_q1", "nodes": [], "textData": { "text": "Texto citado", "decorations": [] } }
      ]
    }
  ]
}
```

---

## Mapa HTML → Ricos (nós, plugins, decorações)

Este mapeamento cobre todas as tags encontradas em `data/html_tags_counts.csv`. Use-o ao converter HTML do WordPress para Ricos. Regras estruturais críticas: TEXT sempre dentro de PARAGRAPH; LIST_ITEM contém PARAGRAPH; QUOTE contém PARAGRAPH.

- `p`: nó `PARAGRAPH` com `TEXT`.
- `h1`–`h6`: nó `HEADING` com `headingData.level` 1–6.
- `ul`: nó `BULLETED_LIST`; filhos `LIST_ITEM` → `PARAGRAPH` → `TEXT`.
- `ol`: nó `ORDERED_LIST`; filhos `LIST_ITEM` → `PARAGRAPH` → `TEXT`.
- `li`: mapar para `LIST_ITEM` contendo um `PARAGRAPH`.
- `a`: decoração `LINK` aplicada a `TEXT` (não é nó de bloco).
- `strong`/`b`: decoração `BOLD` em `TEXT`.
- `em`/`i`: decoração `ITALIC` em `TEXT`.
- `u`: decoração `UNDERLINE` em `TEXT`.
- `img`: nó `IMAGE` (usar ID do Wix Media; defina `width`/`height` e `altText`).
- `figure`/`figcaption`: usar nó `IMAGE` + legenda como `PARAGRAPH` adjacente; quando disponível, preferir campo de legenda do plugin de imagem.
- `hr`: nó `DIVIDER`.
- `blockquote`: nó `BLOCKQUOTE` contendo `PARAGRAPH`(s) internos.
- `code`: código inline como decoração `CODE` em `TEXT`; para blocos de código (se houver), usar `CODE_BLOCK`.
- `br`: converter em quebras de parágrafo ou "soft break" dentro do `TEXT` conforme suportado; evitar `TEXT` direto fora de `PARAGRAPH`.
- `iframe`: usar plugin `HTML`/embed apropriado (por exemplo, o viewer lida com provedores compatíveis).
- `table`/`thead`/`tbody`/`tr`/`td`/`th`/`colgroup`/`col`: plugin de `TABLE` (linhas → células). Se indisponível no destino, renderizar como parágrafos com texto tabular.
- `div`/`section`/`span`: não possuem semântica em Ricos; achatar para `PARAGRAPH`/`HEADING` conforme o conteúdo e estilos.
- `button`: não suportado em Ricos; converter para texto com decoração `LINK` (se houver URL) ou texto simples.
- `script`: não suportado por segurança; descartar o conteúdo.

---

## Plugins e Decorações comuns

- Plugins de bloco: `IMAGE`, `GALLERY`, `VIDEO/EMBED`, `HTML`, `TABLE`, `DIVIDER`, `BLOCKQUOTE`, `ORDERED_LIST`, `BULLETED_LIST`.
- Decorações de texto: `BOLD`, `ITALIC`, `UNDERLINE`, `LINK`, `CODE`.

---

## Referências (Wix)

- Renderização com Ricos Viewer e lista/detalhe do Blog: “How to code a Blog Application” (RicosViewer, plugins). https://dev.wix.com/docs/kb-only/MCP_REST_RECIPES_KB_ID/TRAIN_how-to-code-a-blog-application
- Criação de post com `richContent` e regras de aninhamento: “How to create a Blog Post”. https://dev.wix.com/docs/kb-only/MCP_REST_RECIPES_KB_ID/TRAIN_how-to-create-a-blog-post
- Conceitos de Rich Content no SDK: “About Rich Content”. https://dev.wix.com/docs/sdk/articles/work-with-the-sdk/about-rich-content
- Ricos Documents API (conversão/validação): https://dev.wix.com/docs/sdk/backend-modules/rich-content/ricos-documents/introduction

```json
{
  "type": "BLOCKQUOTE",
  "id": "bq1",
  "nodes": [
    {
      "type": "TEXT",
      "id": "t4",
      "nodes": [],
      "textData": {
        "text": "Esta é uma citação inspiradora.",
        "decorations": []
      }
    }
  ]
}
```

### 7. Bloco de Código (`CODE_BLOCK`)

Para exibir snippets de código.

- `type`: `"CODE_BLOCK"`
- `nodes`: Array de `TextNode`s.

**Exemplo:**

```json
{
  "type": "CODE_BLOCK",
  "id": "cb1",
  "nodes": [
    {
      "type": "TEXT",
      "id": "t5",
      "nodes": [],
      "textData": {
        "text": "console.log('Olá, Ricos!');",
        "decorations": []
      }
    }
  ]
}
```

---

## Decorações de Texto (Decorations)

Decorações são aplicadas a `TextNode`s para formatar o texto. Elas ficam dentro do array `textData.decorations`.

### 1. Negrito (`BOLD`)

```json
{
  "type": "BOLD",
  "fontWeightValue": 700
}
```

### 2. Itálico (`ITALIC`)

```json
{
  "type": "ITALIC",
  "italicData": true
}
```

### 3. Sublinhado (`UNDERLINE`)

```json
{
  "type": "UNDERLINE",
  "underlineData": true
}
```

### 4. Link (`LINK`)

- `type`: `"LINK"`
- `linkData.link`: Objeto contendo a URL.

**Exemplo:**

```json
{
  "type": "LINK",
  "linkData": {
    "link": {
      "url": "https://www.wix.com",
      "target": "_blank",
      "rel": "noopener noreferrer"
    }
  }
}
```

**Exemplo de `TextNode` com Múltiplas Decorações:**

```json
{
  "type": "TEXT",
  "id": "t6",
  "nodes": [],
  "textData": {
    "text": "Texto com link em negrito",
    "decorations": [
      {
        "type": "BOLD",
        "fontWeightValue": 700
      },
      {
        "type": "LINK",
        "linkData": {
          "link": { "url": "http://example.com" }
        }
      }
    ]
  }
}
```
