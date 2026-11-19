"""GitHub Repository Management and Permission Validation Service."""

from typing import List, Optional
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
