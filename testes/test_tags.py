import os
import sys

# Ensure project root is on sys.path for imports when running tests directly
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.tags import parse_tags_field, to_wix_terms_payload


def test_tags_html_entities_and_whitespace():
    raw = "finanças &amp; gestão |  dicas  "
    assert parse_tags_field(raw) == ["finanças & gestão", "dicas"]


def test_tags_split_on_pipe_then_comma():
    assert parse_tags_field("alpha|beta|gamma") == ["alpha", "beta", "gamma"]
    assert parse_tags_field("one, two") == ["one", "two"]


def test_tags_deduplicate_case_insensitive_preserve_first():
    raw = "Marketing|marketing|MARKETING|MarketIng"
    assert parse_tags_field(raw) == ["Marketing"]


def test_to_wix_terms_payload_shape():
    cats = ["Marketing", "Tutoriais"]
    tags = ["finanças & gestão", "dicas"]
    payload = to_wix_terms_payload(cats, tags)
    assert payload == {
        "categories": [
            {"category": {"label": "Marketing"}},
            {"category": {"label": "Tutoriais"}},
        ],
        "tags": [
            {"label": "finanças & gestão"},
            {"label": "dicas"},
        ],
    }

