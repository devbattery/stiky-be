from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.blog import Blog
from app.db.models.post import Post
from app.db.models.tag import PostTag, Tag
from app.schemas.blog import BlogDetail
from app.schemas.tag import TagSummary
from app.schemas.user import BlogPublic, UserPublic


async def get_blog_by_slug(session: AsyncSession, slug: str) -> Blog | None:
    stmt = select(Blog).where(Blog.slug == slug)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_blog_detail(session: AsyncSession, slug: str) -> BlogDetail | None:
    blog = await get_blog_by_slug(session, slug)
    if not blog:
        return None
    total_posts = await session.scalar(select(func.count()).select_from(Post).where(Post.blog_id == blog.id))
    total_tags = await session.scalar(select(func.count()).select_from(Tag).where(Tag.blog_id == blog.id))
    return BlogDetail(
        **BlogPublic.model_validate(blog).model_dump(),
        owner=UserPublic.model_validate(blog.owner),
        total_posts=total_posts or 0,
        total_tags=total_tags or 0,
    )


async def list_blog_tags(session: AsyncSession, blog: Blog) -> list[TagSummary]:
    stmt: Select = (
        select(Tag, func.count(PostTag.post_id).label("post_count"))
        .join(PostTag, PostTag.tag_id == Tag.id)
        .where(Tag.blog_id == blog.id)
        .group_by(Tag.id)
        .order_by(Tag.name.asc())
    )
    result = await session.execute(stmt)
    items = []
    for tag, post_count in result:
        items.append(
            TagSummary(
                id=tag.id,
                name=tag.name,
                slug=tag.slug,
                post_count=post_count or 0,
            )
        )
    return items
