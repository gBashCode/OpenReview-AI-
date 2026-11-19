"""Application configuration and environment settings management.

Utilizes Pydantic Settings (v2) for strongly typed, validated settings with caching.
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Literal, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root path (where .env is located)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    """Central configuration for OpenReview AI backend services."""

    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env", Path(".env")),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "OpenReview AI"
    APP_ENV: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "openreview-development-secret-key-change-in-production"
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000

    # CORS
    ALLOWED_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "openreview"
    POSTGRES_USER: str = "openreview_admin"
    POSTGRES_PASSWORD: str = "openreview_secure_password"
    DATABASE_URL: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> str:
        if v and isinstance(v, str) and len(v.strip()) > 0:
            # Normalize postgres url for asyncpg if needed
            cleaned = v.strip()
            if cleaned.startswith("postgres://"):
                cleaned = cleaned.replace("postgres://", "postgresql+asyncpg://", 1)
            elif cleaned.startswith("postgresql://") and not cleaned.startswith("postgresql+asyncpg://"):
                cleaned = cleaned.replace("postgresql://", "postgresql+asyncpg://", 1)
            if "sslmode=" in cleaned:
                cleaned = cleaned.replace("sslmode=", "ssl=")
            return cleaned

        # Fallback assemble from components
        data = info.data
        user = data.get("POSTGRES_USER", "openreview_admin")
        pwd = data.get("POSTGRES_PASSWORD", "openreview_secure_password")
        server = data.get("POSTGRES_SERVER", "localhost")
        port = data.get("POSTGRES_PORT", 5432)
        db = data.get("POSTGRES_DB", "openreview")
        return f"postgresql+asyncpg://{user}:{pwd}@{server}:{port}/{db}"

    # Database connection pool settings
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_PRE_PING: bool = True
    DB_ECHO: bool = False

    # Observability & Metrics
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: Optional[str] = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.2
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = None
    PROMETHEUS_METRICS_ENABLED: bool = True

    # Redis & Background Queues
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # GitHub App
    GITHUB_APP_ID: Optional[str] = None
    GITHUB_APP_SLUG: str = "openreview-ai"
    GITHUB_APP_PRIVATE_KEY: Optional[str] = None
    GITHUB_APP_PRIVATE_KEY_PATH: Optional[str] = None
    GITHUB_WEBHOOK_SECRET: Optional[str] = None
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GITHUB_TOKEN: Optional[str] = None

    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None

    def get_github_private_key(self) -> Optional[str]:
        """Resolves GitHub App private key from environment variable or file path."""
        if self.GITHUB_APP_PRIVATE_KEY and len(self.GITHUB_APP_PRIVATE_KEY.strip()) > 0:
            key = self.GITHUB_APP_PRIVATE_KEY.strip()
            # If formatted with literal '\n' characters in single-line env var
            if "\\n" in key and "\n" not in key:
                key = key.replace("\\n", "\n")
            return key
        if self.GITHUB_APP_PRIVATE_KEY_PATH:
            p = Path(self.GITHUB_APP_PRIVATE_KEY_PATH)
            if not p.is_absolute():
                p = BASE_DIR / p
            if p.is_file():
                return p.read_text(encoding="utf-8")
        return None

    # AI / LLM Integration
    DEFAULT_LLM_PROVIDER: Literal["openai", "anthropic", "gemini", "groq", "ollama", "mock"] = "openai"
    DEFAULT_MODEL: str = "gpt-4o-mini"
    DEFAULT_EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536

    LLM_MAX_CONTEXT_LENGTH: int = 128000
    LLM_TEMPERATURE: float = 0.2
    LLM_TIMEOUT_SECONDS: float = 60.0
    LLM_RETRY_COUNT: int = 3
    LLM_TOKEN_BUDGET: int = 200000
    LLM_FALLBACK_PROVIDER: Optional[str] = "gemini"
    LLM_FALLBACK_MODEL: Optional[str] = "gemini-2.5-flash"

    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: Literal["json", "console"] = "console"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_sqlite(self) -> bool:
        return bool(self.DATABASE_URL and "sqlite" in self.DATABASE_URL)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached accessor for application settings to prevent redundant filesystem reads."""
    return Settings()


# Default singleton instance
settings = get_settings()
