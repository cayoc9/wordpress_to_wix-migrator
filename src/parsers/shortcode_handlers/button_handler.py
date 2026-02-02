from typing import Dict, Optional

def handle_button(attrs: Dict[str, str], content: Optional[str]) -> str:
    """Converte o shortcode [button] em uma tag <a> estilizada."""
    href = attrs.get("href", "#")
    target = attrs.get("target", "_self")
    text = content or ""
    return f'<a href="{href}" target="{target}" class="wp-block-button__link">{text}</a>'