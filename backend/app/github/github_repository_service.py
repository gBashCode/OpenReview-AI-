"""GitHub Repository Management and Permission Validation Service."""

from typing import List, Optional
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.core.logging import get_logger
from app.github.github_auth_service import GitHubAuthService
from app.github.schemas import GitHubRepositoryItem
from app.repositories.models import Repository

logger = get_logger("openreview.github.repositories")


class GitHubRepositoryService:
    def __init__(self, session: AsyncSession, auth_service: Optional[GitHubAuthService] = None):
        self.session = session
        self.auth_service = auth_service or GitHubAuthService()

    async def list_installation_repositories(self, installation_id: int) -> List[GitHubRepositoryItem]:
        """Fetches all repositories granted to the given installation from GitHub API."""
        client = await self.auth_service.get_authenticated_client(installation_id)
        try:
            response = await client.get("/installation/repositories?per_page=100")
            if response.status_code != 200:
                logger.error(f"Failed to list installation repos [{response.status_code}]: {response.text}")
                raise PermissionDeniedError(f"Could not retrieve installation repositories: {response.text}")

            data = response.json()
            repos = data.get("repositories", [])
            return [
                GitHubRepositoryItem(
                    id=r["id"],
                    name=r["name"],
                    full_name=r["full_name"],
                    private=r.get("private", False),
                    description=r.get("description"),
                    default_branch=r.get("default_branch", "main"),
                    clone_url=r.get("clone_url"),
                    html_url=r.get("html_url"),
                    permissions=r.get("permissions"),
                )
                for r in repos
            ]
        finally:
            await client.aclose()

    async def validate_repository_permissions(self, installation_id: int, owner: str, repo: str) -> bool:
        """Validates that the installation possesses read & write access to repository pull requests."""
        client = await self.auth_service.get_authenticated_client(installation_id)
        try:
            response = await client.get(f"/repos/{owner}/{repo}")
            if response.status_code == 404:
                return False
            if response.status_code != 200:
                return False

            repo_data = response.json()
            perms = repo_data.get("permissions", {})
            # We require pull (read) and push or admin to write review comments
            has_read = perms.get("pull", True)
            has_write = perms.get("push", False) or perms.get("admin", False) or perms.get("maintain", False)
            return bool(has_read and has_write)
        finally:
            await client.aclose()

    async def sync_installation_repositories(
        self,
        organization_id: str,
        installation_id: int,
        installation_db_id: Optional[str] = None,
    ) -> List[Repository]:
        """Synchronizes repositories granted to this installation into the local database."""
        gh_repos = await self.list_installation_repositories(installation_id)
        synced: List[Repository] = []

        for gh_repo in gh_repos:
            stmt = select(Repository).where(
                (Repository.github_repo_id == gh_repo.id)
                | (Repository.full_name == gh_repo.full_name)
            )
            existing = (await self.session.execute(stmt)).scalar_one_or_none()

            owner, name = gh_repo.full_name.split("/", 1)
            if existing:
                existing.organization_id = organization_id
                existing.installation_id = installation_db_id or existing.installation_id
                existing.default_branch = gh_repo.default_branch
                existing.description = gh_repo.description
                existing.clone_url = gh_repo.clone_url
                existing.is_active = True
                synced.append(existing)
            else:
                new_repo = Repository(
                    organization_id=organization_id,
                    installation_id=installation_db_id,
                    github_repo_id=gh_repo.id,
                    owner=owner,
                    name=name,
                    full_name=gh_repo.full_name,
                    default_branch=gh_repo.default_branch,
                    description=gh_repo.description,
                    clone_url=gh_repo.clone_url,
                    is_active=True,
                )
                self.session.add(new_repo)
                synced.append(new_repo)

        await self.session.commit()
        return synced

    async def sync_user_oauth_repositories(
        self,
        organization_id: str,
        user_access_token: str,
    ) -> List[Repository]:
        """Synchronizes repositories accessible by the user's personal OAuth token."""
        headers = {
            "Authorization": f"Bearer {user_access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "OpenReviewAI-App/1.0",
        }
        synced: List[Repository] = []
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://api.github.com/user/repos?per_page=100&sort=updated&affiliation=owner,collaborator,organization_member",
                headers=headers,
            )
            if resp.status_code != 200:
                logger.error(f"Failed to fetch user repositories from GitHub [{resp.status_code}]: {resp.text}")
                raise PermissionDeniedError(f"Could not retrieve user repositories: {resp.text}")

            repos_data = resp.json()
            for r in repos_data:
                try:
                    async with self.session.begin_nested():
                        full_name = r.get("full_name")
                        if not full_name:
                            continue
                        owner, name = full_name.split("/", 1)
                        gh_id = r.get("id")

                        stmt = select(Repository).where(
                            (Repository.organization_id == organization_id)
                            & (
                                (Repository.github_repo_id == gh_id)
                                | (Repository.full_name == full_name)
                            )
                        )
                        existing = (await self.session.execute(stmt)).scalar_one_or_none()
                        if existing:
                            existing.github_repo_id = gh_id
                            existing.default_branch = r.get("default_branch", "main")
                            existing.description = r.get("description")
                            existing.clone_url = r.get("clone_url")
                            existing.is_active = True
                            synced.append(existing)
                            repo_id = existing.id
                        else:
                            new_repo = Repository(
                                organization_id=organization_id,
                                github_repo_id=gh_id,
                                owner=owner,
                                name=name,
                                full_name=full_name,
                                default_branch=r.get("default_branch", "main"),
                                description=r.get("description"),
                                clone_url=r.get("clone_url"),
                                is_active=True,
                            )
                            self.session.add(new_repo)
                            await self.session.flush()
                            synced.append(new_repo)
                            repo_id = new_repo.id

                        try:
                            pr_resp = await client.get(
                                f"https://api.github.com/repos/{owner}/{name}/pulls?state=all&per_page=10",
                                headers=headers,
                            )
                            if pr_resp.status_code == 200:
                                from app.pull_requests.models import PullRequest
                                for pr_item in pr_resp.json():
                                    pr_num = pr_item.get("number")
                                    if not pr_num:
                                        continue
                                    stmt_pr = select(PullRequest).where(
                                        (PullRequest.repository_id == repo_id)
                                        & (PullRequest.pr_number == pr_num)
                                    )
                                    existing_pr = (await self.session.execute(stmt_pr)).scalar_one_or_none()
                                    if not existing_pr:
                                        new_pr = PullRequest(
                                            repository_id=repo_id,
                                            github_pr_id=pr_item.get("id"),
                                            pr_number=pr_num,
                                            title=pr_item.get("title") or f"PR #{pr_num}",
                                            description=pr_item.get("body"),
                                            state=pr_item.get("state", "open"),
                                            head_branch=pr_item.get("head", {}).get("ref", "branch"),
                                            base_branch=pr_item.get("base", {}).get("ref", "main"),
                                            head_sha=pr_item.get("head", {}).get("sha", "0" * 40),
                                            base_sha=pr_item.get("base", {}).get("sha", "0" * 40),
                                            author_username=pr_item.get("user", {}).get("login", "unknown") if pr_item.get("user") else "unknown",
                                        )
                                        self.session.add(new_pr)
                        except Exception as pr_err:
                            logger.warning(f"Failed to fetch PRs for {full_name}: {pr_err}")
                except Exception as repo_err:
                    logger.warning(f"Failed to sync repository {r.get('full_name')}: {repo_err}")

        await self.session.commit()
        return synced
