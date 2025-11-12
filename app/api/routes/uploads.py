from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user  # <--- get_current_user로 변경
from app.db.models.user import User
from app.services.uploads import generate_cloudinary_signature

router = APIRouter()


@router.post("/signature")
async def get_upload_signature(
        user: User = Depends(get_current_user),  # <--- 로그인만 되어 있으면 허용
) -> dict:
    signature = generate_cloudinary_signature()
    return signature
