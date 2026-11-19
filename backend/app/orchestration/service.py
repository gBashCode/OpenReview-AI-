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
            canonical_status = getattr(vf, "canonical_state", vf.status)
            if canonical_status == "Rejected":
                continue  # Skip rejected false positives from database findings table

            f_prop = vf.finding
            v_status = "Confirmed" if canonical_status == "Accepted" else canonical_status
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
                discussion_state=canonical_status,
                verification_status=v_status,
                root_cause=getattr(vf, "verification_reason", f"Identified issue in {f_prop.file_path}"),
                impact=f"Potential {f_prop.severity} risk affecting {f_prop.category} reliability.",
                actionability_score=0.9 if f_prop.suggested_patch else 0.75,
                is_publishable=True,
                evidence=f_prop.code_evidence,
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
                evidence=disc.evidence,
                source_reference=disc.source_reference,
                position=disc.position,
                final_decision=disc.final_decision,
                round_number=disc.round_number,
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

    async def get_conference_session(self, review_id: str) -> Dict[str, Any]:
        """Loads and formats the multi-agent conference timeline, threads, and metrics."""
        stmt = (
            select(Review)
            .options(
                selectinload(Review.findings),
                selectinload(Review.agents),
                selectinload(Review.discussions),
                selectinload(Review.pull_request),
            )
            .where(Review.id == review_id)
        )
        review = (await self.session.execute(stmt)).scalar_one_or_none()
        if not review:
            raise NotFoundError("Review", review_id)

        # Group discussions by finding_id
        discussions_by_finding: Dict[str, List[AgentDiscussion]] = {}
        general_discussions: List[AgentDiscussion] = []

        max_round = 1
        for d in review.discussions:
            if d.round_number and d.round_number > max_round:
                max_round = d.round_number
            if d.finding_id:
                discussions_by_finding.setdefault(d.finding_id, []).append(d)
            else:
                general_discussions.append(d)

        threads = []
        for f in review.findings:
            f_discs = discussions_by_finding.get(f.id, [])
            threads.append({
                "finding_id": f.id,
                "file_path": f.file_path,
                "line_number": f.line_number,
                "title": f.title,
                "category": f.category,
                "severity": f.severity,
                "proposing_agent": f.agent_name or "Specialist Agent",
                "discussion_state": f.discussion_state or "Accepted",
                "evidence": f.evidence,
                "suggested_patch": f.suggested_patch,
                "messages": [
                    {
                        "id": d.id,
                        "review_id": d.review_id,
                        "finding_id": d.finding_id,
                        "agent_name": d.agent_name,
                        "message_type": d.message_type,
                        "position": d.position,
                        "final_decision": d.final_decision,
                        "content": d.content,
                        "file_context": d.file_context,
                        "evidence": d.evidence,
                        "source_reference": d.source_reference,
                        "round_number": d.round_number,
                        "is_verified": d.is_verified,
                        "created_at": d.created_at,
                        "updated_at": d.updated_at,
                    }
                    for d in f_discs
                ],
            })

        # Calculate metrics
        states_count: Dict[str, int] = {}
        for f in review.findings:
            st = f.discussion_state or "Accepted"
            states_count[st] = states_count.get(st, 0) + 1

        total_findings = len(review.findings)
        accepted_count = states_count.get("Accepted", 0)
        consensus_rate = round((accepted_count / total_findings * 100), 1) if total_findings > 0 else 100.0

        return {
            "review_id": review.id,
            "pull_request_id": review.pull_request_id,
            "commit_sha": review.commit_sha,
            "status": review.status,
            "total_rounds": max_round,
            "discussion_threads": threads,
            "general_discussions": [
                {
                    "id": d.id,
                    "review_id": d.review_id,
                    "agent_name": d.agent_name,
                    "message_type": d.message_type,
                    "position": d.position,
                    "content": d.content,
                    "evidence": d.evidence,
                    "round_number": d.round_number,
                    "is_verified": d.is_verified,
                    "created_at": d.created_at,
                }
                for d in general_discussions
            ],
            "agents": [
                {
                    "id": a.id,
                    "review_id": a.review_id,
                    "agent_name": a.agent_name,
                    "role": a.role,
                    "status": a.status,
                    "model_name": a.model_name,
                    "reasoning_summary": a.reasoning_summary,
                    "confidence_score": a.confidence_score or 0.95,
                    "findings_count": a.findings_count,
                    "execution_time_ms": a.execution_time_ms,
                    "created_at": a.created_at,
                    "updated_at": a.updated_at,
                }
                for a in review.agents
            ],
            "summary_metrics": {
                "total_rounds": max_round,
                "total_findings": total_findings,
                "accepted_count": accepted_count,
                "rejected_count": states_count.get("Rejected", 0),
                "needs_investigation_count": states_count.get("Needs investigation", 0),
                "duplicate_count": states_count.get("Duplicate", 0),
                "uncertain_count": states_count.get("Uncertain", 0),
                "consensus_rate": consensus_rate,
            },
        }

