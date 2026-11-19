"""Repository Business Logic Service."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ConflictError, NotFoundError
from app.models.repository import Repository
from app.repositories.repository_repo import RepositoryRepo
from app.schemas.repository import RepositoryCreate, RepositoryUpdate


class RepositoryService:
    """Orchestrates repository ingestion and settings."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = RepositoryRepo(session)

    async def get_repository(self, repository_id: str) -> Repository:
        repository = await self.repo.get_by_id(repository_id)
        if not repository:
            raise NotFoundError("Repository", repository_id)
        return repository

    async def list_repositories(self, skip: int = 0, limit: int = 50) -> List[Repository]:
        return list(await self.repo.list_active(skip=skip, limit=limit))

    async def register_repository(self, data: RepositoryCreate) -> Repository:
        full_name = f"{data.owner}/{data.name}"
        existing = await self.repo.get_by_full_name(full_name)
        if existing:
            raise ConflictError(f"Repository '{full_name}' is already registered.")

        repo_obj = Repository(
            github_repo_id=data.github_repo_id,
            owner=data.owner,
            name=data.name,
            full_name=full_name,
            default_branch=data.default_branch,
            description=data.description,
            is_active=data.is_active,
            clone_url=data.clone_url or f"https://github.com/{full_name}.git",
        )
        return await self.repo.create(repo_obj)

    async def update_repository(
        self, repository_id: str, data: RepositoryUpdate
    ) -> Repository:
        repository = await self.get_repository(repository_id)
        if data.default_branch is not None:
            repository.default_branch = data.default_branch
        if data.description is not None:
            repository.description = data.description
        if data.is_active is not None:
            repository.is_active = data.is_active

        await self.session.commit()
        await self.session.refresh(repository)
        return repository

    async def delete_repository(self, repository_id: str) -> None:
        repository = await self.get_repository(repository_id)
        await self.repo.delete(repository)
