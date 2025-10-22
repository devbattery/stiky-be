from __future__ import annotations

from datetime import UTC, datetime
from typing import Iterable

from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import generate_slug
from app.db.models.blog import Blog
from app.db.models.enums import PostCategory, PostStatus
from app.db.models.post import Post
from app.db.models.tag import PostTag, Tag
from app.schemas.post import PostCreate, PostDetail, PostSummary, PostTagInfo, PostUpdate
from app.utils.markdown import markdown_to_html
from app.utils.slug import ensure_unique_slug, normalize_slug


async def list_posts(
        session: AsyncSession,
        *,
        blog: Blog,
        page: int,
        size: int,
        tag_slug: str | None = None,
        category: PostCategory | None = None,
        status_filter: PostStatus | None = PostStatus.published,
) -> tuple[list[PostSummary], int]:
    base_stmt: Select = select(Post).where(Post.blog_id == blog.id)
    if status_filter:
        base_stmt = base_stmt.where(Post.status == status_filter)
    if category:
        base_stmt = base_stmt.where(Post.category == category)
    if tag_slug:
        base_stmt = base_stmt.join(PostTag, PostTag.post_id == Post.id).join(Tag, Tag.id == PostTag.tag_id)
        base_stmt = base_stmt.where(Tag.slug == tag_slug)

    total_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = await session.scalar(total_stmt)

    stmt = base_stmt.order_by(Post.published_at.desc().nulls_last(), Post.created_at.desc())
    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await session.execute(stmt)
    posts = [PostSummary.model_validate(post) for post in result.scalars().all()]
    return posts, total or 0


async def _collect_existing_slugs(session: AsyncSession, blog: Blog, base_slug: str,
                                  exclude_post_id: int | None = None) -> set[str]:
    stmt = select(Post.slug).where(Post.blog_id == blog.id, Post.slug.like(f"{base_slug}%"))
    if exclude_post_id:
        stmt = stmt.where(Post.id != exclude_post_id)
    result = await session.execute(stmt)
    return {row[0] for row in result}


async def create_post(session: AsyncSession, blog: Blog, data: PostCreate) -> Post:
    base_slug = normalize_slug(data.title) or generate_slug("post")
    existing_slugs = await _collect_existing_slugs(session, blog, base_slug)
    final_slug = ensure_unique_slug(base_slug, existing_slugs)

    category_value = (
        data.category.value
        if isinstance(data.category, PostCategory)
        else str(data.category).lower()
    )
    status_value = (
        data.status.value
        if isinstance(data.status, PostStatus)
        else str(data.status).lower()
    )

    category_value = PostCategory(category_value).value
    status_value = PostStatus(status_value).value

    post = Post(
        blog_id=blog.id,
        title=data.title,
        slug=final_slug,
        category=category_value,
        status=status_value,
        content_md=data.content_md,
        content_html=markdown_to_html(data.content_md),
    )
    if data.status == PostStatus.published:
        post.published_at = datetime.now(UTC)
    session.add(post)
    await session.flush()

    await _sync_tags(session, blog, post, data.tags)
    await session.commit()
    stmt = (
        select(Post)
        .where(Post.id == post.id)
        .options(selectinload(Post.tags).selectinload(PostTag.tag))
    )
    refreshed = await session.execute(stmt)
    return refreshed.scalar_one()


async def update_post(session: AsyncSession, blog: Blog, post: Post, data: PostUpdate) -> Post:
    if data.title and data.title != post.title:
        base_slug = normalize_slug(data.title) or generate_slug("post")
        existing_slugs = await _collect_existing_slugs(session, blog, base_slug, exclude_post_id=post.id)
        post.slug = ensure_unique_slug(base_slug, existing_slugs)
        post.title = data.title
    if data.category and data.category != post.category:
        normalized_category = (
            data.category.value
            if isinstance(data.category, PostCategory)
            else str(data.category).lower()
        )
        post.category = PostCategory(normalized_category).value
    if data.status and data.status != post.status:
        normalized_status = (
            data.status.value
            if isinstance(data.status, PostStatus)
            else str(data.status).lower()
        )
        post.status = PostStatus(normalized_status).value
        if data.status == PostStatus.published and not post.published_at:
            post.published_at = datetime.now(UTC)
    if data.content_md and data.content_md != post.content_md:
        post.content_md = data.content_md
        post.content_html = markdown_to_html(data.content_md)
    if data.tags is not None:
        await _sync_tags(session, blog, post, data.tags)
    await session.commit()
    stmt = (
        select(Post)
        .where(Post.id == post.id)
        .options(selectinload(Post.tags).selectinload(PostTag.tag))
    )
    refreshed = await session.execute(stmt)
    return refreshed.scalar_one()


async def delete_post(session: AsyncSession, post: Post) -> None:
    await session.delete(post)
    await session.commit()


async def get_post_by_slug(
        session: AsyncSession,
        blog: Blog,
        slug: str,
        *,
        include_unpublished: bool = False,
) -> Post | None:
    stmt = select(Post).where(Post.blog_id == blog.id, Post.slug == slug)
    if not include_unpublished:
        stmt = stmt.where(Post.status == PostStatus.published)
    stmt = stmt.options(selectinload(Post.tags).selectinload(PostTag.tag))
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def serialize_post_detail(post: Post) -> PostDetail:
    tag_infos = [
        PostTagInfo(
            id=pt.tag.id,
            name=pt.tag.name,
            slug=pt.tag.slug,
        )
        for pt in post.tags
    ]
    return PostDetail(
        id=post.id,
        title=post.title,
        slug=post.slug,
        category=post.category,
        status=post.status,
        like_count=post.like_count,
        comment_count=post.comment_count,
        view_count=post.view_count,
        published_at=post.published_at,
        created_at=post.created_at,
        updated_at=post.updated_at,
        content_md=post.content_md,
        content_html=post.content_html,
        tags=tag_infos,
    )


def serialize_post_summary(post: Post) -> PostSummary:
    return PostSummary.model_validate(post)


async def _sync_tags(session: AsyncSession, blog: Blog, post: Post, requested_tags: Iterable[str]) -> None:
    normalized_tags = []
    seen = set()
    for raw in requested_tags:
        clean = raw.strip()
        if not clean:
            continue
        slug = normalize_slug(clean)
        if slug in seen:
            continue
        seen.add(slug)
        normalized_tags.append((clean, slug))

    existing_tags: dict[str, Tag] = {}
    if normalized_tags:
        existing_stmt = select(Tag).where(
            Tag.blog_id == blog.id,
            Tag.slug.in_([slug for _, slug in normalized_tags]),
        )
        existing_result = await session.execute(existing_stmt)
        existing_tags = {tag.slug: tag for tag in existing_result.scalars()}

    for name, slug in normalized_tags:
        if slug not in existing_tags:
            tag = Tag(blog_id=blog.id, name=name, slug=slug)
            session.add(tag)
            await session.flush()
            existing_tags[slug] = tag

    await session.execute(delete(PostTag).where(PostTag.post_id == post.id))
    for _, slug in normalized_tags:
        tag = existing_tags[slug]
        session.add(PostTag(post_id=post.id, tag_id=tag.id))
    await session.flush()
