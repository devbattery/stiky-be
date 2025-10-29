from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import ensure_onboarded
from app.db.models.user import User
from app.services.uploads import generate_cloudinary_signature

router = APIRouter()


@router.post("/signature")
async def get_upload_signature(
        user: User = Depends(ensure_onboarded),
) -> dict:
    signature = generate_cloudinary_signature()
    return signature
