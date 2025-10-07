"""initial schema"""

from __future__ import annotations

import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

post_status_enum = pg.ENUM("draft", "published", name="post_status")
post_category_enum = pg.ENUM(
    "free",
    "dev",
    "celeb",
    "love",
    "work",
    "book",
    "health",
    name="post_category",
)


def upgrade() -> None:
    op.execute("DROP TYPE IF EXISTS post_status CASCADE;")
    op.execute("DROP TYPE IF EXISTS post_category CASCADE;")

    op.create_table(
        "users",
        sa.Column("id", pg.UUID(as_uuid=False), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False, unique=True),
        sa.Column("nickname", sa.String(length=32), nullable=True, unique=True),
        sa.Column("profile_image_url", sa.String(length=512), nullable=True),
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "blogs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", pg.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("slug"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_blogs_slug"), "blogs", ["slug"], unique=False)

    op.create_table(
        "auth_codes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("code_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ip_fingerprint", sa.String(length=128), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f("ix_auth_codes_email"), "auth_codes", ["email"], unique=False)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", pg.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rotated_from_id", sa.String(length=36), nullable=True),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"], unique=False)

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("blog_id", sa.Integer(), sa.ForeignKey("blogs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("blog_id", "slug", name="uq_tags_blog_slug"),
    )
    op.create_index(op.f("ix_tags_slug"), "tags", ["slug"], unique=False)

    op.create_table(
        "posts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("blog_id", sa.Integer(), sa.ForeignKey("blogs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=150), nullable=False),
        sa.Column("category", post_category_enum, nullable=False),
        sa.Column("status", post_status_enum, nullable=False, server_default="draft"),
        sa.Column("summary", sa.String(length=300), nullable=True),
        sa.Column("content_md", sa.Text(), nullable=False),
        sa.Column("content_html", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("like_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comment_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("blog_id", "slug", name="uq_posts_blog_slug"),
    )
    op.create_index(op.f("ix_posts_slug"), "posts", ["slug"], unique=False)

    op.create_table(
        "images",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", pg.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("post_id", sa.Integer(), sa.ForeignKey("posts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("url", sa.String(length=512), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("format", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "post_tags",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("post_id", sa.Integer(), sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tag_id", sa.Integer(), sa.ForeignKey("tags.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("post_id", "tag_id", name="uq_post_tags_post_tag"),
    )

    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("post_id", sa.Integer(), sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", pg.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("comments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("content", sa.String(length=1000), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("depth", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_comments_post_id"), "comments", ["post_id"], unique=False)
    op.create_index(op.f("ix_comments_user_id"), "comments", ["user_id"], unique=False)

    op.create_table(
        "post_likes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("post_id", sa.Integer(), sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", pg.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "post_id", name="uq_post_likes_user_post"),
    )
    op.create_index(op.f("ix_post_likes_post_id"), "post_likes", ["post_id"], unique=False)
    op.create_index(op.f("ix_post_likes_user_id"), "post_likes", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_post_likes_user_id"), table_name="post_likes")
    op.drop_index(op.f("ix_post_likes_post_id"), table_name="post_likes")
    op.drop_table("post_likes")

    op.drop_index(op.f("ix_comments_user_id"), table_name="comments")
    op.drop_index(op.f("ix_comments_post_id"), table_name="comments")
    op.drop_table("comments")

    op.drop_table("post_tags")

    op.drop_table("images")

    op.drop_index(op.f("ix_posts_slug"), table_name="posts")
    op.drop_table("posts")
    op.execute("DROP TYPE IF EXISTS post_status;")
    op.execute("DROP TYPE IF EXISTS post_category;")

    op.drop_index(op.f("ix_tags_slug"), table_name="tags")
    op.drop_table("tags")

    op.drop_index(op.f("ix_refresh_tokens_user_id"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index(op.f("ix_auth_codes_email"), table_name="auth_codes")
    op.drop_table("auth_codes")

    op.drop_index(op.f("ix_blogs_slug"), table_name="blogs")
    op.drop_table("blogs")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
