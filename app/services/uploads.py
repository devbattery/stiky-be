from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from app.core.config import settings


def generate_cloudinary_signature(
        *,
        public_id: str | None = None,
        folder: str | None = None,
        eager: str | None = None,
        timestamp: int | None = None,
        invalidate: bool | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "timestamp": timestamp or int(datetime.now(UTC).timestamp()),
        "api_key": settings.cloudinary.api_key,
    }
    if public_id:
        params["public_id"] = public_id
    if folder or settings.cloudinary.upload_folder:
        params["folder"] = folder or settings.cloudinary.upload_folder
    if eager:
        params["eager"] = eager
    if invalidate is not None:
        params["invalidate"] = str(invalidate).lower()

    signature_payload = "&".join(
        f"{key}={value}" for key, value in sorted(params.items()) if key != "api_key"
    )
    to_sign = f"{signature_payload}{settings.cloudinary.api_secret}"
    signature = hashlib.sha1(to_sign.encode("utf-8")).hexdigest()
    params["signature"] = signature
    params["cloud_name"] = settings.cloudinary.cloud_name
    return params
