from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from core.config import Settings, get_settings
from core.logging import get_logger
from core.security import SecurityService
from database import Database, get_db
from models.user import User
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
    try:
        payload = security.decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        return uuid.UUID(payload["sub"])
    except (ValueError, KeyError, Exception) as e:
        logger.warning("token_decode_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from e


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
