from __future__ import annotations
from typing import Any, Dict, List
from bs4.element import Tag
from .utils import generate_ricos_id
import logging

logger = logging.getLogger(__name__)

def handle_script(element: Tag) -> List[Dict[str, Any]]:
    """
    Handle script elements.
    
    If the script tag has a src attribute containing "rdstation",
    convert the entire element to an HTML Ricos node.
    Otherwise, use the default fallback behavior.
    """
    logger.debug(f"handle_script called with element: {element}")
    nodes: List[Dict[str, Any]] = []
    src = element.get("src")
    
    # Check if src contains "rdstation"
    if src and isinstance(src, str) and "rdstation" in src:
        logger.debug("Found rdstation script, converting to HTML node")
        # Convert the entire script element to an HTML Ricos node
        nodes.append({
            "type": "HTML",
            "id": generate_ricos_id(),
            "htmlData": {
                "html": str(element),
                "source": "HTML",
                "containerData": {"width": {"custom": "940px"}}
            }
        })
    else:
        logger.debug("Non-rdstation script or inline script, converting to HTML node")
        # Fallback for other scripts or inline scripts
        # Convert to HTML node to preserve the script content
        nodes.append({
            "type": "HTML",
            "id": generate_ricos_id(),
            "htmlData": {
                "html": str(element),
                "source": "HTML",
                "containerData": {"width": {"custom": "940px"}}
            }
        })
    
    logger.debug(f"handle_script returning nodes: {nodes}")
    return nodes