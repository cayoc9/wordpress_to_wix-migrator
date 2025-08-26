from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _slugify(value: str) -> str:
    text = value.strip().lower()
    out = []
    prev_dash = False
    for ch in text:
        if ch.isalnum():
            out.append(ch)
            prev_dash = False
        else:
            if not prev_dash:
                out.append("-")
            prev_dash = True
    slug = "".join(out).strip("-")
    return slug[:200]


class WixMediaSrc(BaseModel):
    id: str


class WixImage(BaseModel):
    src: WixMediaSrc
    width: Optional[int] = None
    height: Optional[int] = None


class MediaWixMedia(BaseModel):
    image: Optional[WixImage] = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class PostMedia(BaseModel):
    wix_media: Optional[MediaWixMedia] = Field(None, alias="wixMedia")
    alt_text: Optional[str] = Field(None, alias="altText")
    displayed: Optional[bool] = None
    custom: Optional[bool] = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class WixPost(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    title: str = Field(..., min_length=1)
    excerpt: Optional[str] = None
    member_id: Optional[str] = Field(None, alias="memberId")
    rich_content: Optional[dict[str, Any]] = Field(None, alias="richContent")
    media: Optional[PostMedia] = None
    category_ids: Optional[list[str]] = Field(default=None, alias="categoryIds")
    tag_ids: Optional[list[str]] = Field(default=None, alias="tagIds")
    featured: Optional[bool] = False
    commenting_enabled: Optional[bool] = Field(None, alias="commentingEnabled")
    slug: Optional[str] = Field(None, alias="slug")
    seo_data: Optional[dict[str, Any]] = Field(None, alias="seoData")
    language: Optional[str] = None
    first_published_date: Optional[datetime] = Field(None, alias="firstPublishedDate")

    @field_validator("slug", mode="before")
    @classmethod
    def _ensure_slug(cls, v: Optional[str], info):  # type: ignore[override]
        if v is not None and v.strip():
            return v
        title = info.data.get("title")
        if isinstance(title, str) and title.strip():
            return _slugify(title)
        return v

    @field_validator("category_ids", "tag_ids", mode="before")
    @classmethod
    def _dedup_ids(cls, v: Optional[list[str]]):
        if not v:
            return v
        seen = set()
        deduped = []
        for item in v:
            if item not in seen:
                seen.add(item)
                deduped.append(item)
        return deduped

    def to_wix_draft_payload(self, publish: Optional[bool] = None) -> dict[str, Any]:
        body: dict[str, Any] = {
            "draftPost": self.model_dump(by_alias=True, exclude_none=True)
        }
        if publish is not None:
            body["publish"] = bool(publish)
        return body
