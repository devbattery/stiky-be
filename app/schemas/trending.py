from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.db.models.enums import PostCategory
from app.schemas.post import PostSummary
from app.schemas.user import BlogPublic, UserPublic


class TrendingPost(BaseModel):
    post: PostSummary
    blog: BlogPublic


class TrendingUser(BaseModel):
    user: UserPublic
    blog: BlogPublic
    like_count: int
    rank: int


class CategoryTrending(BaseModel):
    category: PostCategory
    posts: list[PostSummary]
    generated_at: datetime
