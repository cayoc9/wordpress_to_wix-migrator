import pytest
from models.wix_post import WixPost

def test_wix_post_creation():
    # Teste básico de criação de post
    post_data = {
        "title": "Test Post",
        "excerpt": "This is a test post",
        "slug": "test-post"
    }
    
    post = WixPost(**post_data)
    assert post.title == "Test Post"
    assert post.excerpt == "This is a test post"
    assert post.slug == "test-post"

def test_wix_post_slug_generation():
    # Teste de geração automática de slug
    post_data = {
        "title": "My Test Post with Spaces and CAPS"
    }
    
    post = WixPost(**post_data)
    assert post.slug == "my-test-post-with-spaces-and-caps"

def test_wix_post_payload_generation():
    # Teste de geração de payload
    post_data = {
        "title": "Test Post",
        "excerpt": "This is a test post",
        "slug": "test-post",
        "categoryIds": ["cat1", "cat2"],
        "tagIds": ["tag1", "tag2"]
    }
    
    post = WixPost(**post_data)
    payload = post.to_wix_draft_payload()
    
    assert "draftPost" in payload
    assert payload["draftPost"]["title"] == "Test Post"
    assert payload["draftPost"]["excerpt"] == "This is a test post"
    assert payload["draftPost"]["slug"] == "test-post"
    assert payload["draftPost"]["categoryIds"] == ["cat1", "cat2"]
    assert payload["draftPost"]["tagIds"] == ["tag1", "tag2"]