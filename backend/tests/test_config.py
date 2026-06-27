from __future__ import annotations

import os

from core.config import Settings, get_settings


class TestSettings:
    def test_default_env_is_development(self) -> None:
        s = get_settings()
        assert s.env == "test"

    def test_is_async_sqlite_true(self) -> None:
        s = Settings(database_url="sqlite+aiosqlite:///test.db")
        assert s.is_async_sqlite is True

    def test_is_async_sqlite_false_for_postgres(self) -> None:
        s = Settings(database_url="postgresql+asyncpg://user:pass@localhost/db")
        assert s.is_async_sqlite is False

    def test_is_postgres_true(self) -> None:
        s = Settings(database_url="postgresql+asyncpg://user:pass@localhost/db")
        assert s.is_postgres is True

    def test_is_postgres_false_for_sqlite(self) -> None:
        s = Settings(database_url="sqlite+aiosqlite:///test.db")
        assert s.is_postgres is False

    def test_validation_passes_for_test(self) -> None:
        s = Settings(
            env="test",
            database_url="sqlite+aiosqlite://",
            gemini_api_key="test-key",
            jwt_secret="test-secret-that-is-long-enough-for-hs256",
        )
        assert s.is_development is False
        assert s.is_production is False

    def test_production_requires_postgres(self) -> None:
        import pytest

        with pytest.raises(ValueError, match="SQLite cannot be used in production"):
            Settings(
                env="production",
                database_url="sqlite+aiosqlite:///test.db",
                gemini_api_key="real-key",
                jwt_secret="real-secret-that-is-long-enough-for-hs256",
            )

    def test_production_requires_gemini_key(self) -> None:
        import pytest

        with pytest.raises(ValueError, match="GEMINI_API_KEY must be set in production"):
            Settings(
                env="production",
                database_url="postgresql+asyncpg://user:pass@localhost/db",
                gemini_api_key="",
                jwt_secret="real-secret-that-is-long-enough-for-hs256",
            )

    def test_production_requires_jwt_secret(self) -> None:
        import pytest

        with pytest.raises(ValueError, match="JWT_SECRET must be changed in production"):
            Settings(
                env="production",
                database_url="postgresql+asyncpg://user:pass@localhost/db",
                gemini_api_key="real-key",
                jwt_secret="dev-secret-change-in-production-min-32-chars!!",
            )

    def test_production_enables_json_logging(self) -> None:
        s = Settings(
            env="production",
            database_url="postgresql+asyncpg://user:pass@localhost/db",
            gemini_api_key="real-key",
            jwt_secret="real-secret-that-is-long-enough-for-hs256",
        )
        assert s.log_json is True

    def test_pool_settings_defaults(self) -> None:
        s = Settings()
        assert s.database_pool_size == 5
        assert s.database_max_overflow == 10
        assert s.database_pool_timeout == 30
        assert s.database_pool_recycle == 1800

    def test_max_daily_briefs_capped(self) -> None:
        s = Settings(max_daily_briefs=500)
        assert s.max_daily_briefs == 500

    def test_env_prefix(self) -> None:
        os.environ["BRANDOS_ENV"] = "staging"
        os.environ["BRANDOS_DEBUG"] = "false"
        s = get_settings()
        assert s.env == "staging"
        assert s.debug is False
