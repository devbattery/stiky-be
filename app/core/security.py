import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, Optional

import jwt
from fastapi import Request

from app.core.config import settings


def _current_time() -> datetime:
    return datetime.now(UTC)


def create_access_token(subject: str, extra: Optional[Dict[str, Any]] = None) -> str:
    now = _current_time()
    issuer = str(settings.backend_base_url) if settings.backend_base_url else "stiky-api"
    payload: Dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt.access_token_ttl_minutes)).timestamp()),
        "iss": issuer,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt.secret_key, algorithm=settings.jwt.algorithm)


def create_refresh_token(subject: str, token_id: str, extra: Optional[Dict[str, Any]] = None) -> str:
    now = _current_time()
    issuer = str(settings.backend_base_url) if settings.backend_base_url else "stiky-api"
    payload: Dict[str, Any] = {
        "sub": subject,
        "jti": token_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=settings.jwt.refresh_token_ttl_days)).timestamp()),
        "iss": issuer,
        "typ": "refresh",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt.secret_key, algorithm=settings.jwt.algorithm)


def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, settings.jwt.secret_key, algorithms=[settings.jwt.algorithm])


def hash_token(value: str) -> str:
    digest = hashlib.sha256()
    digest.update(value.encode("utf-8"))
    return digest.hexdigest()


def generate_otp_code(length: int = 6) -> str:
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(length))


def hash_otp_code(code: str, email: str) -> str:
    secret = settings.jwt.secret_key.encode("utf-8")
    message = f"{email}:{code}".encode("utf-8")
    digest = hmac.new(secret, message, hashlib.sha256).hexdigest()
    return digest


def get_client_fingerprint(request: Request) -> str:
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    key = f"{ip_address}:{user_agent}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def generate_slug(base: str, suffix: Optional[int] = None) -> str:
    slug = base.lower().strip()
    slug = slug.replace(" ", "-")
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789-"
    slug = "".join(char for char in slug if char in allowed)
    if not slug:
        slug = secrets.token_hex(4)
    if suffix is not None:
        slug = f"{slug}-{suffix}"
    return slug
