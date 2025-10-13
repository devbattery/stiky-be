from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base

if TYPE_CHECKING:
    from app.db.models.post import Post
    from app.db.models.tag import Tag
    from app.db.models.user import User


class Blog(Base):
    __tablename__ = "blogs"
    __table_args__ = (UniqueConstraint("slug"), UniqueConstraint("user_id"))

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    owner: Mapped["User"] = relationship(back_populates="blog")
    posts: Mapped[list["Post"]] = relationship(back_populates="blog", cascade="all, delete-orphan")
    tags: Mapped[list["Tag"]] = relationship(back_populates="blog", cascade="all, delete-orphan")
