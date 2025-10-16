from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl


class UserPublic(BaseModel):
    id: str
    email: str
    nickname: str | None = None
    profile_image_url: HttpUrl | None = None
    onboarding_completed: bool

    model_config = {"from_attributes": True}


class OnboardingPayload(BaseModel):
    nickname: str = Field(..., min_length=2, max_length=20)
    blog_name: str = Field(..., min_length=2, max_length=60)
    blog_slug: str = Field(..., min_length=3, max_length=30)
    description: str | None = Field(None, max_length=500)
    profile_image_url: HttpUrl | None = None


class AvailabilityResponse(BaseModel):
    available: bool


class MeResponse(BaseModel):
    user: UserPublic
    blog: BlogPublic | None = None

    model_config = {"from_attributes": True}


class BlogPublic(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None = None

    model_config = {"from_attributes": True}


MeResponse.model_rebuild()
