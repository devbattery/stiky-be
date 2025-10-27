from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.db.models.user import User
from app.schemas.user import AvailabilityResponse, MeResponse, OnboardingPayload
from app.services import users as user_service

router = APIRouter()


@router.get("", response_model=MeResponse)
async def get_me(
        user: User = Depends(get_current_user),
) -> MeResponse:
    return await user_service.serialize_me(user)


@router.post("/onboard", response_model=MeResponse)
async def complete_onboarding_endpoint(
        payload: OnboardingPayload,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_db_session),
) -> MeResponse:
    try:
        await user_service.complete_onboarding(session, user, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    await session.refresh(user)
    return await user_service.serialize_me(user)


@router.get("/availability/nickname", response_model=AvailabilityResponse)
async def nickname_availability(
        value: str = Query(..., min_length=2, max_length=20),
        session: AsyncSession = Depends(get_db_session),
) -> AvailabilityResponse:
    available = await user_service.is_nickname_available(session, value)
    return AvailabilityResponse(available=available)


@router.get("/availability/blog-slug", response_model=AvailabilityResponse)
async def blog_slug_availability(
        value: str = Query(..., min_length=3, max_length=30),
        session: AsyncSession = Depends(get_db_session),
) -> AvailabilityResponse:
    available = await user_service.is_blog_slug_available(session, value)
    return AvailabilityResponse(available=available)
