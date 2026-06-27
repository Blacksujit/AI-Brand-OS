from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from core.chroma import ChromaService
from core.config import Settings, get_settings
from core.embedding import EmbeddingService
from core.logging import get_logger
from core.security import SecurityService
from database import Database, get_db
from models.user import User
from repositories.content import AgentRunRepository, GeneratedPostRepository
from services.auth import AuthService
from services.history import HistoryService
from services.knowledge import KnowledgeBaseService
from services.style import StyleService
from services.trend import TrendService

security_scheme = HTTPBearer()
logger = get_logger(__name__)


async def get_db_session(
    settings: Settings = Depends(get_settings),
) -> AsyncGenerator[Database, None]:
    db = get_db(settings)
    try:
        yield db
    finally:
        await db.close()


async def get_security_service(
    settings: Settings = Depends(get_settings),
) -> SecurityService:
    return SecurityService(settings)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    security: SecurityService = Depends(get_security_service),
) -> uuid.UUID:
    payload = security.verify_token(credentials.credentials)
    if payload is None:
        logger.warning("token_decode_failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    try:
        return uuid.UUID(payload["sub"])
    except (ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )


async def get_style_service(
    db: Database = Depends(get_db_session),
) -> StyleService:
    return StyleService(db=db)


async def get_trend_service(
    db: Database = Depends(get_db_session),
) -> TrendService:
    return TrendService(db=db)


async def require_onboarded(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Database = Depends(get_db_session),
) -> uuid.UUID:
    async with db.session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None or not user.is_onboarded:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has not completed onboarding",
            )
    return user_id


async def get_knowledge_service(
    db: Database = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> KnowledgeBaseService:
    chroma = ChromaService(settings)
    embedding = EmbeddingService(settings)
    await chroma.initialize()
    return KnowledgeBaseService(db=db, chroma=chroma, embedding=embedding)


async def get_auth_service(
    db: Database = Depends(get_db_session),
    security: SecurityService = Depends(get_security_service),
) -> AuthService:
    return AuthService(db=db, security=security)


async def get_history_service(
    db: Database = Depends(get_db_session),
) -> HistoryService:
    return HistoryService(db=db)
