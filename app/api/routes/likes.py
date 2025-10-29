from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ensure_onboarded, get_db_session
from app.db.models.post import Post
from app.db.models.user import User
from app.services import likes as like_service

router = APIRouter()


async def _get_post(session: AsyncSession, post_id: int) -> Post:
    post = await session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@router.post("/{post_id}/likes/toggle")
async def toggle_like_endpoint(
        post_id: int,
        user: User = Depends(ensure_onboarded),
        session: AsyncSession = Depends(get_db_session),
) -> dict[str, int | bool]:
    post = await _get_post(session, post_id)
    liked, like_count = await like_service.toggle_like(session, post, user)
    return {"liked": liked, "like_count": like_count}
