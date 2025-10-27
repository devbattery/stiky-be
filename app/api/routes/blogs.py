from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.schemas.blog import BlogDetail
from app.schemas.tag import TagSummary
from app.services import blogs as blog_service

router = APIRouter()


@router.get("/{slug}", response_model=BlogDetail)
async def get_blog(
        slug: str = Path(..., min_length=3),
        session: AsyncSession = Depends(get_db_session),
) -> BlogDetail:
    blog = await blog_service.get_blog_detail(session, slug)
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    return blog


@router.get("/{slug}/tags", response_model=list[TagSummary])
async def get_blog_tags(
        slug: str = Path(..., min_length=3),
        session: AsyncSession = Depends(get_db_session),
) -> list[TagSummary]:
    blog = await blog_service.get_blog_by_slug(session, slug)
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    return await blog_service.list_blog_tags(session, blog)
