"""Pull Request Analyzer Service."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analyzer.pr_analysis_engine import PRAnalysisEngine
from app.analyzer.schemas import PRAnalysisResult
from app.core.exceptions import NotFoundError
from app.github.github_auth_service import GitHubAuthService
from app.github.github_diff_service import GitHubDiffService
from app.pull_requests.models import PullRequest
from app.repositories.models import Repository


class AnalyzerService:
    """Provides high-level PR impact analysis, diff ingestion, and risk scoring."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.engine = PRAnalysisEngine(session)
        self.diff_service = GitHubDiffService(GitHubAuthService())

    async def analyze_pull_request(
        self,
        pull_request_id: str,
        custom_diff: Optional[str] = None,
    ) -> PRAnalysisResult:
        """Loads pull request and repository details and runs full impact analysis."""
        pr_stmt = select(PullRequest).where(PullRequest.id == pull_request_id)
        pr = (await self.session.execute(pr_stmt)).scalar_one_or_none()
        if not pr:
            raise NotFoundError("PullRequest", pull_request_id)

        repo_stmt = select(Repository).where(Repository.id == pr.repository_id)
        repo = (await self.session.execute(repo_stmt)).scalar_one_or_none()

        raw_diff = custom_diff or ""
        # If no custom diff passed and repo has github installation, fetch live unified diff
        if not raw_diff and repo and repo.installation_id:
            try:
                raw_diff = await self.diff_service.get_unified_diff(
                    installation_id=int(repo.installation_id),
                    owner=repo.owner,
                    repo=repo.name,
                    pull_number=pr.pr_number,
                )
            except Exception:
                pass

        return await self.engine.analyze_pull_request(
            raw_diff=raw_diff,
            pr_number=pr.pr_number,
            title=pr.title,
            description=pr.description or "",
            repository_id=pr.repository_id,
        )

    async def analyze_raw_diff(
        self,
        raw_diff: str,
        title: str = "Ad-hoc Pull Request",
        description: str = "",
        repository_id: Optional[str] = None,
    ) -> PRAnalysisResult:
        """Analyzes an ad-hoc unified diff string with optional repository context."""
        return await self.engine.analyze_pull_request(
            raw_diff=raw_diff,
            pr_number=1,
            title=title,
            description=description,
            repository_id=repository_id,
        )
