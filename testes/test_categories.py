import os
import sys

# Ensure project root is on sys.path for imports when running tests directly
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.categories import parse_categories_field, category_name_to_slug


def test_single_category_with_html_entity_is_normalized():
    assert parse_categories_field("Dicas &amp; Hacks") == ["Dicas & Hacks"]


def test_multiple_categories_pipe_separator_and_entities():
    raw = "Dicas &amp; Hacks|Saúde financeira|Inovações &amp; investimentos"
    expected = [
        "Dicas & Hacks",
        "Saúde financeira",
        "Inovações & investimentos",
    ]
    assert parse_categories_field(raw) == expected


def test_fallback_to_comma_separator():
    raw = "Legislação, Tutoriais"
    assert parse_categories_field(raw) == ["Legislação", "Tutoriais"]


def test_unknown_category_is_unescaped_and_preserved():
    # Not in the canonical list; should still unescape and keep as-is
    raw = "Curiosidades &amp; Outros"
    assert parse_categories_field(raw) == ["Curiosidades & Outros"]


def test_deduplication_and_whitespace_trimming_order_preserved():
    raw = "Marketing| marketing |Marketing"
    assert parse_categories_field(raw) == ["Marketing"]


def test_accent_insensitive_matching_returns_canonical_name():
    # Input missing accents should still map to the canonical accented form
    raw = "Gestao &amp; Organizacao"
    assert parse_categories_field(raw) == ["Gestão & Organização"]


def test_category_name_to_slug_mapping():
    assert category_name_to_slug("Gestão & Organização") == "gestao-organizacao"
    assert category_name_to_slug("Dicas & Hacks") == "dicas-hacks"
    assert category_name_to_slug("Algo Desconhecido") == ""

