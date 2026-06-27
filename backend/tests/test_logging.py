from __future__ import annotations

from core.config import Settings
from core.logging import JsonSink, configure_logging


class TestConfigureLogging:
    def test_development_format(self) -> None:
        s = Settings(
            env="development",
            log_level="DEBUG",
            log_json=False,
        )
        configure_logging(s)

    def test_production_json_format(self) -> None:
        s = Settings(
            env="production",
            log_level="INFO",
            log_json=True,
            database_url="postgresql+asyncpg://user:pass@localhost/db",
            gemini_api_key="real-key",
            jwt_secret="real-secret-that-is-long-enough-for-hs256",
        )
        configure_logging(s)


class TestJsonSink:
    def test_json_sink_accepts_record(self) -> None:
        sink = JsonSink()
        from loguru import logger as _base_logger

        _base_logger.add(sink, level="INFO")
        _base_logger.info("hello json")
