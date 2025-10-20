from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status

from app.utils.redis import get_redis


async def enforce_rate_limit(
        *,
        key: str,
        limit: int,
        window_seconds: int,
        error_detail: str = "Too many requests",
) -> None:
    redis = await get_redis()
    tx = redis.pipeline()
    tx.incr(key, 1)
    tx.expire(key, window_seconds)
    current, _ = await tx.execute()
    if current > limit:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=error_detail)


def rate_limit_window(seconds: int) -> datetime:
    return datetime.now(UTC) + timedelta(seconds=seconds)
