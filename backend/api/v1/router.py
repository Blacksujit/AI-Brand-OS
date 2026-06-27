from fastapi import APIRouter

from api.v1 import auth, content, knowledge, profile, style, trends

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(profile.router)
router.include_router(knowledge.router)
router.include_router(style.router)
router.include_router(trends.router)
router.include_router(content.router)
