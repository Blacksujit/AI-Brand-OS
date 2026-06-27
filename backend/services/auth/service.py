from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy import select

from core.logging import get_logger
from core.security import SecurityService
from database import Database
from models.user import Session, User

logger = get_logger(__name__)


class AuthService:
    def __init__(self, db: Database, security: SecurityService) -> None:
        self._db = db
        self._security = security

    async def register(
        self,
        email: str,
        password: str,
        display_name: str,
        user_agent: str | None = None,
    ) -> tuple[str, str]:
        async with self._db.session() as session:
            result = await session.execute(select(User).where(User.email == email))
            if result.scalar_one_or_none() is not None:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered",
                )

            user = User(
                email=email,
                password_hash=self._security.hash_password(password),
                display_name=display_name,
                is_onboarded=False,
            )
            session.add(user)
            await session.flush()

            session_record = Session(
                user_id=user.id,
                refresh_token_hash=self._security.hash_password(str(uuid.uuid4())),
                expires_at=datetime.now(UTC) + timedelta(days=7),
                user_agent=user_agent,
            )
            session.add(session_record)

        access_token = self._security.create_access_token(user.id)
        refresh_token = self._security.create_refresh_token(user.id)

        logger.info("user_registered", user_id=str(user.id))
        return access_token, refresh_token

    async def login(
        self,
        email: str,
        password: str,
        user_agent: str | None = None,
    ) -> tuple[str, str]:
        async with self._db.session() as session:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if user is None or not self._security.verify_password(password, user.password_hash):
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                )

            if not user.is_active:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is deactivated",
                )

            user.last_login_at = datetime.now(UTC)

            session_record = Session(
                user_id=user.id,
                refresh_token_hash=self._security.hash_password(str(uuid.uuid4())),
                expires_at=datetime.now(UTC) + timedelta(days=7),
                user_agent=user_agent,
            )
            session.add(session_record)

        access_token = self._security.create_access_token(user.id)
        refresh_token = self._security.create_refresh_token(user.id)

        logger.info("user_logged_in", user_id=str(user.id))
        return access_token, refresh_token

    async def refresh_tokens(self, refresh_token: str) -> tuple[str, str]:
        payload = self._security.verify_token(refresh_token)
        if payload is None:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )
        if payload.get("type") != "refresh":
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        user_id = uuid.UUID(payload["sub"])
        new_access = self._security.create_access_token(user_id)
        new_refresh = self._security.create_refresh_token(user_id)
        return new_access, new_refresh

    async def logout(self, refresh_token: str) -> None:
        from sqlalchemy import select as sa_select

        try:
            payload = self._security.verify_token(refresh_token)
            if payload is None:
                return
            user_id = uuid.UUID(payload["sub"])
            async with self._db.session() as session:
                sessions = await session.execute(
                    sa_select(Session).where(
                        Session.user_id == user_id,
                        Session.is_revoked.is_(False),
                    )
                )
                for sess in sessions.scalars().all():
                    sess.is_revoked = True
            logger.info("user_logged_out", user_id=str(user_id))
        except Exception as exc:
            logger.warning("logout_failed", error=str(exc))
