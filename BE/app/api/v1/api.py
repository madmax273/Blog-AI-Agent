from fastapi import APIRouter

router = APIRouter()

from . import blog, auth

router.include_router(blog.router, prefix="/blog", tags=["blog"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
