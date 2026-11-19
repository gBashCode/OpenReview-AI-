"""Pull Request Service for tracking PR lifecycles and metadata."""

from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError
from app.pull_requests.models import PullRequest
from app.pull_requests.schemas import PullRequestCreate, PullRequestUpdate
from app.repositories.models import Repository


class PullRequestService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_repository(
        self,
        repository_id: str,
        state: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[PullRequest], int]:
        """Lists pull requests for a given repository."""
        stmt = select(PullRequest).where(PullRequest.repository_id == repository_id)
        if state:
            stmt = stmt.where(PullRequest.state == state)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(PullRequest.pr_number.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def list_by_organization(
        self,
        organization_id: str,
        state: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[PullRequest], int]:
        """Lists pull requests across all repositories of an organization."""
        stmt = (
            select(PullRequest)
            .join(Repository, PullRequest.repository_id == Repository.id)
            .where(Repository.organization_id == organization_id)
        )
        if state:
            stmt = stmt.where(PullRequest.state == state)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(PullRequest.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def get_by_id(self, pull_request_id: str) -> PullRequest:
        """Retrieves a pull request by UUID."""
        stmt = select(PullRequest).where(PullRequest.id == pull_request_id)
        pr = (await self.session.execute(stmt)).scalar_one_or_none()
        if not pr:
            raise NotFoundError("PullRequest", pull_request_id)
        return pr

    async def get_by_number(self, repository_id: str, pr_number: int) -> PullRequest:
        """Retrieves a pull request by repo and PR number."""
        stmt = select(PullRequest).where(
            PullRequest.repository_id == repository_id,
            PullRequest.pr_number == pr_number,
        )
        pr = (await self.session.execute(stmt)).scalar_one_or_none()
        if not pr:
            raise NotFoundError("PullRequest", f"{repository_id}#{pr_number}")
        return pr

    async def create(self, data: PullRequestCreate) -> PullRequest:
        """Registers a new pull request."""
        pr = PullRequest(
            repository_id=data.repository_id,
            pr_number=data.number,
            title=data.title,
            head_branch=data.source_branch,
            base_branch=data.target_branch,
            head_sha=data.head_sha,
            base_sha=data.base_sha,
            author_username=data.author_username or "unknown",
            state=data.state or "open",
        )
        self.session.add(pr)
        await self.session.commit()
        await self.session.refresh(pr)
        return pr

    async def update(self, pull_request_id: str, data: PullRequestUpdate) -> PullRequest:
        """Updates pull request metadata."""
        pr = await self.get_by_id(pull_request_id)
        if data.title is not None:
            pr.title = data.title
        if data.state is not None:
            pr.state = data.state
        if data.head_sha is not None:
            pr.head_sha = data.head_sha
        if data.base_sha is not None:
            pr.base_sha = data.base_sha

        await self.session.commit()
        await self.session.refresh(pr)
        return pr
