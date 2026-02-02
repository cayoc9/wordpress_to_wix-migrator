import os
import sys

import pytest

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.migration_tool import WordPressMigrationTool


def test_migrate_posts_pipeline(monkeypatch):
    tool = WordPressMigrationTool(config={"migration": {"dry_run": False}})
    posts = [
        {
            "Slug": "post-1",
            "ContentHTML": "<p>Hello</p><img src='http://example.com/img.jpg' />",
            "FeaturedImageUrl": "http://example.com/cover.jpg",
            "Categories": ["Tech"],
            "Tags": ["Python", "Testing"],
            "Permalink": "http://old.example.com/post-1",
        }
    ]

    monkeypatch.setattr(
        "src.migration_tool.get_or_create_author_id",
        lambda cfg, email, default: "member-1",
    )

    import_calls = []

    def fake_import_image(cfg, url):
        import_calls.append(url)
        return "media-id"

    monkeypatch.setattr(
        "src.migration_tool.import_image_from_url", fake_import_image
    )

    def fake_get_terms(cfg, kind, terms):
        return [f"{kind}-{t}" for t in terms]

    monkeypatch.setattr(
        "src.migration_tool.get_or_create_terms", fake_get_terms
    )

    captured = {}

    def fake_create_draft(cfg, post, ricos, *, member_id):
        captured["ricos"] = ricos
        return {"draftPost": {"id": "draft-1"}}

    monkeypatch.setattr(
        "src.migration_tool.create_draft_post", fake_create_draft
    )

    publish_info = {}

    def fake_publish(cfg, draft_id):
        publish_info["draft_id"] = draft_id
        return {"post": {"url": f"https://new.example.com/post/{posts[0]['Slug']}"}}

    monkeypatch.setattr(
        "src.migration_tool.publish_post", fake_publish
    )

    tool.migrate_posts(posts, new_base_url="https://new.example.com")

    assert posts[0]["FeaturedImageId"] == "media-id"
    assert posts[0]["CategoryIds"] == ["categories-Tech"]
    assert posts[0]["TagIds"] == ["tags-Python", "tags-Testing"]
    assert len(import_calls) == 2

    ricos = captured.get("ricos")
    assert ricos is not None and "nodes" in ricos
    assert any(
        node.get("type") == "IMAGE" and
        node.get("imageData", {}).get("image", {}).get("src", {}).get("id") == "media-id"
        for node in ricos["nodes"]
    )

    assert publish_info["draft_id"] == "draft-1"
