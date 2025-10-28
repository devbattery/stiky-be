from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ensure_onboarded, get_current_user_optional, get_db_session
from app.core.security import get_client_fingerprint
from app.db.models.blog import Blog
from app.db.models.enums import PostCategory, PostStatus
from app.db.models.post import Post
from app.db.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.post import PostCreate, PostDetail, PostSummary, PostUpdate
from app.services import blogs as blog_service
from app.services import posts as post_service
from app.services.auth import record_post_view

router = APIRouter()


async def _get_blog_or_404(session: AsyncSession, slug: str) -> Blog:
    blog = await blog_service.get_blog_by_slug(session, slug)
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    return blog


async def _get_post_or_404(session: AsyncSession, blog: Blog, slug: str, include_unpublished: bool = False) -> Post:
    post = await post_service.get_post_by_slug(session, blog, slug, include_unpublished=include_unpublished)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@router.get("/{slug}/posts", response_model=PaginatedResponse[PostSummary])
async def list_posts_endpoint(
        slug: str,
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1, le=100),
        tag: str | None = Query(None),
        category: PostCategory | None = Query(None),
        status_filter: PostStatus | None = Query(None),
        session: AsyncSession = Depends(get_db_session),
        current_user: User | None = Depends(get_current_user_optional),
) -> PaginatedResponse[PostSummary]:
    blog = await _get_blog_or_404(session, slug)
    is_owner = current_user and current_user.id == blog.user_id
    effective_status = status_filter if is_owner else PostStatus.PUBLISHED
    normalized_tag = tag.lower() if tag else None
    posts, total = await post_service.list_posts(
        session,
        blog=blog,
        page=page,
        size=size,
        tag_slug=normalized_tag,
        category=category,
        status_filter=effective_status,
    )
    return PaginatedResponse[PostSummary](items=posts, total=total, page=page, size=size)


@router.get("/{slug}/posts/{post_slug}", response_model=PostDetail)
async def get_post_endpoint(
        slug: str,
        post_slug: str,
        request: Request,
        session: AsyncSession = Depends(get_db_session),
        current_user: User | None = Depends(get_current_user_optional),
) -> PostDetail:
    blog = await _get_blog_or_404(session, slug)
    include_unpublished = current_user is not None and current_user.id == blog.user_id
    post = await _get_post_or_404(session, blog, post_slug, include_unpublished=include_unpublished)

    fingerprint = current_user.id if current_user else get_client_fingerprint(request)
    if await record_post_view(post.id, fingerprint):
        post.view_count += 1
        await session.commit()
        await session.refresh(post)

    return post_service.serialize_post_detail(post)


@router.post("/{slug}/posts", response_model=PostDetail, status_code=status.HTTP_201_CREATED)
async def create_post_endpoint(
        slug: str,
        payload: PostCreate,
        user: User = Depends(ensure_onboarded),
        session: AsyncSession = Depends(get_db_session),
) -> PostDetail:
    blog = await _get_blog_or_404(session, slug)
    if blog.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the blog owner")
    post = await post_service.create_post(session, blog, payload)
    return post_service.serialize_post_detail(post)


@router.patch("/{slug}/posts/{post_slug}", response_model=PostDetail)
async def update_post_endpoint(
        slug: str,
        post_slug: str,
        payload: PostUpdate,
        user: User = Depends(ensure_onboarded),
        session: AsyncSession = Depends(get_db_session),
) -> PostDetail:
    blog = await _get_blog_or_404(session, slug)
    if blog.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the blog owner")
    post = await _get_post_or_404(session, blog, post_slug, include_unpublished=True)
    post = await post_service.update_post(session, blog, post, payload)
    return post_service.serialize_post_detail(post)


@router.delete("/{slug}/posts/{post_slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post_endpoint(
        slug: str,
        post_slug: str,
        user: User = Depends(ensure_onboarded),
        session: AsyncSession = Depends(get_db_session),
) -> Response:
    blog = await _get_blog_or_404(session, slug)
    if blog.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the blog owner")
    post = await _get_post_or_404(session, blog, post_slug, include_unpublished=True)
    await post_service.delete_post(session, post)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
