import pytest

from src.extractors.wordpress_extractor import _parse_taxonomy_field


@pytest.mark.parametrize(
    "input_value,expected",
    [
        ("Geral, Notícias", ["Geral", "Notícias"]),
        ("Tecnologia|Inovação", ["Tecnologia", "Inovação"]),
        ("Geral, Análises|Opinião", ["Geral", "Análises", "Opinião"]),
        ("Tecnologia & Inovação", ["Tecnologia & Inovação"]),
        ("Dicas & Truques", ["Dicas & Truques"]),
        ("  Geral ,   Notícias  ", ["Geral", "Notícias"]),
        ("Geral,,Notícias| |Opinião", ["Geral", "Notícias", "Opinião"]),
        ("", []),
        (None, []),
    ],
)
def test_parse_taxonomy_field(input_value, expected):
    """Verifica a extração correta de campos de taxonomia."""
    assert _parse_taxonomy_field(input_value) == expected

