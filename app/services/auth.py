from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Tuple
from uuid import uuid4

from fastapi import HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import set_auth_cookies, clear_auth_cookies
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_otp_code,
    hash_otp_code,
    hash_token,
)
from app.db.models.token import AuthCode, RefreshToken
from app.db.models.user import User
from app.services.email import resend_client
from app.utils.rate_limit import enforce_rate_limit
from app.utils.redis import get_redis


async def _invalidate_existing_codes(session: AsyncSession, email: str) -> None:
    await session.execute(
        update(AuthCode)
        .where(AuthCode.email == email, AuthCode.consumed.is_(False))
        .values(consumed=True, consumed_at=datetime.now(UTC))
    )


async def request_otp(session: AsyncSession, email: str, request: Request) -> None:
    normalized_email = email.strip().lower()
    ip = request.client.host if request.client else "unknown"
    fingerprint = f"{normalized_email}:{ip}"
    await enforce_rate_limit(
        key=f"otp:req:email:{normalized_email}",
        limit=settings.otp_request_limit_per_email,
        window_seconds=settings.otp_request_limit_window_minutes * 60,
    )
    await enforce_rate_limit(
        key=f"otp:req:ip:{ip}",
        limit=settings.otp_request_limit_per_ip,
        window_seconds=settings.otp_request_limit_window_minutes * 60,
    )

    code = generate_otp_code(settings.otp_code_length)
    code_hash = hash_otp_code(code, normalized_email)
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.otp_ttl_minutes)

    await _invalidate_existing_codes(session, normalized_email)

    auth_code = AuthCode(
        email=normalized_email,
        code_hash=code_hash,
        expires_at=expires_at,
        consumed=False,
        ip_fingerprint=fingerprint,
        user_agent=request.headers.get("user-agent"),
    )
    session.add(auth_code)
    await session.commit()

    try:
        await resend_client.send_otp_email(
            email=normalized_email,
            code=code,
            expires_in_minutes=settings.otp_ttl_minutes,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="Failed to send email") from exc


async def verify_otp(
        session: AsyncSession,
        email: str,
        code: str,
        response,
) -> Tuple[User, str, str]:
    normalized_email = email.strip().lower()
    stmt = (
        select(AuthCode)
        .where(AuthCode.email == normalized_email, AuthCode.consumed.is_(False))
        .order_by(AuthCode.created_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    auth_code = result.scalar_one_or_none()
    if not auth_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")

    now = datetime.now(UTC)
    if auth_code.expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code expired")

    expected_hash = hash_otp_code(code, normalized_email)
    if auth_code.code_hash != expected_hash:
        auth_code.attempt_count += 1
        await session.commit()
        if auth_code.attempt_count >= settings.otp_retry_limit:
            auth_code.consumed = True
            auth_code.consumed_at = now
            await session.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code")

    auth_code.consumed = True
    auth_code.consumed_at = now
    await session.commit()

    user = await _get_or_create_user(session, normalized_email)

    access_token, refresh_token, refresh_model = await _issue_tokens(session, user)

    await session.commit()

    await set_auth_cookies(response, access_token, refresh_token)
    return user, access_token, refresh_model.id


async def _get_or_create_user(session: AsyncSession, email: str) -> User:
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        return user
    user = User(email=email)
    session.add(user)
    await session.flush()
    return user


async def _issue_tokens(session: AsyncSession, user: User) -> Tuple[str, str, RefreshToken]:
    token_id = str(uuid4())
    access_token = create_access_token(user.id, extra={"typ": "access"})
    refresh_token = create_refresh_token(user.id, token_id, extra={"typ": "refresh"})
    refresh_model = RefreshToken(
        id=token_id,
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=datetime.now(UTC) + timedelta(days=settings.jwt.refresh_token_ttl_days),
    )
    session.add(refresh_model)
    return access_token, refresh_token, refresh_model


async def rotate_refresh_token(session: AsyncSession, token: RefreshToken) -> Tuple[str, str, RefreshToken]:
    token.revoked = True
    token.revoked_at = datetime.now(UTC)

    new_token_id = str(uuid4())
    access_token = create_access_token(token.user_id, extra={"typ": "access"})
    refresh_token = create_refresh_token(token.user_id, new_token_id, extra={"typ": "refresh"})
    new_model = RefreshToken(
        id=new_token_id,
        user_id=token.user_id,
        token_hash=hash_token(refresh_token),
        expires_at=datetime.now(UTC) + timedelta(days=settings.jwt.refresh_token_ttl_days),
        rotated_from_id=token.id,
    )
    session.add(new_model)
    return access_token, refresh_token, new_model


async def revoke_refresh_token(session: AsyncSession, token: RefreshToken) -> None:
    token.revoked = True
    token.revoked_at = datetime.now(UTC)
    await session.commit()


async def get_refresh_token(session: AsyncSession, token_hash_value: str) -> RefreshToken | None:
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash_value)
    result = await session.execute(stmt)
    token = result.scalar_one_or_none()
    if token and token.revoked:
        return None
    if token and token.expires_at < datetime.now(UTC):
        return None
    return token


async def clear_session(response, session: AsyncSession, refresh_token_hash: str | None) -> None:
    clear_auth_cookies(response)
    if refresh_token_hash:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == refresh_token_hash)
        result = await session.execute(stmt)
        token = result.scalar_one_or_none()
        if token:
            await revoke_refresh_token(session, token)
    await session.commit()


async def record_post_view(post_id: int, fingerprint: str, ttl_seconds: int = 3600) -> bool:
    redis = await get_redis()
    key = f"views:{post_id}:{fingerprint}"
    was_set = await redis.setnx(key, "1")
    if was_set:
        await redis.expire(key, ttl_seconds)
    return bool(was_set)
