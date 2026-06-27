from __future__ import annotations

from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BRANDOS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "development"
    debug: bool = True
    log_level: str = "DEBUG"
    log_json: bool = False

    database_url: str = "sqlite+aiosqlite:///app/data/brandos.db"
    database_pool_size: int = Field(default=5, ge=1, le=100)
    database_max_overflow: int = Field(default=10, ge=0, le=100)
    database_pool_timeout: int = Field(default=30, ge=1, le=300)
    database_pool_recycle: int = Field(default=1800, ge=60, le=86400)

    chromadb_host: str = "localhost"
    chromadb_port: int = 8001
    chromadb_path: str = "./data/chromadb"
    chromadb_collection_kb: str = "kb_embeddings"
    chromadb_collection_content: str = "content_embeddings"
    chromadb_collection_style: str = "style_vectors"

    cors_origins: list[str] = ["http://localhost:3000"]
    cors_allow_credentials: bool = True

    rate_limit_enabled: bool = True
    rate_limit_default: str = "100/minute"
    rate_limit_auth: str = "20/minute"
    rate_limit_content_generate: str = "10/minute"

    max_request_body_size: int = 1_048_576

    jwt_secret: str = "dev-secret-change-in-production-min-32-chars!!"
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 7

    gemini_api_key: str = ""

    default_llm_model: str = "gemini-2.0-flash"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_device: str = "cpu"

    knowledge_dir: Path = Path("./knowledge")
    data_dir: Path = Path("./data")

    max_daily_briefs: int = Field(default=100, ge=1, le=10000)
    max_concurrent_pipelines: int = Field(default=10, ge=1, le=100)

    langchain_api_key: str = ""
    langchain_project: str = "brandos-content-pipeline"

    n8n_url: str = "http://n8n:5678"
    n8n_api_key: str = ""

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def is_development(self) -> bool:
        return self.env == "development"

    @model_validator(mode="after")
    def validate_settings(self) -> Settings:
        if self.is_production:
            if self.gemini_api_key == "" or self.gemini_api_key == "dev-key":
                msg = "GEMINI_API_KEY must be set in production"
                raise ValueError(msg)

            if self.jwt_secret in (
                "dev-secret-change-in-production-min-32-chars!!",
                "",
            ):
                msg = "JWT_SECRET must be changed in production"
                raise ValueError(msg)

            if self.database_url.startswith("sqlite"):
                msg = (
                    "SQLite cannot be used in production; "
                    "set BRANDOS_DATABASE_URL to a PostgreSQL URL"
                )
                raise ValueError(msg)

            self.log_json = True

        return self

    @property
    def is_async_sqlite(self) -> bool:
        return "sqlite" in self.database_url and "aiosqlite" in self.database_url

    @property
    def is_postgres(self) -> bool:
        return "postgresql" in self.database_url or "postgres" in self.database_url


def get_settings() -> Settings:
    return Settings()
