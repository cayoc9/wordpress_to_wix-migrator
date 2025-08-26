"""
HTML → Ricos converter utilities

Este módulo oferece funções para converter HTML (string) em uma estrutura de
nodos compatível com o editor Ricos (Wix). É pensado para uso em pipelines que
recebem conteúdo HTML (ex.: importação de posts do WordPress) e precisam gerar
um JSON de nodos Ricos com suporte a:

- Parágrafos (p), headings (h1..h6)
- Listas ordenadas/desordenadas (ol/ul) com aninhamento (depth)
- Imagens (img / figure / figcaption) via callback `image_importer(src) -> media_id`
- Blockquotes
- Quebras de linha (<br>)
- Shortcodes de legenda do WP: [caption] ... [/caption] → <figure><figcaption>...
- Inline decorations: bold/italic/underline/link, além de algumas propriedades inline de estilo
  (color, background-color, font-size em px, text-decoration: underline).

Limitações / notas:
- Tabelas são convertidas para nodos HTML (embed) porque Ricos não mapeia tabelas nativamente.
- Font-sizes em units diferentes de "px" não são convertidos automaticamente.
- O parâmetro `embed_strategy` existe para compatibilidade com versões anteriores, mas não é usado na conversão.
- Para importar imagens é esperado um callable image_importer(src: str) -> Optional[str]
  que devolva um `media_id` (string) ou None se falhar.
"""

from typing import Any, Callable, Dict, List, Optional
import re
import uuid
import logging

from bs4 import BeautifulSoup
from bs4.element import NavigableString


__all__ = [
    "convert_html_to_ricos",
    "generate_ricos_id",
]

logger = logging.getLogger(__name__)

def generate_ricos_id() -> str:
    """
    Gera um ID curto para nodos Ricos.

    Usa os primeiros 12 caracteres hexadecimais de uuid4().hex.
    """
    return uuid.uuid4().hex[:12]


def _get_text_alignment(element: Any) -> Optional[str]:
    """
    Extrai alinhamento de texto de `style` inline ou atributo `align`.
    Retorna um dos valores: "CENTER", "JUSTIFY", "LEFT", "RIGHT", ou None.
    """
    style = element.get("style")
    if style:
        match = re.search(r"text-align:\s*(center|justify|left|right)\b;?", style, flags=re.IGNORECASE)
        if match:
            align = match.group(1).upper()
            if align in ["CENTER", "JUSTIFY", "LEFT", "RIGHT"]:
                return align

    # atributo align (deprecated)
    align_attr = element.get("align")
    if align_attr:
        align_attr = align_attr.strip().upper()
        if align_attr in ["CENTER", "JUSTIFY", "LEFT", "RIGHT"]:
            return align_attr

    return None


def _get_inline_styles(element: Any) -> Dict[str, str]:
    """
    Parse simples do atributo style inline -> dict {prop: value}.
    Ex.: 'color: red; font-size: 14px' -> {"color": "red", "font-size": "14px"}
    """
    style_attr = element.get("style")
    styles: Dict[str, str] = {}
    if style_attr:
        for style_pair in style_attr.split(";"):
            if ":" in style_pair:
                prop, value = style_pair.split(":", 1)
                prop = prop.strip().lower()
                value = value.strip()
                if prop:
                    styles[prop] = value
    return styles


def _get_text_nodes_with_decorations(element: Any) -> List[Dict[str, Any]]:
    """
    Extrai os nós de texto de um elemento (BeautifulSoup) e aplica decorações
    baseadas em tags inline (strong/b, em/i, u, a, span) e estilos inline.
    """
    text_nodes: List[Dict[str, Any]] = []
    inline_styles = _get_inline_styles(element)

    for child in element.contents:
        # Texto puro
        if isinstance(child, NavigableString):
            raw = str(child)
            if raw.strip():
                node = {
                    "type": "TEXT",
                    "textData": {
                        "text": raw,
                        "decorations": []
                    }
                }
                # aplicar estilos diretos do elemento pai (ex.: <span style="color:...">texto</span>)
                if "text-decoration" in inline_styles and "underline" in inline_styles["text-decoration"]:
                    node["textData"]["decorations"].append({"type": "UNDERLINE"})
                if "color" in inline_styles:
                    node["textData"]["decorations"].append({"type": "COLOR", "colorData": {"foreground": inline_styles["color"]}})
                if "background-color" in inline_styles:
                    node["textData"]["decorations"].append({"type": "COLOR", "colorData": {"background": inline_styles["background-color"]}})
                if "font-size" in inline_styles:
                    # tenta extrair só pixels (se houver outra unidade, ignora)
                    fs = inline_styles["font-size"]
                    px_match = re.match(r"([\d.]+)px$", fs)
                    if px_match:
                        try:
                            node["textData"]["decorations"].append({
                                "type": "FONT_SIZE",
                                "fontSizeData": {"value": float(px_match.group(1)), "unit": "PX"}
                            })
                        except ValueError:
                            pass
                text_nodes.append(node)

        # strong / b
        elif child.name in ["strong", "b"]:
            for tn in _get_text_nodes_with_decorations(child):
                tn.get("textData", {}).setdefault("decorations", []).append({"type": "BOLD"})
                text_nodes.append(tn)

        # em / i
        elif child.name in ["em", "i"]:
            for tn in _get_text_nodes_with_decorations(child):
                tn.get("textData", {}).setdefault("decorations", []).append({"type": "ITALIC"})
                text_nodes.append(tn)

        # underline tag
        elif child.name == "u":
            for tn in _get_text_nodes_with_decorations(child):
                tn.get("textData", {}).setdefault("decorations", []).append({"type": "UNDERLINE"})
                text_nodes.append(tn)

        # links
        elif child.name == "a":
            href = child.get("href")
            if href:
                for tn in _get_text_nodes_with_decorations(child):
                    tn.get("textData", {}).setdefault("decorations", []).append({
                        "type": "LINK",
                        "linkData": {"url": href}
                    })
                    text_nodes.append(tn)
            else:
                # sem href: apenas propaga filhos
                text_nodes.extend(_get_text_nodes_with_decorations(child))

        # span (pode ter estilos próprios)
        elif child.name == "span":
            # recursão: a chamada trata estilos inline do próprio span
            text_nodes.extend(_get_text_nodes_with_decorations(child))

        # br: tratado por quem agrupa parágrafos (não transformar em espaço aqui)
        elif child.name == "br":
            pass

        # qualquer outra tag inline inesperada
        else:
            txt = child.get_text(strip=True) if hasattr(child, "get_text") else ""
            if txt:
                text_nodes.append({
                    "type": "TEXT",
                    "textData": {"text": txt, "decorations": []}
                })

    return text_nodes


def _convert_html_element_to_ricos_nodes(element: Any,
                                        image_importer: Optional[Callable[[str], Optional[str]]] = None,
                                        paragraph_spacing_px: Optional[int] = None,
                                        list_depth: int = 0) -> List[Dict[str, Any]]:
    """
    Converte um elemento BeautifulSoup (block-level) em lista de nodos Ricos.
    `list_depth` é usado para indicar aninhamento em listas (0 = top-level).
    """
    ricos_nodes: List[Dict[str, Any]] = []
    # soup temporário para criar tags auxiliares quando necessário
    temp_soup = BeautifulSoup("", "html.parser")

    if isinstance(element, NavigableString):
        return ricos_nodes

    inline_styles = _get_inline_styles(element)
    text_style_data: Dict[str, Any] = {}
    if "line-height" in inline_styles:
        text_style_data["lineHeight"] = inline_styles["line-height"]

    node_style_data: Dict[str, Any] = {}
    if paragraph_spacing_px is not None:
        node_style_data["paddingBottom"] = f"{paragraph_spacing_px}px"
    if "padding-top" in inline_styles:
        node_style_data["paddingTop"] = inline_styles["padding-top"]

    tag = getattr(element, "name", None)

    # ------------------------------------------------------------
    # Parágrafo (agrupa inline children, respeita <br>)
    # ------------------------------------------------------------
    if tag == "p":
        inline_buffer: List[Any] = []

        def flush_paragraph_buffer():
            nonlocal inline_buffer
            if not inline_buffer:
                inline_buffer = []
                return

            temp_p = temp_soup.new_tag("p")
            for item in inline_buffer:
                # Se item foi extraído de outro lugar, extract() preserva a sub-árvore
                try:
                    temp_p.append(item.extract())
                except Exception:
                    temp_p.append(item)

            paragraph_content_nodes = _get_text_nodes_with_decorations(temp_p)
            if paragraph_content_nodes:
                paragraph_node = {
                    "type": "PARAGRAPH",
                    "nodes": paragraph_content_nodes,
                    "paragraphData": {"textStyle": {"textAlignment": _get_text_alignment(element) or "LEFT"}}
                }
                if text_style_data:
                    paragraph_node["paragraphData"]["textStyle"].update(text_style_data)
                if node_style_data:
                    paragraph_node["style"] = node_style_data
                ricos_nodes.append(paragraph_node)

            inline_buffer = []

        for child in list(element.children):
            if hasattr(child, "name") and child.name == "br":
                flush_paragraph_buffer()
                ricos_nodes.append({"type": "LINE_BREAK", "nodes": [], "lineBreakData": {}})
            else:
                inline_buffer.append(child)

        flush_paragraph_buffer()

    # ------------------------------------------------------------
    # Headings h1..h6
    # ------------------------------------------------------------
    elif tag and re.match(r"h[1-6]$", tag):
        heading_content_nodes = _get_text_nodes_with_decorations(element)
        if heading_content_nodes:
            heading_node = {
                "type": "HEADING",
                "nodes": heading_content_nodes,
                "headingData": {"level": int(tag[1]), "textStyle": {"textAlignment": _get_text_alignment(element) or "LEFT"}}
            }
            if text_style_data:
                heading_node["headingData"]["textStyle"].update(text_style_data)
            if node_style_data:
                heading_node["style"] = node_style_data
            ricos_nodes.append(heading_node)

    # ------------------------------------------------------------
    # Bold / italic stand-alone treated as paragraph
    # ------------------------------------------------------------
    elif tag in ["b", "strong", "em", "i"]:
        content_nodes = _get_text_nodes_with_decorations(element)
        # garante decoração se não existir
        if tag in ["b", "strong"]:
            for node in content_nodes:
                node["textData"].setdefault("decorations", []).append({"type": "BOLD"})
        else:
            for node in content_nodes:
                node["textData"].setdefault("decorations", []).append({"type": "ITALIC"})
        if content_nodes:
            paragraph_node = {
                "type": "PARAGRAPH",
                "nodes": content_nodes,
                "paragraphData": {"textStyle": {"textAlignment": _get_text_alignment(element) or "LEFT"}}
            }
            if node_style_data:
                paragraph_node["style"] = node_style_data
            ricos_nodes.append(paragraph_node)

    # ------------------------------------------------------------
    # Imagem
    # ------------------------------------------------------------
    elif tag == "img":
        src = element.get("src")
        alt = element.get("alt", "")
        width = element.get("width")
        height = element.get("height")

        if src and image_importer:
            media_id = image_importer(src)
            if media_id:
                image_data = {
                    "containerData": {"width": {"size": "CONTENT"}, "alignment": "CENTER"},
                    "image": {"src": {"id": media_id}, "altText": alt}
                }
                if width:
                    try:
                        image_data["image"]["width"] = int(width)
                    except Exception:
                        pass
                if height:
                    try:
                        image_data["image"]["height"] = int(height)
                    except Exception:
                        pass
                ricos_nodes.append({"type": "IMAGE", "nodes": [], "imageData": image_data})
            else:
                logger.warning("Failed to import image from URL: %s", src)
        elif src:
            logger.warning("No image_importer supplied; image src present but not imported: %s", src)

    # ------------------------------------------------------------
    # Listas (ul / ol) — com suporte a aninhamento
    # ------------------------------------------------------------
    elif tag in ["ul", "ol"]:
        list_type = "BULLETED_LIST" if tag == "ul" else "ORDERED_LIST"
        list_items: List[Dict[str, Any]] = []
        for li in element.find_all("li", recursive=False):
            li_nodes: List[Dict[str, Any]] = []
            paragraph_content_nodes = _get_text_nodes_with_decorations(li)
            if paragraph_content_nodes:
                paragraph_node = {
                    "type": "PARAGRAPH",
                    "nodes": paragraph_content_nodes,
                    "paragraphData": {"textStyle": {"textAlignment": _get_text_alignment(li) or "LEFT"}}
                }
                if text_style_data:
                    paragraph_node["paragraphData"]["textStyle"].update(text_style_data)
                if node_style_data:
                    paragraph_node["style"] = node_style_data
                li_nodes.append(paragraph_node)

            # nested lists
            for nested_list in li.find_all(["ul", "ol"], recursive=False):
                li_nodes.extend(_convert_html_element_to_ricos_nodes(nested_list, image_importer, paragraph_spacing_px, list_depth + 1))

            if li_nodes:
                list_items.append({
                    "type": "LIST_ITEM",
                    "nodes": li_nodes,
                    "listItemData": {"depth": list_depth, "indentation": list_depth}
                })

        if list_items:
            ricos_nodes.append({"type": list_type, "nodes": list_items, "listData": {}})

    # ------------------------------------------------------------
    # Blockquote
    # ------------------------------------------------------------
    elif tag == "blockquote":
        blockquote_content_nodes: List[Dict[str, Any]] = []
        for child in element.children:
            if isinstance(child, NavigableString) and child.strip():
                blockquote_content_nodes.append({
                    "type": "PARAGRAPH",
                    "nodes": [{
                        "type": "TEXT",
                        "textData": {"text": str(child).strip(), "decorations": []}
                    }],
                    "paragraphData": {}
                })
            elif getattr(child, "name", None):
                if child.name == "p":
                    blockquote_content_nodes.extend(_convert_html_element_to_ricos_nodes(child, image_importer, paragraph_spacing_px, list_depth))
                else:
                    text_content = child.get_text(strip=True)
                    if text_content:
                        blockquote_content_nodes.append({
                            "type": "PARAGRAPH",
                            "nodes": [{
                                "type": "TEXT",
                                "textData": {"text": text_content, "decorations": []}
                            }],
                            "paragraphData": {}
                        })

        if blockquote_content_nodes:
            ricos_nodes.append({"type": "BLOCKQUOTE", "nodes": blockquote_content_nodes, "blockquoteData": {"indentation": 0}})

    # ------------------------------------------------------------
    # <br>
    # ------------------------------------------------------------
    elif tag == "br":
        ricos_nodes.append({"type": "LINE_BREAK", "nodes": [], "lineBreakData": {}})

    # ------------------------------------------------------------
    # Figure / figcaption (centralizado num único bloco)
    # ------------------------------------------------------------
    elif tag == "figure":
        figure_nodes: List[Dict[str, Any]] = []
        for child in element.children:
            if getattr(child, "name", None) == "img":
                figure_nodes.extend(_convert_html_element_to_ricos_nodes(child, image_importer, paragraph_spacing_px, list_depth))
            elif getattr(child, "name", None) == "figcaption":
                figcaption_nodes = _get_text_nodes_with_decorations(child)
                if figcaption_nodes:
                    figcaption_node = {
                        "type": "PARAGRAPH",
                        "nodes": figcaption_nodes,
                        "paragraphData": {"textStyle": {"textAlignment": "CENTER"}}
                    }
                    if node_style_data:
                        figcaption_node["style"] = node_style_data
                    figure_nodes.append(figcaption_node)
        ricos_nodes.extend(figure_nodes)

    elif tag == "figcaption":
        figcaption_content_nodes = _get_text_nodes_with_decorations(element)
        if figcaption_content_nodes:
            figcaption_node = {
                "type": "PARAGRAPH",
                "nodes": figcaption_content_nodes,
                "paragraphData": {"textStyle": {"textAlignment": "CENTER"}}
            }
            if node_style_data:
                figcaption_node["style"] = node_style_data
            ricos_nodes.append(figcaption_node)

    # ------------------------------------------------------------
    # Tabelas e qualquer outro elemento não mappeado → HTML node (fallback)
    # ------------------------------------------------------------
    elif tag in ["table", "tbody", "tr", "td", "caption"]:
        logger.info("HTML table element '%s' encountered — converting to HTML node.", tag)
        ricos_nodes.append({
            "type": "HTML",
            "id": generate_ricos_id(),
            "htmlData": {
                "html": str(element),
                "source": "HTML",
                "containerData": {"width": {"custom": "940px"}}
            }
        })

    else:
        # Fallback general para tags desconhecidas / block-level
        logger.info("Unhandled HTML tag '%s' — converting to HTML node.", tag)
        ricos_nodes.append({
            "type": "HTML",
            "id": generate_ricos_id(),
            "htmlData": {
                "html": str(element),
                "source": "HTML",
                "containerData": {"width": {"custom": "940px"}}
            }
        })

    return ricos_nodes


def convert_html_to_ricos(html: str,
                          *,
                          embed_strategy: str = "html_iframe",
                          image_importer: Optional[Callable[[str], Optional[str]]] = None,
                          paragraph_spacing_px: Optional[int] = None) -> Dict[str, Any]:
    """
    Converte uma string HTML para uma estrutura de nodos Ricos.

    Parâmetros
    ----------
    html:
        String contendo HTML a ser convertido.
    embed_strategy:
        Parâmetro de compatibilidade (atualmente não usado).
    image_importer:
        Callable(src: str) -> Optional[str]. Recebe URL/path da imagem e deve retornar
        um media_id (string) que será usado no nodo IMAGE. Se None, imagens não serão importadas.
    paragraph_spacing_px:
        Se fornecido, adiciona padding-bottom nos PARAGRAPH nodes (ex.: 12 para 12px).

    Retorno
    -------
    dict com chave "nodes" contendo a lista de nodos Ricos.
    """
    logger.debug("convert_html_to_ricos called: html length=%s", len(html) if html else 0)

    if not html or not html.strip():
        logger.debug("Empty HTML input — returning empty nodes")
        return {"nodes": []}

    # Converte shortcodes [caption]...[/caption] para <figure><figcaption>...
    def caption_shortcode_to_figure(match):
        img_tag = match.group(2)
        caption_text = match.group(3).strip()
        if caption_text:
            return f'<figure class="wp-caption">{img_tag}<figcaption class="wp-caption-text">{caption_text}</figcaption></figure>'
        else:
            return img_tag

    caption_pattern = re.compile(r'\[caption(.*?)\]\s*(<img .*?>)\s*(.*?)\s*\[/caption\]', re.DOTALL)
    html = caption_pattern.sub(caption_shortcode_to_figure, html)

    soup = BeautifulSoup(html, "html.parser")
    ricos_output_nodes: List[Dict[str, Any]] = []

    # BLOCK_TAGS: somente tags que realmente quebram agrupamento inline
    BLOCK_TAGS = {
        "p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "blockquote",
        "img", "br", "table", "div", "hr", "pre", "figure", "figcaption", "table", "tbody", "tr", "td", "caption"
    }

    inline_buffer: List[Any] = []

    def flush_inline_buffer():
        nonlocal inline_buffer
        if not inline_buffer:
            return

        temp_p = soup.new_tag("p")
        for item in inline_buffer:
            try:
                temp_p.append(item.extract())
            except Exception:
                temp_p.append(item)

        paragraph_content_nodes = _get_text_nodes_with_decorations(temp_p)
        if paragraph_content_nodes:
            paragraph_node = {
                "type": "PARAGRAPH",
                "nodes": paragraph_content_nodes,
                "paragraphData": {"textStyle": {"textAlignment": "LEFT"}}
            }
            if paragraph_spacing_px is not None:
                paragraph_node["style"] = {"paddingBottom": f"{paragraph_spacing_px}px"}
            ricos_output_nodes.append(paragraph_node)

        inline_buffer = []

    # processa filhos diretos do body (ou soup caso não exista body)
    children = list(soup.body.children) if soup.body else list(soup.children)

    for child in children:
        is_inline = isinstance(child, NavigableString) or (getattr(child, "name", None) and child.name not in BLOCK_TAGS)

        if is_inline:
            inline_buffer.append(child)
        else:
            flush_inline_buffer()
            if getattr(child, "name", None):
                ricos_output_nodes.extend(_convert_html_element_to_ricos_nodes(child, image_importer, paragraph_spacing_px, list_depth=0))
            else:
                # se for apenas uma string (mas não inline?), trata como texto simples
                if isinstance(child, NavigableString) and child.strip():
                    tmp = soup.new_tag("p")
                    tmp.append(child.extract())
                    ricos_output_nodes.extend(_convert_html_element_to_ricos_nodes(tmp, image_importer, paragraph_spacing_px, list_depth=0))

    # flush final
    flush_inline_buffer()

    logger.debug("Generated Ricos nodes count: %d", len(ricos_output_nodes))
    return {"nodes": ricos_output_nodes}
