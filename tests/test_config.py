"""Tests for configuration parsing and validation."""

from app.core.config import Settings


def test_cors_origins_parsing():
    settings = Settings(
        ALLOWED_ORIGINS="http://localhost:3000, https://app.openreview.dev"
    )
    assert "http://localhost:3000" in settings.ALLOWED_ORIGINS
    assert "https://app.openreview.dev" in settings.ALLOWED_ORIGINS


def test_database_url_normalization():
    # Tests converting standard postgresql:// into asyncpg driver syntax
    settings = Settings(
        DATABASE_URL="postgresql://user:pass@localhost:5432/testdb"
    )
    assert settings.DATABASE_URL.startswith("postgresql+asyncpg://")


def test_environment_flags():
    dev_settings = Settings(APP_ENV="development")
    assert not dev_settings.is_production

    prod_settings = Settings(APP_ENV="production")
    assert prod_settings.is_production
