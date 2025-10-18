from __future__ import annotations

from pydantic import BaseModel


class TagSummary(BaseModel):
    id: int
    name: str
    slug: str
    post_count: int

    model_config = {"from_attributes": True}
