from __future__ import annotations

from typing import Any, Dict, List, Optional

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
)


InlineDeco = Dict[str, Any]


def convert_html_to_ricos_local(html: str) -> Dict[str, Any]:
    """
    Convert HTML to a basic Ricos document without using Wix APIs.

    Covered:
    - Headings, paragraphs, links, inline emphasis, lists, blockquote,
      divider (hr), code (inline and block), image placeholders.
    - Tables and figures are simplified to text paragraphs in this v1.
    """
    soup = BeautifulSoup(html or "", "html.parser")

    # Remove scripts/styles
    for bad in soup.find_all(["script", "style"]):
        bad.decompose()

    # Normalize &nbsp; by replacing with regular spaces
    def normalize_ws(text: str) -> str:
        return (text or "").replace("\xa0", " ")

    nodes: List[Dict[str, Any]] = []

    def build_inline(node: Tag, active: List[InlineDeco]) -> List[Dict[str, Any]]:
        parts: List[Dict[str, Any]] = []

        def flush_text(s: str):
            s = normalize_ws(s)
            if s.strip():
                parts.append(text_node(s, active.copy() if active else None))

        for child in node.children:
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
                alt = child.get("alt") or "imagem"
                src = child.get("src") or ""
                flush_text(f"[Imagem: {alt}] {src}".strip())
                continue

            # Recurse for inline children
            parts.extend(build_inline(child, new_active))
        return parts

    def handle_block(el: Tag):
        name = (el.name or "").lower()
        if name in {"p", "span", "div", "section"}:
            # Treat as paragraph-ish: collapse into a paragraph
            inlines = build_inline(el, [])
            if inlines:
                nodes.append(paragraph(inlines))
            return
        if name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            lvl = int(name[1])
            inlines = build_inline(el, [])
            nodes.append(heading(lvl, inlines))
            return
        if name in {"ul", "ol"}:
            ordered = name == "ol"
            items: List[Dict[str, Any]] = []
            for li in el.find_all("li", recursive=False):
                # Each li becomes LIST_ITEM with a paragraph from its text
                inlines = build_inline(li, [])
                if inlines:
                    items.append(list_item([paragraph(inlines)]))
            if items:
                nodes.append(list_container(ordered, items))
            return
        if name == "blockquote":
            inlines = build_inline(el, [])
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
            # Simplify to plain paragraph text for v1
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

    # Traverse top-level blocks
    container = soup.body if soup.body else soup
    for child in container.children:
        if isinstance(child, NavigableString):
            t = str(child).strip()
            if t:
                nodes.append(paragraph([text_node(normalize_ws(t))]))
        elif isinstance(child, Tag):
            handle_block(child)

    return validate_ricos(doc(nodes))

