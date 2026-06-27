from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select

from api.deps import (
    get_db_session,
    get_security_service,
)
from core.logging import get_logger
from core.security import SecurityService
from database import Database
from models.user import Session, User
from schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    body: RegisterRequest,
    request: Request,
    db: Database = Depends(get_db_session),
    security: SecurityService = Depends(get_security_service),
) -> TokenResponse:
    async with db.session() as session:
        result = await session.execute(select(User).where(User.email == body.email))
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = User(
            email=body.email,
            password_hash=security.hash_password(body.password),
            display_name=body.display_name,
            is_onboarded=False,
        )
        session.add(user)
        await session.flush()

        session_record = Session(
            user_id=user.id,
            refresh_token_hash=security.hash_password(str(uuid.uuid4())),
            expires_at=datetime.now(UTC).replace(day=datetime.now(UTC).day + 7),
            user_agent=request.headers.get("user-agent"),
        )
        session.add(session_record)

    access_token = security.create_access_token(user.id)
    refresh_token = security.create_refresh_token(user.id)

    logger.info("user_registered", user_id=str(user.id))
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: Database = Depends(get_db_session),
    security: SecurityService = Depends(get_security_service),
) -> TokenResponse:
    async with db.session() as session:
        result = await session.execute(select(User).where(User.email == body.email))
        user = result.scalar_one_or_none()
        if user is None or not security.verify_password(body.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )

        user.last_login_at = datetime.now(UTC)

        session_record = Session(
            user_id=user.id,
            refresh_token_hash=security.hash_password(str(uuid.uuid4())),
            expires_at=datetime.now(UTC).replace(day=datetime.now(UTC).day + 7),
            user_agent=request.headers.get("user-agent"),
        )
        session.add(session_record)

    access_token = security.create_access_token(user.id)
    refresh_token = security.create_refresh_token(user.id)

    logger.info("user_logged_in", user_id=str(user.id))
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
    security: SecurityService = Depends(get_security_service),
) -> TokenResponse:
    try:
        payload = security.decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        user_id = uuid.UUID(payload["sub"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from e

    new_access = security.create_access_token(user_id)
    new_refresh = security.create_refresh_token(user_id)

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
    )


@router.post("/logout", status_code=204)
async def logout(
    body: RefreshRequest,
    db: Database = Depends(get_db_session),
    security: SecurityService = Depends(get_security_service),
) -> None:
    try:
        payload = security.decode_token(body.refresh_token)
        user_id = uuid.UUID(payload["sub"])

        async with db.session() as session:
            sessions = await session.execute(
                select(Session).where(
                    Session.user_id == user_id,
                    not Session.is_revoked,
                )
            )
            for sess in sessions.scalars().all():
                sess.is_revoked = True

        logger.info("user_logged_out", user_id=str(user_id))
    except Exception as e:
        logger.warning("logout_failed", error=str(e))
