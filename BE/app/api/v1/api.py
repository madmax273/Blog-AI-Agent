from fastapi import APIRouter

router = APIRouter()

from . import blog

router.include_router(blog.router, prefix="/blog", tags=["blog"])