# Revisão Crítica do Parser Ricos (src/parsers/ricos_parser.py) e Plano de Evolução

> Escopo: análise técnica do conversor HTML → Ricos, mapeamento de lacunas, estratégias de melhoria, plano de ação, riscos e questões em aberto para pesquisa/validação.

- Data: 2025-08-26
- Artefatos relacionados:
  - docs/relatorio_analise_tags_html.md
  - docs/wix_blog_api_limitations.md
  - docs/posts_wordpress.csv (gerado a partir de main.ipynb)

---

## TL;DR

- O parser cobre bem elementos básicos (parágrafos, títulos, listas simples, imagens simples, blockquote) e decorações inline (bold/italic/underline/link, cor, bg, tamanho de fonte).
- Faltam mapeamentos críticos: iframes/embeds (YouTube/Vimeo), quebras de linha dentro de parágrafos, divisores (hr), blocos de código (pre/code), tabelas (fallback), imagens linkadas, sup/sub/risco, alinhamento e tamanhos vindos de classes do WordPress.
- Há lógica duplicada para figure/figcaption, nomenclatura potencialmente inconsistente para listas, e parâmetros não utilizados (embed_strategy). Falta uma função de stripping (strip_html_nodes) para modo estrito sem HTML.
- Plano: adicionar suporte a embeds e código, normalizar listas e quebras, recursar DIV, consolidar figure, melhorar imagens e links, introduzir strip_html_nodes e testes direcionados.

---

## Estado Atual (resumo do comportamento)

- Parágrafos `<p>`: consolidação de inline em um único PARÁGRAFO, com `textAlignment` (alinhamento justificado por padrão) e suporte a estilos inline básicos (cor, bg, font-size, line-height).
- Títulos `<h1..h6>`: mapeados para `HEADING` com nível e `textAlignment`.
- Listas `<ul>/<ol>/<li>`: mapeadas para `BULLETED_LIST` ou `ORDERED_LIST`; cada item contém um `PARAGRAPH`. Profundidade/indentação definida como 0 (sem hierarquia real).
- Citações `<blockquote>`: convertidas para `BLOCKQUOTE` contendo parágrafos.
- Imagens `<img>`: usa `imageData.image.src.id` a partir de `image_importer`; define largura/altura se presentes.
- Figure/Figcaption: há tratamento, porém com duplicação de código.
- Quebras `<br>`: geram nós `LINE_BREAK` como blocos top-level (e também dentro de `<p>` são flush + `LINE_BREAK`).
- Tabelas `<table>` e similares: convertidas para nós `HTML` (fallback).
- Tags desconhecidas: convertidas para nós `HTML` (fallback) com container de largura custom.

Notas:
- `embed_strategy` é aceito na assinatura, mas não é usado dentro do parser.
- `__all__` e importações em `src/parsers/__init__.py` sugerem `strip_html_nodes`, mas essa função não existe.

---

## Lacunas e Pontos Deficientes

- Embeds/Iframes
  - Ausente: `<iframe>` não é tratado; conteúdo embutido (YouTube/Vimeo, etc.) é perdido.
  - Sem estratégia configurável (html_iframe, vídeo nativo, link de fallback).

- Listas
  - Uso de `BULLETED_LIST` vs `UNORDERED_LIST` pode divergir do esquema aceito. Validar nomenclatura.
  - Profundidade real (listas aninhadas) não é preservada (`depth/indent = 0`).

- Quebras e divisores
  - `<br>` vira nó `LINE_BREAK` top-level; ideal é quebra dura dentro do parágrafo (HARD_BREAK ou equivalente aceito).
  - `<hr>` cai em fallback `HTML`; mapear para `DIVIDER`.

- Código e pré-formatação
  - `<pre>`/`<code>` tratados como `HTML`; deveria existir `CODE_BLOCK` com linguagem (quando inferível, ex.: `class="language-xxx"`).

- Tabelas
  - Fallback para `HTML` sem estratégia caso a API rejeite. Necessário plano de degradação (ex.: texto tabular simples) ou confirmação de suporte a HTML para tabelas.

- Imagens
  - Não lê classes/alinhamento/size do WP (ex.: `aligncenter`, `size-large`) para `containerData.alignment` e largura.
  - `<a><img/></a>` (imagem clicável) não recebe link no componente de imagem.
  - Lógica duplicada/fragmentada para `<figure>`/`<figcaption>`.

- Texto e estilos
  - Faltam decorações: STRIKETHROUGH (s/del/strike, text-decoration: line-through), SUPERSCRIPT, SUBSCRIPT.
  - Links ignoram `target`, `rel`, `title`; URLs relativas não são normalizadas.
  - `line-height` é passado como string; confirmar formato aceito.

- Containers e outros
  - `<div>` cai em `HTML`; comum em WP para agrupamento; deveria recursar/"flatten" os filhos.
  - Logs com `print` na lib; preferível logger ou flag de debug.

- Compatibilidade e contratos
  - `embed_strategy` não aplicado; `allow_html_iframe` (no migrator) sem efeito real.
  - Ausência de `strip_html_nodes(rich)` para modo estrito (remover nós `HTML`/embeds quando necessário).

---

## Estratégias de Evolução (prioridades)

1) Compatibilidade e segurança
- Implementar `strip_html_nodes(rich)` para remover nós `HTML` e quaisquer embeds quando a API rejeitar ou quando `allow_html_iframe=False`.
- Usar `embed_strategy` de fato: `html_iframe` (nó HTML seguro), `video` (mapa nativo), `link` (fallback para link simples).

2) Conteúdo crítico
- Iframes/Embeds: detectar YouTube/Vimeo e mapear para `VIDEO` nativo (estrutura a confirmar). Demais iframes → seguir `embed_strategy`.
- Listas: normalizar não numeradas para `UNORDERED_LIST` (ou conforme esquema aceito) e calcular `depth/indent` reais.
- Quebras e divisores: `<br>` como quebra dura dentro do parágrafo; `<hr>` → `DIVIDER`.
- Código: `<pre>/<code>` → `CODE_BLOCK` com tentativa de identificar linguagem por `class`.

3) Qualidade de conversão
- DIV: recursar/“flatten” o conteúdo em vez de cair em `HTML`.
- Figure/Figcaption: consolidar lógica e centralizar caption.
- Imagens: mapear classes WP (`align*`, `size-*`) para `containerData.alignment` e largura; suportar imagem clicável (`<a><img/></a>`).
- Texto: adicionar STRIKETHROUGH, SUPERSCRIPT, SUBSCRIPT; enriquecer metadados de link (target/rel/title); normalizar URLs.

4) Observabilidade e testes
- Substituir `print` por logger com níveis ou `debug=True` no conversor.
- Testes unitários para cobertura de tags principais e casos-limite; snapshot básico do payload conforme aceitação da API.

---

## Plano de Ação (detalhado)

- Infra/Contratos
  - [ ] Criar `strip_html_nodes(rich)` em `src/parsers/ricos_parser.py`.
  - [ ] Ajustar `src/parsers/__init__.py` para exportar corretamente funções existentes.
  - [ ] Em `create_draft_post`, aplicar `allow_html_iframe`: ao receber erro de validação relacionado a HTML, re-tentar com `richContent` “stripped”.

- Mapeamentos de conteúdo
  - [ ] Listas: normalizar tipo (UNORDERED_LIST) e calcular profundidade real.
  - [ ] `<br>`: quebra dura no parágrafo (evitar `LINE_BREAK` top-level), respeitando `<p>` com múltiplas linhas.
  - [ ] `<hr>`: mapear para `DIVIDER`.
  - [ ] `<div>`: “flatten” recursivo para filhos conhecidos.
  - [ ] `<pre>/<code>`: `CODE_BLOCK` (+ linguagem opcional).
  - [ ] `<iframe>`: YouTube/Vimeo → `VIDEO`; demais seguem `embed_strategy`.
  - [ ] `<figure>/<figcaption>`: consolidar e remover duplicações.
  - [ ] `<a><img/></a>`: imagem clicável (link no bloco de imagem ou estratégia suportada).
  - [ ] Texto: STRIKETHROUGH/SUP/SUB; link `target/rel/title`.
  - [ ] Tabelas: manter `HTML` por ora; se API rejeitar, degradar para texto tabular simples.

- Observabilidade/QA
  - [ ] Flag `debug` (ou logger) no conversor para logs controlados.
  - [ ] Testes pytest:
    - [ ] Parágrafos e títulos (alinhamento, estilos inline básicos).
    - [ ] Listas aninhadas (depth/indent).
    - [ ] Link + imagem (imagem clicável).
    - [ ] Figure + figcaption (caption centralizado).
    - [ ] Iframe YouTube (vídeo nativo) e iframe genérico (fallback conforme `embed_strategy`).
    - [ ] Code block (com e sem linguagem).
    - [ ] Quebras `<br>` dentro do parágrafo; `<hr>` como `DIVIDER`.
    - [ ] Tabela (HTML) e fallback em modo estrito.

- Documentação
  - [ ] Atualizar docs/relatorio_analise_tags_html.md com status de suporte.
  - [ ] Criar doc curto descrevendo `embed_strategy`, `allow_html_iframe` e “modo estrito”.

---

## Riscos e Mitigações

- Rejeição a nós `HTML`/embeds pela API
  - Mitigar com `strip_html_nodes` e re-tentativa automática; fallback para link simples quando necessário.

- Inconsistências no esquema Ricos aceito
  - Validar com uma postagem de teste via scripts/update_wix_post.py; ajustar nomenclaturas (ex.: UNORDERED_LIST) e estruturas conforme respostas da API.

- Degradação de tabelas
  - Confirmar aceitação de `HTML` com `<table>`; se rejeitado, converter para texto tabular legível ou snapshot de imagem (se aceitável).

- Performance em HTMLs longos
  - Minimizar re-parses, limitar profundidade recursiva, e escrever testes com amostras grandes (do CSV) para validar tempo de execução.

---

## Questões em Aberto (pesquisa/validação)

- Quais tipos de lista são aceitos canonicamente hoje? `UNORDERED_LIST` vs `BULLETED_LIST`.
- Quebra de linha: existe `HARD_BREAK`/decorador no texto ou aceita `LINE_BREAK` como bloco?
- Esquema de `CODE_BLOCK`: quais campos mínimos? como declarar `language`?
- Plugin de vídeo: estrutura para YouTube/Vimeo (url/origem vs `embedId`).
- Imagem clicável: o componente de imagem aceita link nativo? Em que campo?
- Limites de tamanho/complexidade para `richContent` (número de nós, profundidade, bytes).
- A API v3 aceita nós `HTML` contendo `<table>` de forma estável?

---

## Próximos Passos Imediatos (sugeridos)

1) Infra e compatibilidade: `strip_html_nodes`, correções de export em `__init__`, aplicar `allow_html_iframe` no migrator.
2) Normalizar listas e resolver duplicação `figure/figcaption`.
3) Implementar `<hr>` → `DIVIDER`, `<br>` como quebra dura, `<div>` flatten.
4) Adicionar suporte a `<pre>/<code>` → `CODE_BLOCK` e iframe YouTube/Vimeo → `VIDEO`.
5) Criar 2–3 testes pytest cobrindo os casos acima e rodar validação manual com `scripts/update_wix_post.py` num draft de teste.

---

### Observação sobre Consistência de Exports

- `src/parsers/__init__.py` atualmente expõe `strip_html_nodes` em `__all__` mas não a importa; e `src/migrators/wix_migrator.py` cita `strip_html_nodes` apenas em docstring. Ao implementar `strip_html_nodes`, alinhar `__all__`/imports para evitar `ImportError` futuros.

