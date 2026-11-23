"""GitHub Pull Request Event Ingestion and Lifecycle Service."""

from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.analyzer.workload_classifier import workload_classifier
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.github.github_auth_service import GitHubAuthService
from app.github.models import GitHubInstallation
from app.organizations.models import Organization
from app.pull_requests.models import PullRequest
from app.repositories.models import Repository
from app.reviews.models import Review
from app.reviews.schemas import ReviewCreate
from app.reviews.service import ReviewService

logger = get_logger("openreview.github.pr")


class GitHubPullRequestService:
    def __init__(
        self,
        session: AsyncSession,
        auth_service: Optional[GitHubAuthService] = None,
        review_service: Optional[ReviewService] = None,
    ):
        self.session = session
        self.auth_service = auth_service or GitHubAuthService()
        self.review_service = review_service or ReviewService(session)

    async def get_pull_request_metadata(
        self,
        installation_id: int,
        owner: str,
        repo: str,
        pull_number: int,
    ) -> Dict[str, Any]:
        """Fetches complete pull request metadata from GitHub REST API."""
        client = await self.auth_service.get_authenticated_client(installation_id)
        try:
            response = await client.get(f"/repos/{owner}/{repo}/pulls/{pull_number}")
            if response.status_code != 200:
                raise NotFoundError("PullRequest", f"{owner}/{repo}#{pull_number}")
            return response.json()
        finally:
            await client.aclose()

    async def handle_pull_request_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Processes GitHub `pull_request` webhook events (opened, synchronize, reopened, closed)."""
        action = payload.get("action")
        pr_data = payload.get("pull_request", {})
        repo_data = payload.get("repository", {})
        installation_data = payload.get("installation", {})

        if not pr_data or not repo_data:
            return {"status": "ignored", "reason": "Missing pull_request or repository payload"}

        pr_number = pr_data.get("number")
        repo_github_id = repo_data.get("id")
        repo_full_name = repo_data.get("full_name")
        owner_login = repo_data.get("owner", {}).get("login")
        repo_name = repo_data.get("name")
        head_sha = pr_data.get("head", {}).get("sha")
        base_sha = pr_data.get("base", {}).get("sha")
        head_branch = pr_data.get("head", {}).get("ref")
        base_branch = pr_data.get("base", {}).get("ref")
        author = pr_data.get("user", {}).get("login", "unknown")
        title = pr_data.get("title", f"PR #{pr_number}")
        description = pr_data.get("body")
        is_merged = pr_data.get("merged", False)

        # 1. Look up repository or automatically link with installation organization
        stmt_repo = select(Repository).where(
            (Repository.github_repo_id == repo_github_id)
            | (Repository.full_name == repo_full_name)
        )
        repo = (await self.session.execute(stmt_repo)).scalar_one_or_none()

        if not repo:
            # Resolve organization from installation
            inst_id_num = installation_data.get("id")
            org_id = None
            inst_db_id = None
            if inst_id_num:
                stmt_inst = select(GitHubInstallation).where(GitHubInstallation.installation_id == inst_id_num)
                inst = (await self.session.execute(stmt_inst)).scalar_one_or_none()
                if inst:
                    org_id = inst.organization_id
                    inst_db_id = inst.id

            if not org_id:
                stmt_org = select(Organization).order_by(Organization.created_at)
                org = (await self.session.execute(stmt_org)).scalars().first()
                org_id = org.id if org else "default-org"

            repo = Repository(
                organization_id=org_id,
                installation_id=inst_db_id,
                github_repo_id=repo_github_id,
                owner=owner_login,
                name=repo_name,
                full_name=repo_full_name,
                default_branch=repo_data.get("default_branch", "main"),
                clone_url=repo_data.get("clone_url"),
                is_active=True,
            )
            self.session.add(repo)
            await self.session.flush()

        # 2. Look up or create PullRequest
        stmt_pr = select(PullRequest).where(
            PullRequest.repository_id == repo.id,
            PullRequest.pr_number == pr_number,
        )
        pr = (await self.session.execute(stmt_pr)).scalar_one_or_none()

        if not pr:
            pr = PullRequest(
                repository_id=repo.id,
                github_pr_id=pr_data.get("id"),
                pr_number=pr_number,
                title=title,
                description=description,
                head_branch=head_branch,
                base_branch=base_branch,
                head_sha=head_sha,
                base_sha=base_sha,
                author_username=author,
                state="open",
            )
            self.session.add(pr)
            await self.session.flush()
        else:
            pr.title = title
            pr.head_sha = head_sha
            pr.base_sha = base_sha
            pr.head_branch = head_branch
            pr.base_branch = base_branch
            if action in ("opened", "reopened", "synchronize"):
                pr.state = "open"
            elif action == "closed":
                pr.state = "merged" if is_merged else "closed"

        await self.session.commit()

        # 3. Actions that trigger an automated multi-agent code review
        if action in ("opened", "synchronize", "reopened"):
            # AutoScaleX: Classify workload before dispatching to review fleet
            workload = workload_classifier.classify(
                changed_files_count=pr_data.get("changed_files", 1),
                additions=pr_data.get("additions", 0),
                deletions=pr_data.get("deletions", 0),
            )
            logger.info(
                f"AutoScaleX classified PR #{pr_number} on {repo_full_name}: "
                f"tier=[{workload.tier.value.upper()}] score={workload.complexity_score} "
                f"est_tokens={workload.estimated_tokens} scaling_weight={workload.scaling_weight}"
            )

            logger.info(f"Queuing autonomous code review for PR #{pr_number} [{action}] on {repo_full_name} via queue [{workload.tier.value}]")
            review = await self.review_service.trigger_review(
                ReviewCreate(
                    pull_request_id=pr.id,
                    commit_sha=head_sha,
                )
            )

            # AutoScaleX: Dispatch review task to Celery priority queue or in-process fallback
            from app.tasks.review_tasks import dispatch_review_task
            dispatch_info = dispatch_review_task(
                review_id=review.id,
                tier=workload.tier.value,
            )

            return {
                "status": "review_triggered",
                "action": action,
                "pull_request_id": pr.id,
                "review_id": review.id,
                "head_sha": head_sha,
                "dispatch": dispatch_info,
                "workload": {
                    "tier": workload.tier.value,
                    "complexity_score": workload.complexity_score,
                    "estimated_tokens": workload.estimated_tokens,
                    "recommended_agent_count": workload.recommended_agent_count,
                    "scaling_weight": workload.scaling_weight,
                    "timeout_seconds": workload.timeout_seconds,
                },
            }

        elif action == "closed":
            return {
                "status": "closed",
                "action": action,
                "pull_request_id": pr.id,
                "merged": is_merged,
            }

        return {"status": "unhandled_action", "action": action}
