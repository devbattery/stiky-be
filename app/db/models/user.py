from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base

if TYPE_CHECKING:
    from app.db.models.blog import Blog
    from app.db.models.comment import Comment
    from app.db.models.like import PostLike
    from app.db.models.token import RefreshToken


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False, index=True)
    nickname: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, unique=True)
    profile_image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    blog: Mapped["Blog"] = relationship(back_populates="owner", uselist=False)
    comments: Mapped[list["Comment"]] = relationship(back_populates="author")
    likes: Mapped[list["PostLike"]] = relationship(back_populates="user")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user")
