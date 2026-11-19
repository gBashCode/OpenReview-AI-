"""GitHub Unified Diff and Changed File Inspection Service."""

import re
from typing import Any, Dict, List, Optional, Tuple
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.github.github_auth_service import GitHubAuthService
from app.github.schemas import GitHubChangedFile

logger = get_logger("openreview.github.diff")


class GitHubDiffService:
    def __init__(self, auth_service: Optional[GitHubAuthService] = None):
        self.auth_service = auth_service or GitHubAuthService()

    async def get_pull_request_files(
        self,
        installation_id: int,
        owner: str,
        repo: str,
        pull_number: int,
    ) -> List[GitHubChangedFile]:
        """Fetches all changed files in a pull request with additions, deletions, and patches."""
        client = await self.auth_service.get_authenticated_client(installation_id)
        try:
            response = await client.get(f"/repos/{owner}/{repo}/pulls/{pull_number}/files?per_page=100")
            if response.status_code != 200:
                logger.error(f"Failed to fetch PR files [{response.status_code}]: {response.text}")
                raise NotFoundError("PullRequestFiles", f"{owner}/{repo}#{pull_number}")

            items = response.json()
            return [
                GitHubChangedFile(
                    sha=item.get("sha", ""),
                    filename=item["filename"],
                    status=item.get("status", "modified"),
                    additions=item.get("additions", 0),
                    deletions=item.get("deletions", 0),
                    changes=item.get("changes", 0),
                    patch=item.get("patch"),
                    raw_url=item.get("raw_url"),
                )
                for item in items
            ]
        finally:
            await client.aclose()

    async def get_unified_diff(
        self,
        installation_id: int,
        owner: str,
        repo: str,
        pull_number: int,
    ) -> str:
        """Fetches complete raw unified diff for a pull request."""
        client = await self.auth_service.get_authenticated_client(installation_id)
        try:
            headers = {"Accept": "application/vnd.github.v3.diff"}
            response = await client.get(f"/repos/{owner}/{repo}/pulls/{pull_number}", headers=headers)
            if response.status_code != 200:
                raise NotFoundError("PullRequestDiff", f"{owner}/{repo}#{pull_number}")
            return response.text
        finally:
            await client.aclose()

    async def get_commit_details(
        self,
        installation_id: int,
        owner: str,
        repo: str,
        commit_sha: str,
    ) -> Dict[str, Any]:
        """Fetches details for a specific commit SHA."""
        client = await self.auth_service.get_authenticated_client(installation_id)
        try:
            response = await client.get(f"/repos/{owner}/{repo}/commits/{commit_sha}")
            if response.status_code != 200:
                raise NotFoundError("Commit", commit_sha)
            return response.json()
        finally:
            await client.aclose()

    async def compare_commits(
        self,
        installation_id: int,
        owner: str,
        repo: str,
        base_sha: str,
        head_sha: str,
    ) -> Dict[str, Any]:
        """Compares two commit SHAs and retrieves merge base and file diffs."""
        client = await self.auth_service.get_authenticated_client(installation_id)
        try:
            response = await client.get(f"/repos/{owner}/{repo}/compare/{base_sha}...{head_sha}")
            if response.status_code != 200:
                raise NotFoundError("CommitComparison", f"{base_sha}...{head_sha}")
            return response.json()
        finally:
            await client.aclose()

    @staticmethod
    def parse_patch_lines(patch: str) -> List[Tuple[int, int, str]]:
        """Parses a Git hunk patch string into a list of (diff_position, file_line_number, line_content).
        
        Essential for positioning inline GitHub review comments accurately.
        """
        lines = patch.split("\n")
        parsed = []
        current_right_line = 0
        diff_position = 0

        hunk_header_re = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")

        for line in lines:
            diff_position += 1
            match = hunk_header_re.match(line)
            if match:
                current_right_line = int(match.group(2))
                continue

            if line.startswith("+"):
                parsed.append((diff_position, current_right_line, line[1:]))
                current_right_line += 1
            elif line.startswith("-"):
                pass  # Deleted line from old revision
            else:
                # Context line present on both sides
                parsed.append((diff_position, current_right_line, line[1:] if len(line) > 1 else ""))
                current_right_line += 1

        return parsed
