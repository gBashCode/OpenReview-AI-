"""FastAPI Dependency Injection providers."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.services.health_service import HealthService
from app.services.repository_service import RepositoryService
from app.services.review_service import ReviewService


def get_health_service(session: AsyncSession = Depends(get_db)) -> HealthService:
    """Provides HealthService instance injected with active db session."""
    return HealthService(session)


def get_repository_service(session: AsyncSession = Depends(get_db)) -> RepositoryService:
    """Provides RepositoryService instance injected with active db session."""
    return RepositoryService(session)


def get_review_service(session: AsyncSession = Depends(get_db)) -> ReviewService:
    """Provides ReviewService instance injected with active db session."""
    return ReviewService(session)
