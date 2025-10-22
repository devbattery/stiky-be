from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.comment import Comment
from app.db.models.post import Post
from app.db.models.user import User
from app.schemas.comment import CommentCreate, CommentPublic
from app.schemas.user import UserPublic


async def list_comments(session: AsyncSession, post: Post) -> list[CommentPublic]:
    stmt = (
        select(Comment)
        .where(Comment.post_id == post.id)
        .order_by(Comment.created_at.asc())
        .options(selectinload(Comment.author))
    )
    result = await session.execute(stmt)
    comments = [
        CommentPublic(
            id=item.id,
            post_id=item.post_id,
            user_id=item.user_id,
            content="" if item.is_deleted else item.content,
            is_deleted=item.is_deleted,
            depth=item.depth,
            created_at=item.created_at,
            updated_at=item.updated_at,
            author=UserPublic.model_validate(item.author),
        )
        for item in result.scalars().all()
    ]
    return comments


async def add_comment(session: AsyncSession, post: Post, user: User, payload: CommentCreate) -> CommentPublic:
    depth = 0
    if payload.parent_id:
        parent = await session.get(Comment, payload.parent_id)
        if parent and parent.post_id == post.id:
            depth = parent.depth + 1
        else:
            payload.parent_id = None

    comment = Comment(
        post_id=post.id,
        user_id=user.id,
        parent_id=payload.parent_id,
        content=payload.content,
        depth=depth,
    )
    session.add(comment)

    post.comment_count += 1
    await session.commit()
    await session.refresh(comment)
    await session.refresh(post)

    return CommentPublic(
        id=comment.id,
        post_id=comment.post_id,
        user_id=comment.user_id,
        content=comment.content,
        is_deleted=comment.is_deleted,
        depth=comment.depth,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        author=UserPublic.model_validate(user),
    )


async def delete_comment(
        session: AsyncSession,
        comment: Comment,
        *,
        hard_delete: bool = False,
) -> None:
    post = await session.get(Post, comment.post_id)
    if hard_delete:
        await session.delete(comment)
    else:
        comment.is_deleted = True
        comment.content = ""
    if post and post.comment_count > 0:
        post.comment_count -= 1
    await session.commit()
