"""Pytest configuration and shared async test fixtures."""

import os
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import create_application

# Use an in-memory SQLite database for isolated unit/integration tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_settings = Settings(
    APP_ENV="test",
    DEBUG=True,
    DATABASE_URL=TEST_DB_URL,
    REDIS_URL="redis://localhost:6379/15",
    SECRET_KEY="test-secret-key",
)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncSession:
    SessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with SessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def async_client(test_engine, db_session) -> AsyncClient:
    app = create_application()

    # Override get_db dependency to point to the test session
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = lambda: test_settings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
