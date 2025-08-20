import re
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup, NavigableString

__all__ = [
    "convert_html_to_ricos",
]

def generate_ricos_id() -> str:
    """
    Generates a valid Ricos node ID.
    """
    return str(uuid.uuid4()).replace("-", "")[:12] # Ricos IDs are typically shorter

def _get_text_alignment(element: Any) -> Optional[str]:
    """
    Extracts text alignment from an HTML element's style or align attribute.
    Returns "CENTER", "JUSTIFY", "LEFT", "RIGHT", or None.
    """
    # Check inline style
    style = element.get("style")
    if style:
        match = re.search(r"text-align:\s*(center|justify|left|right);?", style)
        if match:
            align = match.group(1).upper()
            if align in ["CENTER", "JUSTIFY", "LEFT", "RIGHT"]:
                return align

    # Check align attribute (deprecated)
    align_attr = element.get("align")
    if align_attr:
        align_attr = align_attr.upper()
        if align_attr in ["CENTER", "JUSTIFY", "LEFT", "RIGHT"]:
            return align_attr

    return None

def _get_inline_styles(element: Any) -> Dict[str, str]:
    """
    Extracts inline CSS styles from an HTML element.
    """
    style_attr = element.get("style")
    styles = {}
    if style_attr:
        for style_pair in style_attr.split(";"):
            if ":" in style_pair:
                prop, value = style_pair.split(":", 1)
                styles[prop.strip()] = value.strip()
    return styles

def _get_text_nodes_with_decorations(element: Any) -> List[Dict[str, Any]]:
    """
    Extracts text content from a BeautifulSoup element and applies Ricos decorations
    based on inline HTML tags (strong, em, a, span).
    """
    text_nodes = []
    inline_styles = _get_inline_styles(element)

    for child in element.contents:
        if isinstance(child, NavigableString):
            if str(child).strip():
                text_node = {
                    "type": "TEXT",
                    "textData": {
                        "text": str(child),
                        "decorations": []
                    }
                }
                # Apply inline style decorations
                if "text-decoration" in inline_styles and "underline" in inline_styles["text-decoration"]:
                    text_node["textData"]["decorations"].append({"type": "UNDERLINE"})
                if "color" in inline_styles:
                    text_node["textData"]["decorations"].append({"type": "COLOR", "colorData": {"foreground": inline_styles["color"]}})
                if "background-color" in inline_styles:
                    text_node["textData"]["decorations"].append({"type": "COLOR", "colorData": {"background": inline_styles["background-color"]}})
                if "font-size" in inline_styles:
                    # Ricos expects font size in px, so ensure it's in px
                    font_size_val = inline_styles["font-size"].replace("px", "")
                    try:
                        text_node["textData"]["decorations"].append({"type": "FONT_SIZE", "fontSizeData": {"value": float(font_size_val), "unit": "PX"}})
                    except ValueError:
                        pass # Ignore if not a valid float
                text_nodes.append(text_node)
        elif child.name in ["strong", "b"]:
            # Apply BOLD decoration to all text nodes within this strong/b tag
            for text_node in _get_text_nodes_with_decorations(child):
                text_node["textData"]["decorations"].append({"type": "BOLD"})
                text_nodes.append(text_node)
        elif child.name in ["em", "i"]:
            # Apply ITALIC decoration
            for text_node in _get_text_nodes_with_decorations(child):
                text_node["textData"]["decorations"].append({"type": "ITALIC"})
                text_nodes.append(text_node)
        elif child.name == "u":
            # Apply UNDERLINE decoration
            for text_node in _get_text_nodes_with_decorations(child):
                text_node["textData"]["decorations"].append({"type": "UNDERLINE"})
                text_nodes.append(text_node)
        elif child.name == "a":
            # Apply LINK decoration
            href = child.get("href")
            if href:
                for text_node in _get_text_nodes_with_decorations(child):
                    text_node["textData"]["decorations"].append({
                        "type": "LINK",
                        "linkData": {"url": href}
                    })
                    text_nodes.append(text_node)
            else: # If <a> tag has no href, just process its children
                text_nodes.extend(_get_text_nodes_with_decorations(child))
        elif child.name == "span":
            # For span, just process its children, ignoring its own styling
            text_nodes.extend(_get_text_nodes_with_decorations(child))
        elif child.name == "br":
            # This case should be handled by the calling function, which splits nodes.
            # We pass it up by not converting it to a space.
            pass
        else:
            # For any other unexpected tag within what should be inline content,
            # try to extract its text content and add it as a plain text node.
            if child.get_text(strip=True):
                text_nodes.append({
                    "type": "TEXT",
                    "textData": {
                        "text": child.get_text(),
                        "decorations": []
                    }
                })
    return text_nodes

def _convert_html_element_to_ricos_nodes(element: Any, image_importer: Optional[Callable[[str], Optional[str]]] = None, paragraph_spacing_px: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Converts a single BeautifulSoup HTML element (expected to be a block-level element)
    into a list of Ricos nodes.
    """
    ricos_nodes = []
    soup = BeautifulSoup("", "html.parser") # Used to create temporary tags

    if isinstance(element, NavigableString):
        # NavigableString should be handled by the caller (convert_html_to_ricos)
        return ricos_nodes

    inline_styles = _get_inline_styles(element)
    text_style_data = {}
    if "line-height" in inline_styles:
        text_style_data["lineHeight"] = inline_styles["line-height"]
    
    node_style_data = {}
    if paragraph_spacing_px is not None:
        node_style_data["paddingBottom"] = f"{paragraph_spacing_px}px"
    if "padding-top" in inline_styles:
        node_style_data["paddingTop"] = inline_styles["padding-top"]
    
    if element.name == "p":
        inline_buffer = []

        def flush_paragraph_buffer():
            nonlocal inline_buffer
            if not inline_buffer:
                return

            temp_p = soup.new_tag("p")
            for item in inline_buffer:
                temp_p.append(item.extract())

            paragraph_content_nodes = _get_text_nodes_with_decorations(temp_p)
            if paragraph_content_nodes:
                paragraph_node = {
                    "type": "PARAGRAPH",
                    "nodes": paragraph_content_nodes,
                    "paragraphData": {}
                }
                alignment = _get_text_alignment(element)
                paragraph_node["paragraphData"]["textStyle"] = {"textAlignment": alignment if alignment else "JUSTIFY"}
                if text_style_data:
                    paragraph_node["paragraphData"]["textStyle"].update(text_style_data)
                if node_style_data:
                    paragraph_node["style"] = node_style_data
                ricos_nodes.append(paragraph_node)
            
            inline_buffer = []

        for child in list(element.children):
            if hasattr(child, 'name') and child.name == 'br':
                flush_paragraph_buffer()
                ricos_nodes.append({"type": "LINE_BREAK", "nodes": [], "lineBreakData": {}})
            else:
                inline_buffer.append(child)
        
        flush_paragraph_buffer()

    elif element.name and re.match(r"h[1-6]", element.name):
        heading_level_map = {
            "h1": "HEADING_ONE", "h2": "HEADING_TWO", "h3": "HEADING_THREE",
            "h4": "HEADING_FOUR", "h5": "HEADING_FIVE", "h6": "HEADING_SIX"
        }
        heading_type = heading_level_map.get(element.name, "HEADING_ONE")
        heading_content_nodes = _get_text_nodes_with_decorations(element)
        if heading_content_nodes:
            heading_node = {
                "type": "HEADING",
                "nodes": heading_content_nodes,
                "headingData": {"level": int(element.name[1])}
            }
            alignment = _get_text_alignment(element)
            heading_node["headingData"]["textStyle"] = {"textAlignment": alignment if alignment else "JUSTIFY"}
            if text_style_data:
                heading_node["headingData"]["textStyle"].update(text_style_data)
            if node_style_data:
                heading_node["style"] = node_style_data
            ricos_nodes.append(heading_node)
    elif element.name in ["b", "strong"]:
        content_nodes = _get_text_nodes_with_decorations(element)
        for node in content_nodes:
            is_bold = any(d.get("type") == "BOLD" for d in node.get("textData", {}).get("decorations", []))
            if not is_bold:
                node.get("textData", {}).setdefault("decorations", []).append({"type": "BOLD"})
        if content_nodes:
            paragraph_node = {
                "type": "PARAGRAPH",
                "nodes": content_nodes,
                "paragraphData": {"textStyle": {"textAlignment": "JUSTIFY"}}
            }
            ricos_nodes.append(paragraph_node)
    elif element.name in ["em", "i"]:
        content_nodes = _get_text_nodes_with_decorations(element)
        for node in content_nodes:
            is_italic = any(d.get("type") == "ITALIC" for d in node.get("textData", {}).get("decorations", []))
            if not is_italic:
                node.get("textData", {}).setdefault("decorations", []).append({"type": "ITALIC"})
        if content_nodes:
            paragraph_node = {
                "type": "PARAGRAPH",
                "nodes": content_nodes,
                "paragraphData": {"textStyle": {"textAlignment": "JUSTIFY"}}
            }
            ricos_nodes.append(paragraph_node)
    elif element.name == "img":
        src = element.get("src")
        alt = element.get("alt", "")
        width = element.get("width")
        height = element.get("height")

        if src and image_importer:
            media_id = image_importer(src)
            if media_id:
                image_data = {
                    "containerData": {
                        "width": {"size": "CONTENT"},
                        "alignment": "CENTER"
                    },
                    "image": {
                        "src": {"id": media_id},
                        "altText": alt
                    }
                }
                if width:
                    try:
                        image_data["image"]["width"] = int(width)
                    except ValueError:
                        pass
                if height:
                    try:
                        image_data["image"]["height"] = int(height)
                    except ValueError:
                        pass
                
                ricos_nodes.append({
                    "type": "IMAGE",
                    "nodes": [],
                    "imageData": image_data
                })
            else:
                print(f"WARNING: Failed to import image from URL: {src}")
        elif src:
            print(f"WARNING: Image importer not provided or image source missing for: {src}")
    elif element.name in ["ul", "ol"]:
        list_type = "BULLETED_LIST" if element.name == "ul" else "ORDERED_LIST"
        list_items = []
        for li in element.find_all("li", recursive=False):
            li_nodes = []
            # Each LIST_ITEM must contain a PARAGRAPH node
            paragraph_content_nodes = _get_text_nodes_with_decorations(li)
            if paragraph_content_nodes:
                paragraph_node = {
                    "type": "PARAGRAPH",
                    "nodes": paragraph_content_nodes,
                    "paragraphData": {}
                }
                alignment = _get_text_alignment(li)
                paragraph_node["paragraphData"]["textStyle"] = {"textAlignment": alignment if alignment else "JUSTIFY"}
                if text_style_data:
                    paragraph_node["paragraphData"]["textStyle"].update(text_style_data)
                if node_style_data:
                    paragraph_node["style"] = node_style_data
                li_nodes.append(paragraph_node)
            
            # Handle nested lists within <li>
            for nested_list in li.find_all(["ul", "ol"], recursive=False):
                li_nodes.extend(_convert_html_element_to_ricos_nodes(nested_list, image_importer, paragraph_spacing_px))

            if li_nodes:
                list_items.append({
                    "type": "LIST_ITEM",
                    "nodes": li_nodes,
                    "listItemData": {"depth": 0, "indentation": 0} # Depth and indentation might need more complex logic for nested lists
                })
        if list_items:
            ricos_nodes.append({
                "type": list_type,
                "nodes": list_items,
                "listData": {}
            })
    elif element.name == "blockquote":
        blockquote_content_nodes = []
        # Blockquote must contain PARAGRAPH nodes
        for child in element.children:
            if isinstance(child, NavigableString) and child.strip():
                blockquote_content_nodes.append({
                    "type": "PARAGRAPH",
                    "nodes": [{
                        "type": "TEXT",
                        "textData": {
                            "text": str(child).strip(),
                            "decorations": []
                        }
                    }],
                    "paragraphData": {}
                })
            elif child.name:
                # If it's a <p> inside a blockquote, process it as a paragraph.
                if child.name == "p":
                    blockquote_content_nodes.extend(_convert_html_element_to_ricos_nodes(child, image_importer, paragraph_spacing_px))
                else: # For other tags, just get their text content
                    text_content = child.get_text(strip=True)
                    if text_content:
                        blockquote_content_nodes.append({
                            "type": "PARAGRAPH",
                            "nodes": [{
                                "type": "TEXT",
                                "textData": {
                                    "text": text_content,
                                    "decorations": []
                                }
                            }],
                            "paragraphData": {}
                        })
        
        if blockquote_content_nodes:
            ricos_nodes.append({
                "type": "BLOCKQUOTE",
                "nodes": blockquote_content_nodes,
                "blockquoteData": {"indentation": 0}
            })
    elif element.name == "br":
        # <br> tags at the top level or directly under a block should be LINE_BREAK nodes
        ricos_nodes.append({
            "type": "LINE_BREAK",
            "nodes": [],
            "lineBreakData": {}
        })
    elif element.name == "figure":
        # Handle <figure> tag: process its children (img and figcaption)
        figure_nodes = []
        for child in element.children:
            if child.name == "img":
                figure_nodes.extend(_convert_html_element_to_ricos_nodes(child, image_importer, paragraph_spacing_px))
            elif child.name == "figcaption":
                # figcaption should be a paragraph
                figcaption_content_nodes = _get_text_nodes_with_decorations(child)
                if figcaption_content_nodes:
                    figcaption_node = {
                        "type": "PARAGRAPH",
                        "nodes": figcaption_content_nodes,
                        "paragraphData": {"textStyle": {"textAlignment": "CENTER"}} # Captions are often centered
                    }
                    if node_style_data:
                        figcaption_node["style"] = node_style_data
                    figure_nodes.append(figcaption_node)
        ricos_nodes.extend(figure_nodes)
    elif element.name == "figcaption":
        # figcaption should be a paragraph (handled when inside figure, but also if standalone)
        figcaption_content_nodes = _get_text_nodes_with_decorations(element)
        if figcaption_content_nodes:
            figcaption_node = {
                "type": "PARAGRAPH",
                "nodes": figcaption_content_nodes,
                "paragraphData": {"textStyle": {"textAlignment": "CENTER"}} # Captions are often centered
            }
            if node_style_data:
                figcaption_node["style"] = node_style_data
            ricos_nodes.append(figcaption_node)
    elif element.name == "figure":
        # Handle <figure> tag: process its children (img and figcaption)
        figure_nodes = []
        for child in element.children:
            if child.name == "img":
                figure_nodes.extend(_convert_html_element_to_ricos_nodes(child, image_importer, paragraph_spacing_px))
            elif child.name == "figcaption":
                # figcaption should be a paragraph
                figcaption_content_nodes = _get_text_nodes_with_decorations(child)
                if figcaption_content_nodes:
                    figcaption_node = {
                        "type": "PARAGRAPH",
                        "nodes": figcaption_content_nodes,
                        "paragraphData": {"textStyle": {"textAlignment": "CENTER"}} # Captions are often centered
                    }
                    if node_style_data:
                        figcaption_node["style"] = node_style_data
                    figure_nodes.append(figcaption_node)
        ricos_nodes.extend(figure_nodes)
    elif element.name == "figcaption":
        # figcaption should be a paragraph (handled when inside figure, but also if standalone)
        figcaption_content_nodes = _get_text_nodes_with_decorations(element)
        if figcaption_content_nodes:
            figcaption_node = {
                "type": "PARAGRAPH",
                "nodes": figcaption_content_nodes,
                "paragraphData": {"textStyle": {"textAlignment": "CENTER"}} # Captions are often centered
            }
            if node_style_data:
                figcaption_node["style"] = node_style_data
            ricos_nodes.append(figcaption_node)
    elif element.name in ["table", "tbody", "tr", "td", "caption"]:
        # Tables are not directly supported in Ricos. Convert to HTML node.
        print(f"INFO: HTML table element '{element.name}'. Converting to HTML node.")
        ricos_nodes.append({
            "type": "HTML",
            "id": generate_ricos_id(),
            "htmlData": {
                "html": str(element),
                "source": "HTML",
                "containerData": {
                    "width": {"custom": "940px"}
                }
            }
        })
    else:
        # For any other unhandled block-level tags, convert to HTML node.
        print(f"INFO: Unhandled HTML tag '{element.name}'. Converting to HTML node.")
        ricos_nodes.append({
            "type": "HTML",
            "id": generate_ricos_id(),
            "htmlData": {
                "html": str(element),
                "source": "HTML",
                "containerData": {
                    "width": {"custom": "940px"}
                }
            }
        })
    return ricos_nodes

def convert_html_to_ricos(html: str, *, embed_strategy: str = "html_iframe", image_importer: Optional[Callable[[str], Optional[str]]] = None, paragraph_spacing_px: Optional[int] = None) -> Dict[str, Any]:
    """
    Converts HTML to Wix Ricos format by parsing HTML elements into native Ricos nodes.
    This version aims to convert HTML tags like p, h1-h6, img, ul, ol, li, blockquote,
    and apply inline text decorations for strong, em, and a.
    It also groups consecutive inline elements into single paragraphs and handles <br> tags.
    """
    print(f"DEBUG: convert_html_to_ricos called with HTML (length {len(html) if html else 0}): {html[:200] if html else ''}...")

    if not html or not html.strip():
        print("DEBUG: HTML is empty, returning empty nodes")
        return {"nodes": []}

    # Pre-process [caption] shortcodes into <figure> and <figcaption>
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
    ricos_output_nodes = []
    
    # Define block-level tags that should break inline grouping
    BLOCK_TAGS = ["p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "blockquote", "img", "br", "table", "div", "hr", "pre", "b", "strong", "i", "em", "figure", "figcaption"]

    inline_buffer = []

    def flush_inline_buffer():
        nonlocal inline_buffer
        if not inline_buffer:
            return

        # Create a temporary paragraph to hold the inline elements
        temp_p = soup.new_tag("p")
        for item in inline_buffer:
            temp_p.append(item.extract()) # Use extract to move the item

        paragraph_content_nodes = _get_text_nodes_with_decorations(temp_p)
        if paragraph_content_nodes:
            paragraph_node = {
                "type": "PARAGRAPH",
                "nodes": paragraph_content_nodes,
                "paragraphData": {"textStyle": {"textAlignment": "JUSTIFY"}}
            }
            if paragraph_spacing_px is not None:
                paragraph_node["style"] = {"paddingBottom": f"{paragraph_spacing_px}px"}
            ricos_output_nodes.append(paragraph_node)
        
        inline_buffer = []

    # Process direct children of the body or the soup itself if no body tag
    children = list(soup.body.children) if soup.body else list(soup.children)
    
    for child in children:
        is_inline = isinstance(child, NavigableString) or (hasattr(child, 'name') and child.name not in BLOCK_TAGS)

        if is_inline:
            inline_buffer.append(child)
        else:
            flush_inline_buffer()
            # Process the block-level element
            if hasattr(child, 'name') and child.name:
                 ricos_output_nodes.extend(_convert_html_element_to_ricos_nodes(child, image_importer, paragraph_spacing_px))

    # Flush any remaining inline elements at the end
    flush_inline_buffer()

    print(f"DEBUG: Generated Ricos content (first 500 chars): {str(ricos_output_nodes)[:500]}...")
    return {"nodes": ricos_output_nodes}