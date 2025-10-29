from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.schemas.trending import CategoryTrending, TrendingPost, TrendingUser
from app.services import trending as trending_service

router = APIRouter()


@router.get("/posts", response_model=list[TrendingPost])
async def trending_posts_endpoint(
        period_days: int = Query(30, ge=1, le=365),
        limit: int = Query(10, ge=1, le=50),
        session: AsyncSession = Depends(get_db_session),
) -> list[TrendingPost]:
    return await trending_service.trending_posts(session, period_days=period_days, limit=limit)


@router.get("/by-category", response_model=list[CategoryTrending])
async def trending_by_category_endpoint(
        period_days: int = Query(30, ge=1, le=365),
        limit: int = Query(5, ge=1, le=20),
        session: AsyncSession = Depends(get_db_session),
) -> list[CategoryTrending]:
    return await trending_service.trending_by_category(session, period_days=period_days, limit=limit)


@router.get("/users", response_model=list[TrendingUser])
async def trending_users_endpoint(
        period_days: int = Query(30, ge=1, le=365),
        limit: int = Query(10, ge=1, le=50),
        session: AsyncSession = Depends(get_db_session),
) -> list[TrendingUser]:
    return await trending_service.trending_users(session, period_days=period_days, limit=limit)
