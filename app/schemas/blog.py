from __future__ import annotations

from pydantic import BaseModel

from app.schemas.user import BlogPublic


class BlogAvailabilityResponse(BaseModel):
    available: bool


class BlogDetail(BlogPublic):
    owner: "UserPublic"
    total_posts: int
    total_tags: int

    model_config = {"from_attributes": True}


from app.schemas.user import UserPublic
