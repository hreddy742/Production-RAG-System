from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "P4 Production RAG"
    app_env: str = "development"
    api_prefix: str = "/api"
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    postgres_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/p4_rag"
    )
    redis_url: str = "redis://localhost:6379/0"
    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chat_model: str = "llama3.1:8b"
    embedding_dimensions: int = 384
    retrieval_top_k: int = 4
    max_history_messages: int = 6
    cache_ttl_seconds: int = 900
    upload_dir: str = "data/uploads"
    temp_dir: str = "data/tmp"
    max_file_size_mb: int = 25

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[2]


@lru_cache
def get_settings() -> Settings:
    return Settings()
