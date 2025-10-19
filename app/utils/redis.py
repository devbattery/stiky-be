from __future__ import annotations

import asyncio
import redis.asyncio as redis

from app.core.config import settings

_redis_pool: redis.Redis | None = None
_pool_lock = asyncio.Lock()


async def get_redis() -> redis.Redis:
    global _redis_pool
    if _redis_pool is None:
        async with _pool_lock:
            if _redis_pool is None:
                _redis_pool = redis.from_url(settings.redis.url, decode_responses=True)
                if settings.redis.use_ssl:
                    _redis_pool = redis.from_url(
                        settings.redis.url,
                        decode_responses=True,
                        ssl=True,
                        ssl_cert_reqs="none",
                    )
    return _redis_pool


async def close_redis() -> None:
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.close()
        _redis_pool = None
