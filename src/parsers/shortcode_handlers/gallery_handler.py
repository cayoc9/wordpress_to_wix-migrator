from typing import Dict, Optional

def handle_gallery(attrs: Dict[str, str], content: Optional[str]) -> str:
    """Converte o shortcode [gallery] em uma série de tags <img>."""
    ids_str = attrs.get("ids", "")
    if not ids_str:
        return ""
    
    ids = [img_id.strip() for img_id in ids_str.split(",")]
    
    # Como não temos acesso ao banco de dados do WordPress para mapear IDs para URLs,
    # vamos gerar tags de imagem com um placeholder de URL. O `image_handler` do ricos_parser
    # irá então processar estas tags.
    # Uma implementação futura poderia usar um arquivo de mapeamento (id -> url).
    
    image_tags = []
    for img_id in ids:
        # Usamos uma URL de placeholder que pode ser identificada e substituída mais tarde,
        # ou simplesmente para que o image_handler possa tentar fazer o upload.
        placeholder_url = f"https://via.placeholder.com/150/000000/FFFFFF/?text=ImageID:{img_id}"
        image_tags.append(f'<img src="{placeholder_url}" alt="Gallery image {img_id}" />')
        
    return "\n".join(image_tags)

