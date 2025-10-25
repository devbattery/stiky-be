from fastapi import APIRouter

from app.api.routes import auth, blogs, comments, health, likes, onboarding, posts, trending, uploads

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(onboarding.router, prefix="/me", tags=["me"])
api_router.include_router(blogs.router, prefix="/blogs", tags=["blogs"])
api_router.include_router(posts.router, prefix="/blogs", tags=["posts"])
api_router.include_router(comments.router, prefix="/posts", tags=["comments"])
api_router.include_router(likes.router, prefix="/posts", tags=["likes"])
api_router.include_router(trending.router, prefix="/trending", tags=["trending"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
