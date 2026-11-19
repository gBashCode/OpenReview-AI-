"""Repository Data Access Object."""

from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.repository import Repository
from app.repositories.base import BaseRepository


class RepositoryRepo(BaseRepository[Repository]):
    """Data access layer for Repository entities."""

    def __init__(self, session: AsyncSession):
        super().__init__(Repository, session)

    async def get_by_github_id(self, github_repo_id: int) -> Optional[Repository]:
        result = await self.session.execute(
            select(Repository).where(Repository.github_repo_id == github_repo_id)
        )
        return result.scalar_one_or_none()

    async def get_by_full_name(self, full_name: str) -> Optional[Repository]:
        result = await self.session.execute(
            select(Repository).where(Repository.full_name == full_name)
        )
        return result.scalar_one_or_none()

    async def list_active(self, skip: int = 0, limit: int = 50) -> Sequence[Repository]:
        result = await self.session.execute(
            select(Repository)
            .where(Repository.is_active == True)
            .order_by(Repository.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
