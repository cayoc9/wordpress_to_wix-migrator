# Guia de Conteúdo Rico (Ricos) do Wix

Este documento fornece exemplos da estrutura JSON para a criação de elementos de conteúdo rico no Wix, especificamente para links e vídeos. Este formato é conhecido como Ricos.

Para mais detalhes e para experimentar diferentes tipos de conteúdo, você pode usar o [Ricos Playground](https://ricos.dev).

## Tipos de Nós Suportados em Posts de Blog

Ao criar posts de blog no Wix, os seguintes tipos de nós de conteúdo rico são suportados. Usar estes tipos garantirá que seu conteúdo seja exibido corretamente.

*   `PARAGRAPH` (parágrafo)
*   `HEADING` (cabeçalho)
*   `IMAGE` (imagem, requer o upload prévio para o Wix Media)
*   `VIDEO` (vídeo, como os do YouTube)
*   `ORDERED_LIST` (lista ordenada)
*   `BULLETED_LIST` (lista com marcadores)
*   `BLOCKQUOTE` (bloco de citação)
*   `LIST_ITEM` (item de lista)
*   Decoração `LINK` (aplicada a um nó de texto)


## Links

Para criar um link, você precisa usar uma decoração `LINK` em um nó de `TEXT`.

**Exemplo de JSON:**

```json
{
  "nodes": [
    {
      "type": "PARAGRAPH",
      "id": "p1",
      "nodes": [
        {
          "type": "TEXT",
          "id": "t1",
          "nodes": [],
          "textData": {
            "text": "Clique aqui para visitar o Wix",
            "decorations": [
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
            ]
          }
        }
      ]
    }
  ],
  "metadata": {
    "version": 1,
    "createdTimestamp": "2025-08-31T12:00:00.000Z",
    "updatedTimestamp": "2025-08-31T12:00:00.000Z"
  }
}
```

## Vídeos

Para incorporar um vídeo, você usa um nó `VIDEO`. Você precisa fornecer a URL de origem do vídeo e também pode incluir uma miniatura.

**Exemplo de JSON para um vídeo do YouTube:**

```json
{
  "nodes": [
    {
      "type": "VIDEO",
      "id": "v1",
      "videoData": {
        "video": {
          "src": {
            "url": "https://www.youtube.com/watch?v=your_video_id"
          }
        },
        "thumbnail": {
          "src": {
             "url": "https://i.ytimg.com/vi/your_video_id/hqdefault.jpg"
          },
          "width": 480,
          "height": 360
        }
      }
    }
  ],
  "metadata": {
    "version": 1,
    "createdTimestamp": "2025-08-31T12:00:00.000Z",
    "updatedTimestamp": "2025-08-31T12:00:00.000Z"
  }
}
```
