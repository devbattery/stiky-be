from __future__ import annotations

from typing import Annotated, AsyncIterator

from fastapi import Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_token
from app.db.base import SessionLocal
from app.db.models.user import User


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


async def get_current_user(
        request: Request,
        session: Annotated[AsyncSession, Depends(get_db_session)],
        access_token: str | None = Cookie(default=None, alias="access_token"),
) -> User:
    token = access_token
    if token is None:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ")
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = decode_token(token)
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from None

    if payload.get("typ") == "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


async def ensure_onboarded(user: Annotated[User, Depends(get_current_user)]) -> User:
    if not user.onboarding_completed:
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED, detail="Onboarding incomplete"
        )
    return user


async def get_current_user_optional(
        request: Request,
        session: Annotated[AsyncSession, Depends(get_db_session)],
        access_token: str | None = Cookie(default=None, alias="access_token"),
) -> User | None:
    try:
        return await get_current_user(request, session, access_token)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            return None
        raise


async def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    cookie_domain = settings.security.cookie_domain
    secure = settings.security.secure_cookies
    same_site = settings.security.same_site
    response.set_cookie(
        "access_token",
        access_token,
        max_age=settings.jwt.access_token_ttl_minutes * 60,
        httponly=True,
        secure=secure,
        samesite=same_site,
        domain=cookie_domain,
        path="/",
    )
    response.set_cookie(
        "refresh_token",
        refresh_token,
        max_age=settings.jwt.refresh_token_ttl_days * 24 * 60 * 60,
        httponly=True,
        secure=secure,
        samesite=same_site,
        domain=cookie_domain,
        path="/api/v1/auth",
    )


def clear_auth_cookies(response: Response) -> None:
    cookie_domain = settings.security.cookie_domain
    response.delete_cookie("access_token", domain=cookie_domain, path="/")
    response.delete_cookie("refresh_token", domain=cookie_domain, path="/api/v1/auth")
