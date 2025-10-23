from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.blog import Blog
from app.db.models.enums import PostCategory, PostStatus
from app.db.models.like import PostLike
from app.db.models.post import Post
from app.db.models.user import User
from app.schemas.post import PostSummary
from app.schemas.trending import CategoryTrending, TrendingPost, TrendingUser
from app.schemas.user import BlogPublic, UserPublic


async def trending_posts(
        session: AsyncSession,
        *,
        period_days: int = 30,
        limit: int = 10,
) -> list[TrendingPost]:
    since = datetime.now(UTC) - timedelta(days=period_days)
    stmt = (
        select(Post)
        .join(PostLike, PostLike.post_id == Post.id)
        .where(PostLike.created_at >= since, Post.status == PostStatus.published)
        .group_by(Post.id)
        .order_by(func.count(PostLike.id).desc())
        .limit(limit)
        .options(selectinload(Post.blog).selectinload(Blog.owner))
    )
    result = await session.execute(stmt)
    posts = []
    for post in result.scalars().all():
        posts.append(
            TrendingPost(
                post=PostSummary.model_validate(post),
                blog=BlogPublic.model_validate(post.blog),
            )
        )
    return posts


async def trending_by_category(
        session: AsyncSession,
        *,
        period_days: int = 30,
        limit: int = 5,
) -> list[CategoryTrending]:
    since = datetime.now(UTC) - timedelta(days=period_days)
    stmt = (
        select(
            Post.category,
            Post.id,
            func.count(PostLike.id).label("like_count"),
        )
        .join(PostLike, PostLike.post_id == Post.id)
        .where(PostLike.created_at >= since, Post.status == PostStatus.published)
        .group_by(Post.category, Post.id)
        .order_by(Post.category, func.count(PostLike.id).desc())
    )
    result = await session.execute(stmt)
    category_map: dict[PostCategory, list[int]] = {}
    for category, post_id, _ in result:
        category_map.setdefault(category, []).append(post_id)
    trends: list[CategoryTrending] = []
    for category, post_ids in category_map.items():
        top_ids = post_ids[:limit]
        stmt_posts = (
            select(Post)
            .where(Post.id.in_(top_ids))
            .options(selectinload(Post.blog))
        )
        posts_result = await session.execute(stmt_posts)
        posts_by_id = {post.id: post for post in posts_result.scalars().all()}
        ordered_posts = [posts_by_id[pid] for pid in top_ids if pid in posts_by_id]
        summaries = [PostSummary.model_validate(p) for p in ordered_posts]
        trends.append(
            CategoryTrending(
                category=category,
                posts=summaries,
                generated_at=datetime.now(UTC),
            )
        )
    return trends


async def trending_users(
        session: AsyncSession,
        *,
        period_days: int = 30,
        limit: int = 10,
) -> list[TrendingUser]:
    since = datetime.now(UTC) - timedelta(days=period_days)
    stmt = (
        select(User, Blog, func.count(PostLike.id).label("likes"))
        .join(Blog, Blog.user_id == User.id)
        .join(Post, Post.blog_id == Blog.id)
        .join(PostLike, PostLike.post_id == Post.id)
        .where(PostLike.created_at >= since)
        .group_by(User.id, Blog.id)
        .order_by(func.count(PostLike.id).desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    trends = []
    rank = 1
    for user, blog, like_count in result:
        trends.append(
            TrendingUser(
                user=UserPublic.model_validate(user),
                blog=BlogPublic.model_validate(blog),
                like_count=like_count,
                rank=rank,
            )
        )
        rank += 1
    return trends
