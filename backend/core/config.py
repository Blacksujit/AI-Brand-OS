from __future__ import annotations

from pathlib import Path

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

    database_url: str = "sqlite+aiosqlite:///app/data/brandos.db"
    chromadb_host: str = "localhost"
    chromadb_port: int = 8001
    chromadb_path: str = "./data/chromadb"

    cors_origins: list[str] = ["http://localhost:3000"]

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

    max_daily_briefs: int = 100
    max_concurrent_pipelines: int = 10

    n8n_url: str = "http://n8n:5678"
    n8n_api_key: str = ""

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def is_development(self) -> bool:
        return self.env == "development"


def get_settings() -> Settings:
    return Settings()
