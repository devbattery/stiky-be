from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import ensure_onboarded, get_db_session
from app.db.models.blog import Blog
from app.db.models.comment import Comment
from app.db.models.post import Post
from app.db.models.user import User
from app.schemas.comment import CommentCreate, CommentPublic
from app.services import comments as comment_service

router = APIRouter()


async def _get_post(session: AsyncSession, post_id: int) -> Post:
    stmt = (
        select(Post)
        .where(Post.id == post_id)
        .options(selectinload(Post.blog).selectinload(Blog.owner))
    )
    result = await session.execute(stmt)
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@router.get("/{post_id}/comments", response_model=list[CommentPublic])
async def list_comments_endpoint(
        post_id: int,
        session: AsyncSession = Depends(get_db_session),
) -> list[CommentPublic]:
    post = await _get_post(session, post_id)
    return await comment_service.list_comments(session, post)


@router.post("/{post_id}/comments", response_model=CommentPublic, status_code=status.HTTP_201_CREATED)
async def add_comment_endpoint(
        post_id: int,
        payload: CommentCreate,
        user: User = Depends(ensure_onboarded),
        session: AsyncSession = Depends(get_db_session),
) -> CommentPublic:
    post = await _get_post(session, post_id)
    return await comment_service.add_comment(session, post, user, payload)


@router.delete("/{post_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment_endpoint(
        post_id: int,
        comment_id: int,
        user: User = Depends(ensure_onboarded),
        session: AsyncSession = Depends(get_db_session),
) -> None:
    post = await _get_post(session, post_id)
    comment = await session.get(Comment, comment_id)
    if not comment or comment.post_id != post.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment.user_id != user.id and post.blog.owner.id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to delete")
    await comment_service.delete_comment(session, comment)
