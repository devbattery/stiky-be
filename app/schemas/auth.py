from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserPublic


class OTPRequest(BaseModel):
    email: EmailStr


class OTPVerify(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=4, max_length=10)


class AuthResponse(BaseModel):
    user: UserPublic
    onboarding_required: bool
