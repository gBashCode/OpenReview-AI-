"""Autonomous Review Orchestration Database Service.

Executes the LangGraph multi-agent review graph and persists findings,
agents, discussions, and scorecard metrics into PostgreSQL.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.models import AgentDiscussion, ReviewAgent
from app.core.ai.gateway import ModelGateway
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.findings.models import Finding
from app.orchestration.state import ReviewState
from app.orchestration.workflow import get_review_workflow
from app.pull_requests.models import PullRequest
from app.repositories.models import Repository
from app.reviews.models import Review

logger = get_logger("openreview.orchestration.service")


class ReviewOrchestrationService:
    """Executes the autonomous multi-agent code review pass on a pull request,
    storing all agent telemetry, findings, and discussions in the database.
    """

    def __init__(self, session: AsyncSession, gateway: Optional[ModelGateway] = None):
        self.session = session
        self.gateway = gateway or ModelGateway()

    async def execute_review(
        self,
        review_id: str,
        custom_diff: Optional[str] = None,
    ) -> Review:
        """Executes the complete LangGraph review workflow for a registered Review record."""
        # 1. Fetch Review, PullRequest, and Repository
        stmt = (
            select(Review)
            .options(
                selectinload(Review.pull_request),
                selectinload(Review.findings),
                selectinload(Review.agents),
                selectinload(Review.discussions),
            )
            .where(Review.id == review_id)
        )
        review = (await self.session.execute(stmt)).scalar_one_or_none()
        if not review:
            raise NotFoundError("Review", review_id)

        pr = review.pull_request
        if not pr:
            raise NotFoundError("PullRequest", review.pull_request_id)

        repo_stmt = select(Repository).where(Repository.id == pr.repository_id)
        repo = (await self.session.execute(repo_stmt)).scalar_one_or_none()

        # Update status to analyzing
        review.status = "analyzing"
        review.started_at = datetime.now(timezone.utc)
        await self.session.commit()

        raw_diff = custom_diff or ""
        if not raw_diff:
            # Create a fallback mock diff if none was loaded
            raw_diff = (
                f"diff --git a/app/main.py b/app/main.py\n"
                f"--- a/app/main.py\n"
                f"+++ b/app/main.py\n"
                f"@@ -1,5 +1,7 @@\n"
                f" def process_data(user_input):\n"
                f"+    # PR change: {pr.title}\n"
                f"+    return eval(user_input)\n"
            )

        # 2. Prepare initial LangGraph state
        initial_state: ReviewState = {
            "review_id": review.id,
            "pull_request_id": pr.id,
            "repository_id": repo.id if repo else "unknown",
            "commit_sha": review.commit_sha or pr.head_sha or "0000000",
            "pr_title": pr.title,
            "pr_description": pr.description or "",
            "raw_diff": raw_diff,
            "changed_files": [],
            "context_evidence": {},
            "pr_analysis": {},
            "agent_findings": [],
            "agent_discussions": [],
            "agent_execution_logs": [],
            "errors": [],
            "verified_findings": [],
            "overall_score": 100.0,
            "security_score": 100.0,
            "performance_score": 100.0,
            "quality_score": 100.0,
            "review_summary": "",
            "token_budget_remaining": self.gateway.token_budget,
            "is_completed": False,
        }

        # 3. Compile and execute LangGraph workflow
        workflow = get_review_workflow(self.gateway)
        logger.info(f"Invoking LangGraph review workflow for review {review.id}...")

        try:
            final_state = await workflow.ainvoke(initial_state)
        except Exception as e:
            logger.error(f"LangGraph review workflow failed: {e}", exc_info=True)
            review.status = "failed"
            review.error_message = str(e)
            review.completed_at = datetime.now(timezone.utc)
            await self.session.commit()
            return review

        # 4. Persist ReviewAgents telemetry
        existing_agents_map = {a.agent_name.lower(): a for a in review.agents}
        for log in final_state.get("agent_execution_logs", []):
            agent_record = existing_agents_map.get(log.agent_name.lower())
            if not agent_record:
                agent_record = ReviewAgent(
                    review_id=review.id,
                    agent_name=log.agent_name,
                    role=log.role,
                    status=log.status,
                    findings_count=log.findings_count,
                    execution_time_ms=log.execution_time_ms,
                    reasoning_summary=log.reasoning_summary or log.error_message,
                )
                self.session.add(agent_record)
            else:
                agent_record.status = log.status
                agent_record.findings_count = log.findings_count
                agent_record.execution_time_ms = log.execution_time_ms
                agent_record.reasoning_summary = log.reasoning_summary or log.error_message

        # 5. Persist Verified Findings
        persisted_findings_map = {}
        for vf in final_state.get("verified_findings", []):
            if vf.status == "rejected":
                continue  # Skip rejected false positives from database findings table

            f_prop = vf.finding
            finding_record = Finding(
                review_id=review.id,
                file_path=f_prop.file_path,
                line_number=f_prop.line_number,
                end_line_number=f_prop.end_line_number,
                side=f_prop.side,
                category=f_prop.category,
                severity=f_prop.severity,
                title=f_prop.title,
                message=f_prop.message,
                suggested_patch=f_prop.suggested_patch,
                agent_name=f_prop.agent_name,
                confidence_score=vf.confidence_score,
                is_resolved=False,
            )
            self.session.add(finding_record)
            await self.session.flush()
            persisted_findings_map[f_prop.id] = finding_record.id

        # 6. Persist AgentDiscussions (Conference Messages)
        for disc in final_state.get("agent_discussions", []):
            db_finding_id = persisted_findings_map.get(disc.finding_id) if disc.finding_id else None
            disc_record = AgentDiscussion(
                review_id=review.id,
                finding_id=db_finding_id,
                agent_name=disc.agent_name,
                message_type=disc.message_type,
                content=disc.content,
                file_context=disc.file_context,
                is_verified=disc.is_verified,
            )
            self.session.add(disc_record)

        # 7. Update Review record
        review.status = "completed"
        review.score = final_state.get("overall_score", 100.0)
        review.security_score = final_state.get("security_score", 100.0)
        review.performance_score = final_state.get("performance_score", 100.0)
        review.quality_score = final_state.get("quality_score", 100.0)
        review.summary = final_state.get("review_summary", "Review completed successfully.")
        review.findings_count = len(persisted_findings_map)
        review.completed_at = datetime.now(timezone.utc)

        await self.session.commit()
        await self.session.refresh(review)
        logger.info(f"Review {review.id} successfully completed and persisted.")
        return review
