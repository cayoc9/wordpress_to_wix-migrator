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


    """
    Extracts text content from a BeautifulSoup element and applies Ricos decorations
    based on inline HTML tags (strong, em, a, span).
    """
    text_nodes = []
    for child in element.contents:
        if isinstance(child, NavigableString):
            if str(child).strip():
                text_nodes.append({
                    "type": "TEXT",
                    "textData": {
                        "text": str(child),
                        "decorations": []
                    }
                })
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
            # Line breaks within text content are represented as a space for now.
            # A more advanced solution might split text nodes and insert LINE_BREAK nodes.
            text_nodes.append({
                "type": "TEXT",
                "textData": {
                    "text": " ",
                    "decorations": []
                }
            })
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

    if isinstance(element, NavigableString):
        # NavigableString should be handled by the caller (convert_html_to_ricos or _get_text_nodes_with_decorations)
        return ricos_nodes

    if element.name in ["p", "span", "b", "a"]:
        paragraph_content_nodes = _get_text_nodes_with_decorations(element)
        if paragraph_content_nodes:
            paragraph_node = {
                "type": "PARAGRAPH",
                "nodes": paragraph_content_nodes,
                "paragraphData": {}
            }
            alignment = _get_text_alignment(element)
            paragraph_node["paragraphData"]["textStyle"] = {"textAlignment": alignment if alignment else "JUSTIFY"}
            if paragraph_spacing_px is not None:
                paragraph_node["style"] = {"paddingBottom": f"{paragraph_spacing_px}px"}
            ricos_nodes.append(paragraph_node)
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
            if paragraph_spacing_px is not None:
                heading_node["style"] = {"paddingBottom": f"{paragraph_spacing_px}px"}
            ricos_nodes.append(heading_node)
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
                if paragraph_spacing_px is not None:
                    paragraph_node["style"] = {"paddingBottom": f"{paragraph_spacing_px}px"}
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
    elif element.name in ["em", "i"]:
        # Treat <em> and <i> as inline elements, wrapping their content in a paragraph.
        paragraph_content_nodes = _get_text_nodes_with_decorations(element)
        if paragraph_content_nodes:
            paragraph_node = {
                "type": "PARAGRAPH",
                "nodes": paragraph_content_nodes,
                "paragraphData": {}
            }
            alignment = _get_text_alignment(element)
            paragraph_node["paragraphData"]["textStyle"] = {"textAlignment": alignment if alignment else "JUSTIFY"}
            if paragraph_spacing_px is not None:
                paragraph_node["style"] = {"paddingBottom": f"{paragraph_spacing_px}px"}
            ricos_nodes.append(paragraph_node)
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

def _get_text_nodes_with_decorations(element: Any) -> List[Dict[str, Any]]:
    """
    Extracts text content from a BeautifulSoup element and applies Ricos decorations
    based on inline HTML tags (strong, em, a, span).
    """
    text_nodes = []
    for child in element.contents:
        if isinstance(child, NavigableString):
            if str(child).strip():
                text_nodes.append({
                    "type": "TEXT",
                    "textData": {
                        "text": str(child),
                        "decorations": []
                    }
                })
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
            # Line breaks within text content are represented as a space for now.
            # A more advanced solution might split text nodes and insert LINE_BREAK nodes.
            text_nodes.append({
                "type": "TEXT",
                "textData": {
                    "text": " ",
                    "decorations": []
                }
            })
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

def convert_html_to_ricos(html: str, *, embed_strategy: str = "html_iframe", image_importer: Optional[Callable[[str], Optional[str]]] = None, paragraph_spacing_px: Optional[int] = None) -> Dict[str, Any]:
    """
    Converts HTML to Wix Ricos format by parsing HTML elements into native Ricos nodes.
    This version aims to convert HTML tags like p, h1-h6, img, ul, ol, li, blockquote,
    and apply inline text decorations for strong, em, and a.
    """
    print(f"DEBUG: convert_html_to_ricos called with HTML (length {len(html) if html else 0}): {html[:200] if html else ''}...")

    if not html or not html.strip():
        print("DEBUG: HTML is empty, returning empty nodes")
        return {"nodes": []}

    soup = BeautifulSoup(html, "html.parser")
    ricos_output_nodes = []

    # Process direct children of the body or the soup itself if no body tag
    # This loop should only call _convert_html_element_to_ricos_nodes for block-level elements
    # or wrap NavigableStrings in paragraphs.
    for child in soup.body.children if soup.body else soup.children:
        if isinstance(child, NavigableString):
            text = str(child).strip()
            if text:
                ricos_output_nodes.append({
                    "type": "PARAGRAPH",
                    "nodes": [{
                        "type": "TEXT",
                        "textData": {
                            "text": text,
                            "decorations": []
                        }
                    }],
                    "paragraphData": {}
                })
        elif child.name in ["p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "blockquote", "img", "br", "table", "em", "i", "span", "b", "a"]:
            # These are block-level elements or elements that should result in a block-level Ricos node
            ricos_output_nodes.extend(_convert_html_element_to_ricos_nodes(child, image_importer, paragraph_spacing_px))
        elif child.name:
            # For any other unhandled top-level tags, convert to HTML node.
            print(f"INFO: Unhandled top-level HTML tag '{child.name}'. Converting to HTML node.")
            ricos_output_nodes.append({
                "type": "HTML",
                "id": generate_ricos_id(),
                "htmlData": {
                    "html": str(child),
                    "source": "HTML",
                    "containerData": {
                        "width": {"custom": "940px"}
                    }
                }
            })

    print(f"DEBUG: Generated Ricos content (first 500 chars): {str(ricos_output_nodes)[:500]}...")
    return {"nodes": ricos_output_nodes}
