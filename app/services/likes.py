from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.like import PostLike
from app.db.models.post import Post
from app.db.models.user import User


async def toggle_like(session: AsyncSession, post: Post, user: User) -> tuple[bool, int]:
    stmt = select(PostLike).where(PostLike.post_id == post.id, PostLike.user_id == user.id)
    result = await session.execute(stmt)
    like = result.scalar_one_or_none()
    liked = False
    if like:
        await session.execute(delete(PostLike).where(PostLike.id == like.id))
        post.like_count = max(0, post.like_count - 1)
    else:
        like = PostLike(post_id=post.id, user_id=user.id)
        session.add(like)
        post.like_count += 1
        liked = True
    await session.commit()
    await session.refresh(post)
    return liked, post.like_count
