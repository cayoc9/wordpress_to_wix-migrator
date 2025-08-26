from typing import Dict, Optional
from urllib.parse import urlparse

def handle_embed(attrs: Dict[str, str], content: Optional[str]) -> str:
    """Converte o shortcode [embed] em um <iframe> para ser processado posteriormente."""
    url = content.strip() if content else ""
    if not url:
        return ""
    # Simplificação: assume que o conteúdo é a URL.
    # Uma implementação mais robusta poderia verificar a URL.
    # Apenas um exemplo para youtube
    parsed_url = urlparse(url)
    if 'youtube.com' in parsed_url.netloc or 'youtu.be' in parsed_url.netloc:
         # Deixa o iframe_handler fazer o trabalho pesado
        return f'<iframe src="{url}"></iframe>'
    return f'<!-- embed para {url} não suportado -->'