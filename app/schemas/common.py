from __future__ import annotations

from datetime import datetime
from typing import Generic, Sequence, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class PaginatedResponse(BaseModel, Generic[T]):
    items: Sequence[T]
    total: int
    page: int
    size: int


class MetaResponse(BaseModel):
    data: dict
    error: dict | None = None
