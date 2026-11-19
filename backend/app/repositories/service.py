"""Repository Service supporting organization-level data isolation."""

from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ConflictError, NotFoundError
from app.repositories.models import Repository
from app.repositories.schemas import RepositoryCreate, RepositoryUpdate


class RepositoryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_organization(
        self,
        organization_id: str,
        skip: int = 0,
        limit: int = 50,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[Repository], int]:
        """Lists repositories isolated to a specific organization with total count."""
        stmt = select(Repository).where(Repository.organization_id == organization_id)
        if is_active is not None:
            stmt = stmt.where(Repository.is_active == is_active)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(Repository.full_name).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def get_by_id(self, repository_id: str, organization_id: Optional[str] = None) -> Repository:
        """Retrieves a repository by ID, optionally verifying organization ownership."""
        stmt = select(Repository).where(Repository.id == repository_id)
        if organization_id:
            stmt = stmt.where(Repository.organization_id == organization_id)
        repo = (await self.session.execute(stmt)).scalar_one_or_none()
        if not repo:
            raise NotFoundError("Repository", repository_id)
        return repo

    async def create(self, data: RepositoryCreate) -> Repository:
        """Registers a new repository under an organization."""
        full_name = getattr(data, "full_name", None) or f"{data.owner}/{data.name}"
        github_repo_id = (
            getattr(data, "github_repo_id", None)
            or getattr(data, "github_id", None)
            or (100000 + int(abs(hash(full_name)) % 900000))
        )

        # Check uniqueness within the organization or globally by github_repo_id
        stmt_id = select(Repository).where(Repository.github_repo_id == github_repo_id)
        if (await self.session.execute(stmt_id)).scalar_one_or_none():
            raise ConflictError(f"GitHub repository ID {github_repo_id} is already registered.")

        stmt = select(Repository).where(
            Repository.organization_id == data.organization_id,
            Repository.full_name == full_name,
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ConflictError(f"Repository '{full_name}' is already connected to this organization.")

        repo = Repository(
            organization_id=data.organization_id,
            github_repo_id=github_repo_id,
            owner=data.owner,
            name=data.name,
            full_name=full_name,
            default_branch=data.default_branch or "main",
            description=data.description,
            is_active=data.is_active if data.is_active is not None else True,
            clone_url=data.clone_url or f"https://github.com/{full_name}.git",
        )
        self.session.add(repo)
        await self.session.commit()
        await self.session.refresh(repo)
        return repo

    async def update(
        self,
        repository_id: str,
        data: RepositoryUpdate,
        organization_id: Optional[str] = None,
    ) -> Repository:
        """Updates repository settings."""
        repo = await self.get_by_id(repository_id, organization_id)
        if data.default_branch is not None:
            repo.default_branch = data.default_branch
        if data.description is not None:
            repo.description = data.description
        if data.is_active is not None:
            repo.is_active = data.is_active

        await self.session.commit()
        await self.session.refresh(repo)
        return repo

    async def delete(self, repository_id: str, organization_id: Optional[str] = None) -> None:
        """Removes a repository."""
        repo = await self.get_by_id(repository_id, organization_id)
        await self.session.delete(repo)
        await self.session.commit()
