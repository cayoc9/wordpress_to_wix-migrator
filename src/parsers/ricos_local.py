from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
import re

from bs4 import BeautifulSoup, NavigableString, Tag

from .ricos_schema import (
    doc,
    paragraph,
    heading,
    blockquote,
    divider,
    code_block,
    list_container,
    list_item,
    text_node,
    deco,
    validate_ricos,
    image_node_wix_media,
    html_block,
    table_node_simple,
)


InlineDeco = Dict[str, Any]


def convert_html_to_ricos_local(
    html: str,
    *,
    image_importer: Optional[Callable[[str], Optional[str]]] = None,
    table_mode: str = "html",
) -> Dict[str, Any]:
    """
    Convert HTML to a basic Ricos document without using Wix APIs.

    Covered:
    - Headings, paragraphs, links, inline emphasis, lists, blockquote,
      divider (hr), code (inline and block), image placeholders.
    - Tables and figures are simplified to text paragraphs in this v1.
    """
    # Pre-process to remove WordPress shortcodes like [caption]
    cleaned_html = re.sub(r'\[/?caption[^\]]*\]', '', html or "", flags=re.IGNORECASE)
    
    soup = BeautifulSoup(cleaned_html, "html.parser")

    # Remove scripts/styles
    for bad in soup.find_all(["script", "style"]):
        bad.decompose()

    # Normalize &nbsp; by replacing with regular spaces
    def normalize_ws(text: str) -> str:
        return (text or "").replace("\xa0", " ")

    nodes: List[Dict[str, Any]] = []

    def build_inline_from_nodes(children_iter, active: List[InlineDeco], deferred_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        parts: List[Dict[str, Any]] = []

        def flush_text(s: str):
            s = normalize_ws(s)
            if s.strip():
                parts.append(text_node(s, active.copy() if active else None))

        for child in children_iter:
            if isinstance(child, NavigableString):
                flush_text(str(child))
                continue
            if not isinstance(child, Tag):
                continue
            name = (child.name or "").lower()

            # Handle line breaks inside paragraphs
            if name == "br":
                parts.append(text_node("\n", active.copy() if active else None))
                continue

            # Decorations
            new_active = active.copy()
            if name in ("strong", "b"):
                new_active.append(deco("BOLD"))
            elif name in ("em", "i"):
                new_active.append(deco("ITALIC"))
            elif name == "u":
                new_active.append(deco("UNDERLINE"))
            elif name in ("s", "strike", "del"):
                new_active.append(deco("STRIKETHROUGH"))
            elif name == "code":
                new_active.append(deco("CODE"))
            elif name == "a":
                href = child.get("href")
                if href:
                    new_active.append(deco("LINK", {"url": href}))

            # Replace images as text placeholders
            if name == "img":
                alt_attr = child.get("alt")
                alt = alt_attr[0] if isinstance(alt_attr, list) else alt_attr or "imagem"
                src_attr = child.get("src")
                src = src_attr[0] if isinstance(src_attr, list) else src_attr or ""
                if image_importer and src:
                    try:
                        media_id = image_importer(src)
                    except Exception:
                        media_id = None
                    if media_id:
                        deferred_blocks.append(image_node_wix_media(media_id, caption=alt or None))
                        continue
                # Fallback: textual placeholder
                flush_text(f"[Imagem: {alt}] {src}".strip())
                continue

            # Recurse for inline children
            # Recurse for inline children
            parts.extend(build_inline_from_nodes(child.children, new_active, deferred_blocks))
        return parts

    def build_inline(node: Tag, active: List[InlineDeco], deferred_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return build_inline_from_nodes(node.children, active, deferred_blocks)

    def handle_block(el: Tag):
        name = (el.name or "").lower()
        if name in {"p", "span", "div", "section"}:
            # Treat as paragraph-ish: collapse into a paragraph
            deferred_blocks: List[Dict[str, Any]] = []
            inlines = build_inline(el, [], deferred_blocks)
            if inlines:
                nodes.append(paragraph(inlines))
            if deferred_blocks:
                nodes.extend(deferred_blocks)
            return
        if name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            lvl = int(name[1])
            inlines = build_inline(el, [], [])
            nodes.append(heading(lvl, inlines))
            return
        if name in {"ul", "ol"}:
            ordered = name == "ol"
            items: List[Dict[str, Any]] = []
            for li in el.find_all("li", recursive=False):
                # Each li becomes LIST_ITEM with a paragraph from its text
                inlines = build_inline(li, [], [])
                if inlines:
                    items.append(list_item([paragraph(inlines)]))
            if items:
                nodes.append(list_container(ordered, items))
            return
        if name == "blockquote":
            inlines = build_inline(el, [], [])
            if inlines:
                nodes.append(blockquote([paragraph(inlines)]))
            return
        if name == "hr":
            nodes.append(divider())
            return
        if name == "pre":
            # preformatted text, try to extract code text
            code_child = el.find("code")
            text = code_child.get_text("\n") if code_child else el.get_text("\n")
            nodes.append(code_block(normalize_ws(text)))
            return
        if name in {"table", "thead", "tbody", "tr", "td", "th", "figure", "figcaption"}:
            # Tables/figures handling
            # Try to extract image inside figure
            img = el.find("img")
            if isinstance(img, Tag) and image_importer:
                src_attr = img.get("src")
                src = src_attr[0] if isinstance(src_attr, list) else src_attr or ""
                alt_attr = img.get("alt")
                alt = alt_attr if isinstance(alt_attr, str) else None

                if src:
                    try:
                        media_id = image_importer(src)
                    except Exception:
                        media_id = None
                    if media_id:
                        nodes.append(image_node_wix_media(media_id, caption=alt))
                        return
            # Table modes: html (default), plugin, paragraphs
            if name == "table":
                if table_mode == "html":
                    nodes.append(html_block(str(el)))
                    return
                elif table_mode == "plugin":
                    # Build rows from text of cells
                    rows: List[List[str]] = []
                    for tr in el.find_all("tr", recursive=False):
                        cells: List[str] = []
                        for cell in tr.find_all(["td", "th"], recursive=False):
                            cells.append(cell.get_text(" ", strip=True))
                        if cells:
                            rows.append(cells)
                    if rows:
                        # crude header rows detection: if any th in first row
                        first_row = el.find("tr")
                        header_rows = 1 if first_row and first_row.find("th") else 0
                        nodes.append(table_node_simple(rows, header_rows=header_rows))
                        return
                # paragraphs fallback
                txt = el.get_text(" ", strip=True)
                if txt:
                    nodes.append(paragraph([text_node(txt)]))
                return
            # Not a root table; fallback text
            txt = el.get_text(" ", strip=True)
            if txt:
                nodes.append(paragraph([text_node(txt)]))
            return
        if name == "iframe":
            src = el.get("src") or ""
            if src:
                nodes.append(paragraph([text_node(f"[Embed] {src}")]))
            return

        # Fallback: treat unknown blocks as paragraph text
        txt = el.get_text(" ", strip=True)
        if txt:
            nodes.append(paragraph([text_node(txt)]))

    # Traverse top-level: coalesce inline siblings into a single paragraph
    def is_inline_tag(t: Optional[str]) -> bool:
        if not t:
            return False
        t = t.lower()
        return t in {"span", "a", "strong", "b", "em", "i", "u", "s", "strike", "del", "code", "img", "br"}

    container = soup.body if soup.body else soup
    inline_run: List[Any] = []

    def flush_inline_run():
        nonlocal inline_run
        if not inline_run:
            return
        deferred_blocks: List[Dict[str, Any]] = []
        inlines = build_inline_from_nodes(inline_run, [], deferred_blocks)
        if inlines:
            nodes.append(paragraph(inlines))
        if deferred_blocks:
            nodes.extend(deferred_blocks)
        inline_run = []

    for child in container.children:
        if isinstance(child, NavigableString):
            if str(child).strip():
                inline_run.append(child)
            else:
                # whitespace boundary ends run
                flush_inline_run()
            continue
        if isinstance(child, Tag) and is_inline_tag(child.name):
            inline_run.append(child)
            continue
        # Block-level element encountered
        flush_inline_run()
        if isinstance(child, Tag):
            handle_block(child)

    # flush any trailing inline run
    flush_inline_run()

    return validate_ricos(doc(nodes))
