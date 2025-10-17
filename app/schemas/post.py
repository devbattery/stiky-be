from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models.enums import PostCategory, PostStatus


class PostTagInfo(BaseModel):
    id: int
    name: str
    slug: str
    count: int | None = None

    model_config = {"from_attributes": True}


class PostSummary(BaseModel):
    id: int
    title: str
    slug: str
    category: PostCategory
    status: PostStatus
    like_count: int
    comment_count: int
    view_count: int
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PostDetail(PostSummary):
    content_md: str
    content_html: str
    tags: list[PostTagInfo]


class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    category: PostCategory
    status: PostStatus = PostStatus.draft
    content_md: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)


class PostUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=120)
    category: PostCategory | None = None
    status: PostStatus | None = None
    content_md: str | None = Field(None, min_length=1)
    tags: list[str] | None = None
