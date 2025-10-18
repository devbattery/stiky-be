from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.user import UserPublic


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)
    parent_id: int | None = Field(None)


class CommentPublic(BaseModel):
    id: int
    post_id: int
    user_id: str
    content: str
    is_deleted: bool
    depth: int
    created_at: datetime
    updated_at: datetime
    author: UserPublic

    model_config = {"from_attributes": True}
