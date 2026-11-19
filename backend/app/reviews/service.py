"""Autonomous Multi-Agent Review Service."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.agents.models import AgentDiscussion, ReviewAgent
from app.core.exceptions import NotFoundError
from app.findings.models import Finding
from app.pull_requests.models import PullRequest
from app.reviews.models import Review
from app.reviews.schemas import ReviewCreate


class ReviewService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_reviews(
        self,
        pull_request_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Review], int]:
        """Lists reviews with optional filtering and pagination."""
        stmt = select(Review)
        if pull_request_id:
            stmt = stmt.where(Review.pull_request_id == pull_request_id)
        if status:
            stmt = stmt.where(Review.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(Review.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def get_by_id(self, review_id: str) -> Review:
        """Retrieves a review by UUID with findings, agents, and discussions loaded."""
        stmt = (
            select(Review)
            .options(
                selectinload(Review.pull_request),
                selectinload(Review.findings).selectinload(Finding.patches),
                selectinload(Review.agents),
                selectinload(Review.discussions),
            )
            .execution_options(populate_existing=True)
            .where(Review.id == review_id)
        )
        review = (await self.session.execute(stmt)).scalar_one_or_none()
        if not review:
            raise NotFoundError("Review", review_id)
        return review

    async def trigger_review(self, data: ReviewCreate) -> Review:
        """Initiates an autonomous multi-agent review session."""
        stmt_pr = select(PullRequest).where(PullRequest.id == data.pull_request_id)
        pr = (await self.session.execute(stmt_pr)).scalar_one_or_none()
        if not pr:
            raise NotFoundError("PullRequest", data.pull_request_id)

        commit_sha = data.commit_sha or pr.head_sha

        review = Review(
            pull_request_id=pr.id,
            commit_sha=commit_sha,
            status="analyzing",
            summary="Autonomous review initiated. Agents are inspecting changed files.",
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(review)
        await self.session.flush()

        # Instantiate the 5 specialized AI review agents
        agents_data = [
            ("Security Sentinel", "security_analysis", "claude-3-5-sonnet", 0.96),
            ("Performance Guardian", "performance_profiling", "gpt-4o", 0.92),
            ("Bug Hunter", "code_quality", "gpt-4o", 0.94),
            ("Architecture Specialist", "architecture_review", "gemini-1.5-pro", 0.89),
            ("Verification Arbiter", "verification", "claude-3-5-sonnet", 0.98),
        ]
        for name, role, model, conf in agents_data:
            agent = ReviewAgent(
                review_id=review.id,
                agent_name=name,
                role=role,
                status="running",
                model_name=model,
                confidence_score=conf,
            )
            self.session.add(agent)

        await self.session.commit()
        return await self.get_by_id(review.id)
