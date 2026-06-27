from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt
from passlib.context import CryptContext

from core.config import Settings


class SecurityService:
    def __init__(self, settings: Settings) -> None:
        self._secret = settings.jwt_secret
        self._algorithm = settings.jwt_algorithm
        self._access_ttl = timedelta(minutes=settings.jwt_access_ttl_minutes)
        self._refresh_ttl = timedelta(days=settings.jwt_refresh_ttl_days)
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        return self._pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return self._pwd_context.verify(plain, hashed)

    def create_access_token(self, user_id: uuid.UUID, session_id: uuid.UUID | None = None) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "sid": str(session_id or uuid.uuid4()),
            "type": "access",
            "iat": now,
            "exp": now + self._access_ttl,
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def create_refresh_token(self, user_id: uuid.UUID) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "iat": now,
            "exp": now + self._refresh_ttl,
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode_token(self, token: str) -> dict:
        return jwt.decode(token, self._secret, algorithms=[self._algorithm])
