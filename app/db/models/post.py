from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base
from app.db.models.enums import PostCategory, PostStatus

if TYPE_CHECKING:
    from app.db.models.blog import Blog
    from app.db.models.tag import PostTag
    from app.db.models.comment import Comment
    from app.db.models.like import PostLike


class Post(Base):
    __tablename__ = "posts"
    __table_args__ = (
        UniqueConstraint("blog_id", "slug", name="uq_posts_blog_slug"),
        CheckConstraint("char_length(title) BETWEEN 1 AND 120", name="ck_posts_title_length"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    blog_id: Mapped[int] = mapped_column(ForeignKey("blogs.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    category: Mapped[PostCategory] = mapped_column(Enum(PostCategory, name="post_category"), nullable=False)
    status: Mapped[PostStatus] = mapped_column(Enum(PostStatus, name="post_status"), default=PostStatus.draft,
                                               nullable=False)
    summary: Mapped[str | None] = mapped_column(String(300), nullable=True)
    content_md: Mapped[str] = mapped_column(Text, nullable=False)
    content_html: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    blog: Mapped["Blog"] = relationship(back_populates="posts")
    tags: Mapped[list["PostTag"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    comments: Mapped[list["Comment"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    likes: Mapped[list["PostLike"]] = relationship(back_populates="post", cascade="all, delete-orphan")
