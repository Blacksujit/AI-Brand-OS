from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import jwt
import pytest

from core.security import SecurityService


@pytest.fixture
def mock_settings() -> MagicMock:
    settings = MagicMock()
    settings.jwt_secret = "test-secret-that-is-at-least-32-characters!!"
    settings.jwt_algorithm = "HS256"
    settings.jwt_access_ttl_minutes = 15
    settings.jwt_refresh_ttl_days = 7
    return settings


@pytest.fixture
def service(mock_settings: MagicMock) -> SecurityService:
    return SecurityService(mock_settings)


class TestPasswordHashing:
    def test_hash_password_returns_string(self, service: SecurityService) -> None:
        result = service.hash_password("my-secret-password")
        assert isinstance(result, str)
        assert result.startswith("$2b$")

    def test_verify_password_correct(self, service: SecurityService) -> None:
        hashed = service.hash_password("correct-password")
        assert service.verify_password("correct-password", hashed) is True

    def test_verify_password_incorrect(self, service: SecurityService) -> None:
        hashed = service.hash_password("correct-password")
        assert service.verify_password("wrong-password", hashed) is False

    def test_hash_produces_different_hashes(self, service: SecurityService) -> None:
        h1 = service.hash_password("same-password")
        h2 = service.hash_password("same-password")
        assert h1 != h2

    def test_verify_empty_string(self, service: SecurityService) -> None:
        hashed = service.hash_password("")
        assert service.verify_password("", hashed) is True
        assert service.verify_password("x", hashed) is False


class TestAccessToken:
    def test_returns_string(self, service: SecurityService) -> None:
        user_id = uuid.uuid4()
        token = service.create_access_token(user_id)
        assert isinstance(token, str)
        assert token.count(".") == 2

    def test_contains_correct_claims(self, service: SecurityService) -> None:
        user_id = uuid.uuid4()
        token = service.create_access_token(user_id)
        payload = jwt.decode(
            token,
            service._secret,
            algorithms=[service._algorithm],
            audience="brandos-api",
        )
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"
        assert payload["aud"] == "brandos-api"

    def test_contains_sid_claim(self, service: SecurityService) -> None:
        user_id = uuid.uuid4()
        token = service.create_access_token(user_id)
        payload = jwt.decode(
            token,
            service._secret,
            algorithms=[service._algorithm],
            audience="brandos-api",
        )
        assert "sid" in payload
        assert uuid.UUID(payload["sid"])

    def test_custom_session_id(self, service: SecurityService) -> None:
        user_id = uuid.uuid4()
        session_id = uuid.uuid4()
        token = service.create_access_token(user_id, session_id=session_id)
        payload = jwt.decode(
            token,
            service._secret,
            algorithms=[service._algorithm],
            audience="brandos-api",
        )
        assert payload["sid"] == str(session_id)

    def test_has_iat_and_exp(self, service: SecurityService) -> None:
        user_id = uuid.uuid4()
        before = datetime.now(UTC)
        token = service.create_access_token(user_id)
        after = datetime.now(UTC)
        payload = jwt.decode(
            token,
            service._secret,
            algorithms=[service._algorithm],
            audience="brandos-api",
        )
        iat = datetime.fromtimestamp(payload["iat"], tz=UTC)
        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        ts_before = before.replace(microsecond=0)
        ts_after = (after + timedelta(seconds=1)).replace(microsecond=0)
        assert ts_before <= iat <= ts_after
        assert exp > iat

    def test_expires_after_ttl(self, service: SecurityService) -> None:
        user_id = uuid.uuid4()
        token = service.create_access_token(user_id)
        payload = jwt.decode(
            token,
            service._secret,
            algorithms=[service._algorithm],
            audience="brandos-api",
        )
        iat = datetime.fromtimestamp(payload["iat"], tz=UTC)
        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        expected_ttl = timedelta(minutes=15)
        tolerance = timedelta(seconds=2)
        assert abs((exp - iat) - expected_ttl) <= tolerance

    def test_different_user_ids(self, service: SecurityService) -> None:
        uid_a = uuid.uuid4()
        uid_b = uuid.uuid4()
        token_a = service.create_access_token(uid_a)
        token_b = service.create_access_token(uid_b)
        payload_a = jwt.decode(
            token_a,
            service._secret,
            algorithms=[service._algorithm],
            audience="brandos-api",
        )
        payload_b = jwt.decode(
            token_b,
            service._secret,
            algorithms=[service._algorithm],
            audience="brandos-api",
        )
        assert payload_a["sub"] == str(uid_a)
        assert payload_b["sub"] == str(uid_b)
        assert payload_a["sub"] != payload_b["sub"]

    def test_rejects_wrong_audience(self, service: SecurityService) -> None:
        user_id = uuid.uuid4()
        token = service.create_access_token(user_id)
        with pytest.raises(jwt.InvalidAudienceError):
            jwt.decode(
                token,
                service._secret,
                algorithms=[service._algorithm],
                audience="wrong-audience",
            )


class TestRefreshToken:
    def test_returns_string(self, service: SecurityService) -> None:
        user_id = uuid.uuid4()
        token = service.create_refresh_token(user_id)
        assert isinstance(token, str)
        assert token.count(".") == 2

    def test_contains_correct_claims(self, service: SecurityService) -> None:
        user_id = uuid.uuid4()
        token = service.create_refresh_token(user_id)
        payload = jwt.decode(
            token,
            service._secret,
            algorithms=[service._algorithm],
            audience="brandos-api",
        )
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"
        assert payload["aud"] == "brandos-api"

    def test_no_sid_claim(self, service: SecurityService) -> None:
        user_id = uuid.uuid4()
        token = service.create_refresh_token(user_id)
        payload = jwt.decode(
            token,
            service._secret,
            algorithms=[service._algorithm],
            audience="brandos-api",
        )
        assert "sid" not in payload

    def test_has_iat_and_exp(self, service: SecurityService) -> None:
        user_id = uuid.uuid4()
        token = service.create_refresh_token(user_id)
        payload = jwt.decode(
            token,
            service._secret,
            algorithms=[service._algorithm],
            audience="brandos-api",
        )
        assert "iat" in payload
        assert "exp" in payload
        assert payload["exp"] > payload["iat"]

    def test_expires_after_seven_days(self, service: SecurityService) -> None:
        user_id = uuid.uuid4()
        token = service.create_refresh_token(user_id)
        payload = jwt.decode(
            token,
            service._secret,
            algorithms=[service._algorithm],
            audience="brandos-api",
        )
        iat = datetime.fromtimestamp(payload["iat"], tz=UTC)
        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        expected_ttl = timedelta(days=7)
        tolerance = timedelta(seconds=2)
        assert abs((exp - iat) - expected_ttl) <= tolerance


class TestDecodeToken:
    def test_decode_access_token(self, service: SecurityService) -> None:
        user_id = uuid.uuid4()
        token = service.create_access_token(user_id)
        payload = service.decode_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"
        assert payload["aud"] == "brandos-api"

    def test_decode_refresh_token(self, service: SecurityService) -> None:
        user_id = uuid.uuid4()
        token = service.create_refresh_token(user_id)
        payload = service.decode_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"
        assert payload["aud"] == "brandos-api"

    def test_decode_raises_on_expired_token(self, service: SecurityService) -> None:
        user_id = uuid.uuid4()
        expired_token = jwt.encode(
            {
                "sub": str(user_id),
                "type": "access",
                "aud": "brandos-api",
                "iat": datetime.now(UTC) - timedelta(hours=2),
                "exp": datetime.now(UTC) - timedelta(hours=1),
            },
            service._secret,
            algorithm=service._algorithm,
        )
        with pytest.raises(jwt.ExpiredSignatureError):
            service.decode_token(expired_token)

    def test_decode_raises_on_bad_signature(self, service: SecurityService) -> None:
        user_id = uuid.uuid4()
        token = jwt.encode(
            {
                "sub": str(user_id),
                "type": "access",
                "aud": "brandos-api",
                "iat": datetime.now(UTC),
                "exp": datetime.now(UTC) + timedelta(minutes=15),
            },
            "different-secret",
            algorithm="HS256",
        )
        with pytest.raises(jwt.InvalidSignatureError):
            service.decode_token(token)

    def test_decode_raises_on_malformed_token(self, service: SecurityService) -> None:
        with pytest.raises(jwt.exceptions.DecodeError):
            service.decode_token("not-a-jwt-token")

    def test_decode_raises_on_wrong_audience(
        self, service: SecurityService
    ) -> None:
        user_id = uuid.uuid4()
        token = jwt.encode(
            {
                "sub": str(user_id),
                "type": "access",
                "aud": "other-api",
                "iat": datetime.now(UTC),
                "exp": datetime.now(UTC) + timedelta(minutes=15),
            },
            service._secret,
            algorithm=service._algorithm,
        )
        with pytest.raises(jwt.InvalidAudienceError):
            service.decode_token(token)


class TestVerifyToken:
    def test_returns_payload_for_valid_access_token(
        self, service: SecurityService
    ) -> None:
        user_id = uuid.uuid4()
        token = service.create_access_token(user_id)
        payload = service.verify_token(token)
        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"

    def test_returns_payload_for_valid_refresh_token(
        self, service: SecurityService
    ) -> None:
        user_id = uuid.uuid4()
        token = service.create_refresh_token(user_id)
        payload = service.verify_token(token)
        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"

    def test_returns_none_for_expired_token(
        self, service: SecurityService
    ) -> None:
        user_id = uuid.uuid4()
        expired_token = jwt.encode(
            {
                "sub": str(user_id),
                "type": "access",
                "aud": "brandos-api",
                "iat": datetime.now(UTC) - timedelta(hours=2),
                "exp": datetime.now(UTC) - timedelta(hours=1),
            },
            service._secret,
            algorithm=service._algorithm,
        )
        assert service.verify_token(expired_token) is None

    def test_returns_none_for_bad_signature(
        self, service: SecurityService
    ) -> None:
        user_id = uuid.uuid4()
        token = jwt.encode(
            {
                "sub": str(user_id),
                "type": "access",
                "aud": "brandos-api",
                "iat": datetime.now(UTC),
                "exp": datetime.now(UTC) + timedelta(minutes=15),
            },
            "different-secret",
            algorithm="HS256",
        )
        assert service.verify_token(token) is None

    def test_returns_none_for_malformed_token(
        self, service: SecurityService
    ) -> None:
        assert service.verify_token("not-a-jwt-token") is None

    def test_returns_none_for_wrong_audience(
        self, service: SecurityService
    ) -> None:
        user_id = uuid.uuid4()
        token = jwt.encode(
            {
                "sub": str(user_id),
                "type": "access",
                "aud": "other-api",
                "iat": datetime.now(UTC),
                "exp": datetime.now(UTC) + timedelta(minutes=15),
            },
            service._secret,
            algorithm=service._algorithm,
        )
        assert service.verify_token(token) is None

    def test_returns_none_for_empty_string(
        self, service: SecurityService
    ) -> None:
        assert service.verify_token("") is None

    def test_round_trip_access_token(self, service: SecurityService) -> None:
        user_id = uuid.uuid4()
        token = service.create_access_token(user_id)
        payload = service.verify_token(token)
        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"
        assert payload["aud"] == "brandos-api"

    def test_round_trip_refresh_token(self, service: SecurityService) -> None:
        user_id = uuid.uuid4()
        token = service.create_refresh_token(user_id)
        payload = service.verify_token(token)
        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"
        assert payload["aud"] == "brandos-api"
