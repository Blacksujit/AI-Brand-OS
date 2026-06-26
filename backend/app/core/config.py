from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BRANDOS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    env: str = "development"
    debug: bool = True
    log_level: str = "DEBUG"

    database_url: str = "sqlite+aiosqlite:///app/data/brandos.db"
    redis_url: str = "redis://localhost:6379/0"
    chromadb_path: str = "./data/chromadb"

    storage_endpoint: str = "http://localhost:9000"
    storage_access_key: str = "brandos"
    storage_secret_key: str = "brandossecret"
    storage_bucket: str = "brandos"
    storage_region: str = "us-east-1"

    jwt_secret: str = "dev-secret-change-in-production-min-32-chars!!"
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 7

    encryption_key: str = "dev-encryption-key-32-bytes-long!!"

    cors_origins: list[str] = ["http://localhost:3000"]

    anthropic_api_key: str = ""
    openai_api_key: str = ""

    default_llm_model: str = "claude-sonnet-4-20250514"
    writing_llm_model: str = "claude-opus-4-20250514"
    fast_llm_model: str = "claude-haiku-3-5-20241022"
    embedding_model: str = "text-embedding-3-small"

    max_daily_briefs: int = 100
    max_concurrent_pipelines: int = 10
    circuit_breaker_failures: int = 3
    circuit_breaker_seconds: int = 1800

    data_dir: Path = Path("./data")

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def is_development(self) -> bool:
        return self.env == "development"


def get_settings() -> Settings:
    return Settings()
