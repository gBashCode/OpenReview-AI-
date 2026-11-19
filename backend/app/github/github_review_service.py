"""GitHub Review Comments, Pull Request Reviews, and Check Runs Service."""

from typing import Any, Dict, List, Literal, Optional
from app.core.exceptions import AppException, NotFoundError
from app.core.logging import get_logger
from app.github.github_auth_service import GitHubAuthService
from app.github.schemas import (
    GitHubCheckRunAnnotation,
    GitHubCheckRunCreate,
    GitHubCheckRunOutput,
    GitHubInlineComment,
    GitHubReviewCreate,
)

logger = get_logger("openreview.github.review")


class GitHubReviewService:
    def __init__(self, auth_service: Optional[GitHubAuthService] = None):
        self.auth_service = auth_service or GitHubAuthService()

    async def publish_inline_comment(
        self,
        installation_id: int,
        owner: str,
        repo: str,
        pull_number: int,
        commit_sha: str,
        file_path: str,
        line: int,
        body: str,
        side: Literal["LEFT", "RIGHT"] = "RIGHT",
    ) -> Dict[str, Any]:
        """Publishes an atomic inline review comment on a specific line of code."""
        client = await self.auth_service.get_authenticated_client(installation_id)
        try:
            payload = {
                "body": body,
                "commit_id": commit_sha,
                "path": file_path,
                "line": line,
                "side": side,
            }
            response = await client.post(
                f"/repos/{owner}/{repo}/pulls/{pull_number}/comments",
                json=payload,
            )
            if response.status_code not in (200, 201):
                logger.error(f"Failed to post inline comment [{response.status_code}]: {response.text}")
                raise AppException(
                    f"GitHub inline comment creation failed: {response.text}",
                    status_code=response.status_code,
                )
            return response.json()
        finally:
            await client.aclose()

    async def publish_pull_request_review(
        self,
        installation_id: int,
        owner: str,
        repo: str,
        pull_number: int,
        commit_sha: str,
        summary_body: str,
        event: Literal["COMMENT", "APPROVE", "REQUEST_CHANGES"] = "COMMENT",
        inline_comments: Optional[List[GitHubInlineComment]] = None,
    ) -> Dict[str, Any]:
        """Submits an executive review summary with optional batch inline comments."""
        client = await self.auth_service.get_authenticated_client(installation_id)
        try:
            payload: Dict[str, Any] = {
                "commit_id": commit_sha,
                "body": summary_body,
                "event": event,
            }
            if inline_comments:
                payload["comments"] = [
                    {
                        "path": c.path,
                        "line": c.line,
                        "side": c.side,
                        "body": c.body,
                    }
                    for c in inline_comments
                ]

            response = await client.post(
                f"/repos/{owner}/{repo}/pulls/{pull_number}/reviews",
                json=payload,
            )
            if response.status_code not in (200, 201):
                logger.error(f"Failed to publish PR review [{response.status_code}]: {response.text}")
                raise AppException(
                    f"GitHub PR review submission failed: {response.text}",
                    status_code=response.status_code,
                )
            return response.json()
        finally:
            await client.aclose()

    async def create_check_run(
        self,
        installation_id: int,
        owner: str,
        repo: str,
        check_run_in: GitHubCheckRunCreate,
    ) -> Dict[str, Any]:
        """Creates a GitHub Check Run representing the ongoing autonomous multi-agent analysis."""
        client = await self.auth_service.get_authenticated_client(installation_id)
        try:
            payload: Dict[str, Any] = {
                "name": check_run_in.name,
                "head_sha": check_run_in.head_sha,
                "status": check_run_in.status,
            }
            if check_run_in.conclusion:
                payload["conclusion"] = check_run_in.conclusion
            if check_run_in.output:
                payload["output"] = check_run_in.output.model_dump(exclude_none=True)

            response = await client.post(f"/repos/{owner}/{repo}/check-runs", json=payload)
            if response.status_code not in (200, 201):
                logger.error(f"Failed to create Check Run [{response.status_code}]: {response.text}")
                raise AppException(
                    f"GitHub Check Run creation failed: {response.text}",
                    status_code=response.status_code,
                )
            return response.json()
        finally:
            await client.aclose()

    async def update_check_run(
        self,
        installation_id: int,
        owner: str,
        repo: str,
        check_run_id: int,
        status: Literal["in_progress", "completed"] = "completed",
        conclusion: Optional[Literal["success", "failure", "neutral", "cancelled", "timed_out"]] = "success",
        output: Optional[GitHubCheckRunOutput] = None,
    ) -> Dict[str, Any]:
        """Updates or completes a GitHub Check Run with final score annotations."""
        client = await self.auth_service.get_authenticated_client(installation_id)
        try:
            payload: Dict[str, Any] = {
                "status": status,
            }
            if conclusion:
                payload["conclusion"] = conclusion
            if output:
                payload["output"] = output.model_dump(exclude_none=True)

            response = await client.patch(f"/repos/{owner}/{repo}/check-runs/{check_run_id}", json=payload)
            if response.status_code != 200:
                logger.error(f"Failed to update Check Run [{response.status_code}]: {response.text}")
                raise AppException(
                    f"GitHub Check Run update failed: {response.text}",
                    status_code=response.status_code,
                )
            return response.json()
        finally:
            await client.aclose()

    @staticmethod
    def format_review_summary_markdown(
        score: float,
        security_score: float,
        performance_score: float,
        quality_score: float,
        summary_text: str,
        findings_count: int,
        agent_names: List[str],
    ) -> str:
        """Formats a clean markdown executive review summary for GitHub PR reviews."""
        badge_color = "brightgreen" if score >= 90 else ("yellow" if score >= 75 else "red")
        score_badge = f"![Quality Score](https://img.shields.io/badge/OpenReview_Score-{score:.1f}%2F100-{badge_color})"

        agents_bullet = ", ".join([f"`{name}`" for name in agent_names])

        md = f"""## 🤖 OpenReview AI — Autonomous Code Review

{score_badge}

| Quality Dimension | Score | Status |
| :--- | :--- | :--- |
| 🛡️ **Security** | `{security_score:.1f}/100` | {'✅ Passed' if security_score >= 85 else '⚠️ Needs Attention'} |
| ⚡ **Performance** | `{performance_score:.1f}/100` | {'✅ Optimal' if performance_score >= 85 else '⚠️ Review Needed'} |
| 🧹 **Code Quality** | `{quality_score:.1f}/100` | {'✅ Clean' if quality_score >= 85 else '⚠️ Suggestions Found'} |

### Executive Summary
{summary_text}

---
*Reviewed by autonomous agents: {agents_bullet}*
*Total findings detected: `{findings_count}`*
"""
        return md
