from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, set_auth_cookies
from app.core.security import decode_token, hash_token
from app.db.models.user import User
from app.schemas.auth import AuthResponse, OTPRequest, OTPVerify
from app.schemas.user import UserPublic
from app.services import auth as auth_service

router = APIRouter()


@router.post("/request-otp", status_code=status.HTTP_202_ACCEPTED)
async def request_otp_endpoint(
        payload: OTPRequest,
        request: Request,
        session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    await auth_service.request_otp(session, payload.email, request)
    return {"status": "sent"}


@router.post("/verify-otp", response_model=AuthResponse)
async def verify_otp_endpoint(
        payload: OTPVerify,
        response: Response,
        session: AsyncSession = Depends(get_db_session),
) -> AuthResponse:
    user, _, _ = await auth_service.verify_otp(session, payload.email, payload.code, response)
    onboarding_required = not user.onboarding_completed
    return AuthResponse(user=UserPublic.model_validate(user), onboarding_required=onboarding_required)


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token_endpoint(
        response: Response,
        refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
        session: AsyncSession = Depends(get_db_session),
) -> AuthResponse:
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
    try:
        payload = decode_token(refresh_token)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc
    if payload.get("typ") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    token_hash_value = hash_token(refresh_token)
    token_model = await auth_service.get_refresh_token(session, token_hash_value)
    if not token_model:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    access_token, new_refresh_token, _ = await auth_service.rotate_refresh_token(session, token_model)
    await session.commit()

    set_auth_cookies(response, access_token, new_refresh_token)

    user = await session.get(User, token_model.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    onboarding_required = not user.onboarding_completed
    return AuthResponse(user=UserPublic.model_validate(user), onboarding_required=onboarding_required)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_endpoint(
        response: Response,
        refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
        session: AsyncSession = Depends(get_db_session),
) -> Response:
    refresh_hash = hash_token(refresh_token) if refresh_token else None
    await auth_service.clear_session(response, session, refresh_hash)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
