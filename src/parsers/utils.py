"""
Funções utilitárias para o parser Ricos.
"""

import uuid

def generate_ricos_id() -> str:
    """Gera um ID curto para nodos Ricos."""
    return uuid.uuid4().hex[:12]