from __future__ import annotations

import re

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.blog import Blog
from app.db.models.user import User
from app.schemas.user import BlogPublic, MeResponse, OnboardingPayload, UserPublic
from app.utils.slug import normalize_slug, is_valid_slug


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def is_nickname_available(session: AsyncSession, nickname: str) -> bool:
    stmt = select(exists().where(User.nickname == nickname))
    result = await session.execute(stmt)
    return not result.scalar()


async def is_blog_slug_available(session: AsyncSession, slug: str) -> bool:
    normalized = normalize_slug(slug)
    if not is_valid_slug(normalized):
        return False
    stmt = select(exists().where(Blog.slug == normalized))
    result = await session.execute(stmt)
    return not result.scalar()


async def complete_onboarding(
        session: AsyncSession,
        user: User,
        payload: OnboardingPayload,
) -> User:
    await session.refresh(user, attribute_names=["blog"])
    nickname_pattern = re.compile(r"^[A-Za-z0-9가-힣_]{2,20}$")
    if not nickname_pattern.fullmatch(payload.nickname):
        raise ValueError("Invalid nickname format")
    nickname_exists = False
    if payload.nickname != user.nickname:
        stmt_nick = select(exists().where(User.nickname == payload.nickname))
        result = await session.execute(stmt_nick)
        nickname_exists = result.scalar()
    if nickname_exists:
        raise ValueError("Nickname already taken")

    user.nickname = payload.nickname
    user.profile_image_url = (
        str(payload.profile_image_url) if payload.profile_image_url is not None else None
    )
    user.onboarding_completed = True

    blog_slug = normalize_slug(payload.blog_slug)
    if not is_valid_slug(blog_slug):
        raise ValueError("Invalid blog slug")

    slug_taken = False
    if not user.blog or user.blog.slug != blog_slug:
        stmt_slug = select(exists().where(Blog.slug == blog_slug))
        result = await session.execute(stmt_slug)
        slug_taken = result.scalar()
    if slug_taken:
        raise ValueError("Blog slug already taken")

    blog = user.blog
    if blog is None:
        blog = Blog(
            user_id=user.id,
            name=payload.blog_name,
            slug=blog_slug,
            description=payload.description,
        )
        session.add(blog)
    else:
        blog.name = payload.blog_name
        blog.slug = blog_slug
        blog.description = payload.description
    await session.commit()
    await session.refresh(user)
    await session.refresh(user, attribute_names=["blog"])
    return user


async def serialize_me(user: User) -> MeResponse:
    blog_obj = user.__dict__.get("blog")
    blog = BlogPublic.model_validate(blog_obj) if blog_obj is not None else None
    return MeResponse(user=UserPublic.model_validate(user), blog=blog)
