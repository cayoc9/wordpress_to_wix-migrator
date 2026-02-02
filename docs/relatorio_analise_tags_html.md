### **Relatório de Análise de Tags HTML para Migração WordPress para Wix**

**1. Introdução**

O objetivo desta análise foi realizar um levantamento exploratório das tags HTML presentes no arquivo `Posts-Export-2025-July-25-1838.csv`. A finalidade é categorizar as tags, entender sua frequência e complexidade, e fornecer um guia estratégico para a migração do conteúdo para o formato Rich Content da plataforma Wix.

**2. Resumo da Análise de Frequência**

A análise do conteúdo revelou um uso intenso de um conjunto específico de tags, indicando um padrão de conteúdo focado em texto, imagens e links. As tags mais frequentes, em ordem aproximada de ocorrência, são:

1. `<span>` (principalmente para estilização de fontes)
2. `<a>` (links)
3. `<p>` (parágrafos)
4. `<img>` (imagens)
5. `<b>` e `<strong>` (negrito)
6. `<h4>`, `<h3>`, `<h2>` (títulos)
7. `<li>`, `<ul>`, `<ol>` (listas)
8. `<iframe>` (conteúdo embutido, como vídeos do YouTube)
9. Shortcodes como `[caption]`

A alta frequência da tag `<span>` com o atributo `style` sugere que muito do estilo do texto é aplicado diretamente no HTML, o que exigirá atenção durante a migração.

**3. Categorização das Tags e Complexidade de Migração**

As tags foram agrupadas em três categorias com base na complexidade de sua conversão para o formato Rich Content.

---

#### **Grupo 1: Conversão Simples (Baixo Risco)**

Estas tags possuem um mapeamento direto para elementos padrão em editores de Rich Content e podem ser convertidas de forma automatizada com alta confiabilidade.

* **Tags:** `<p>`, `<b>`, `<strong>`, `<i>`, `<em>`, `<u>`, `<ul>`, `<ol>`, `<li>`, `<br>`, `<h1>` a `<h6>`
* **Análise:**
  * `<p>`: Mapeia diretamente para parágrafos.
  * `<b>`, `<strong>`: Mapeiam para texto em **negrito**.
  * `<i>`, `<em>`: Mapeiam para texto em *itálico*.
  * `<ul>`, `<ol>`, `<li>`: Mapeiam diretamente para listas com marcadores ou numeradas.
  * `<h1>` - `<h6>`: Mapeiam para os respectivos níveis de título.
* **Recomendação:** A conversão destas tags pode ser totalmente automatizada. Um script simples de "procurar e substituir" ou um parser básico de HTML pode lidar com elas eficientemente.

---

#### **Grupo 2: Conversão Moderada (Risco Médio)**

Estas tags são padrão, mas sua conversão exige a extração e o tratamento de atributos (como URLs de links e imagens) ou a recriação de uma estrutura mais complexa (como tabelas).

* **Tags:** `<a>`, `<img>`, `<span>` (com atributo `style`), `<table>`, `<blockquote>`
* **Análise:**
  * `<a>`: Requer a extração do texto do link e do atributo `href` para recriar o hiperlink.
  * `<img>`: É necessário extrair o `src` (URL da imagem), `alt` (texto alternativo) e, crucialmente, analisar os atributos `class` (ex: `aligncenter`, `size-large`) para mapear o alinhamento e o tamanho da imagem no Wix.
  * `<span>`: A tag mais comum nos seus posts. A maioria dos usos é para aplicar estilo inline (ex: `style="font-weight: 400;"`). A migração exige um parser de CSS para traduzir essas regras de estilo para as propriedades equivalentes no Rich Content do Wix.
  * `<table>`: Requer a recriação da estrutura de tabela, com suas linhas (`<tr>`) e células (`<td>`), o que exige uma lógica de parsing mais elaborada.
* **Recomendação:** A conversão pode ser automatizada, mas necessita de um parser de HTML mais robusto (como BeautifulSoup em Python) que possa ler e interpretar os atributos de cada tag. É essencial testar exaustivamente para garantir que os estilos e links não sejam perdidos.

---

#### **Grupo 3: Conversão Complexa (Alto Risco e Ação Manual)**

Este grupo contém tags e códigos que não são HTML padrão ou que envolvem conteúdo dinâmico. Eles representam o maior desafio para a migração e, provavelmente, exigirão soluções customizadas ou intervenção manual.

* **Tags/Elementos:** `<iframe>`, `<script>`, `<style>`, e **Shortcodes** (`[caption]`, `[button]`, `[embed]`, etc.)
* **Análise:**
  * `<iframe>`, `<script>`: São um grande risco de segurança e **quase certamente serão bloqueados** pela plataforma Wix. A funcionalidade de scripts não poderá ser migrada. Para `<iframe>` de vídeos (como YouTube), a única solução viável é extrair a URL do vídeo do atributo `src` e usar um componente de vídeo nativo do Wix para incorporá-lo.
  * **Shortcodes (`[caption]`, `[button]`)**: Estes **não são HTML**. São códigos específicos do WordPress que são processados pelo sistema antes de exibir a página. Eles não têm significado fora do WordPress e exigem uma lógica de parsing customizada.
    * `[caption]`: Geralmente envolve uma imagem e um texto de legenda. O script de migração precisa identificar este shortcode, extrair a imagem e o texto, e recriá-los como uma imagem com legenda no Wix.
    * `[button]`: Precisa ser convertido para um elemento de botão no Wix, extraindo o texto e o link do shortcode.
* **Recomendação:**
  * **Scripts e Estilos:** Devem ser descartados. Qualquer funcionalidade essencial provida por eles precisará ser recriada usando as ferramentas nativas do Wix.
  * **Iframes:** Crie uma função específica para identificar iframes de plataformas conhecidas (YouTube, Vimeo) e convertê-los para os respectivos blocos de vídeo do Wix. Outros iframes provavelmente terão que ser convertidos em links.
  * **Shortcodes:** O tratamento de shortcodes é o ponto mais crítico e que exige mais esforço. É preciso mapear cada shortcode usado, entender o que ele gera e criar uma função de parsing específica para converter sua estrutura para um elemento equivalente no Wix.

**4. Conclusão e Estratégia Recomendada**

A análise indica que a maior parte do conteúdo textual e de mídia dos posts pode ser migrada de forma semi-automatizada. O principal desafio e onde o esforço de desenvolvimento deve ser focado é no tratamento das tags de **Grupo 3**, especialmente os **shortcodes** e **iframes**.

**Estratégia Sugerida:**

1. **Fase 1 (Migração em Massa Automatizada):** Desenvolva um script que trate as tags dos **Grupos 1 e 2**. Isso migrará a grande maioria do conteúdo (textos, formatação, listas, links e imagens básicas).
2. **Fase 2 (Desenvolvimento de Parsers Customizados):** Crie funções específicas para tratar os shortcodes mais frequentes (`[caption]`, `[button]`, etc.) e para converter iframes de vídeo em elementos de vídeo nativos.
3. **Fase 3 (Revisão e Ajuste Manual):** Após a migração automatizada, planeje uma fase de revisão manual para os posts mais complexos ou para aqueles onde os scripts falharam, garantindo a qualidade e a fidelidade do conteúdo migrado.
