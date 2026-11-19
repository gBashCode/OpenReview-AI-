"""Code Review Service orchestrating reviews and AI findings."""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError
from app.models.review import Review
from app.models.review_comment import ReviewComment
from app.repositories.review_repo import ReviewCommentRepo, ReviewRepo
from app.schemas.review import ReviewCommentCreate, ReviewCreate


class ReviewService:
    """Manages review lifecycle, findings aggregation, and status updates."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.review_repo = ReviewRepo(session)
        self.comment_repo = ReviewCommentRepo(session)

    async def get_review(self, review_id: str) -> Review:
        review = await self.review_repo.get_with_comments(review_id)
        if not review:
            raise NotFoundError("Review", review_id)
        return review

    async def list_reviews_for_pr(self, pull_request_id: str) -> List[Review]:
        return list(await self.review_repo.list_by_pr(pull_request_id))

    async def create_review(self, data: ReviewCreate) -> Review:
        review = Review(
            pull_request_id=data.pull_request_id,
            commit_sha=data.commit_sha,
            status="pending",
            started_at=datetime.now(timezone.utc),
            findings_count=0,
        )
        return await self.review_repo.create(review)

    async def add_finding(
        self, review_id: str, data: ReviewCommentCreate
    ) -> ReviewComment:
        review = await self.get_review(review_id)
        comment = ReviewComment(
            review_id=review.id,
            file_path=data.file_path,
            line_number=data.line_number,
            end_line_number=data.end_line_number,
            side=data.side,
            category=data.category,
            severity=data.severity,
            title=data.title,
            message=data.message,
            suggested_patch=data.suggested_patch,
        )
        created_comment = await self.comment_repo.create(comment)

        # Increment review findings count
        review.findings_count += 1
        await self.session.commit()
        return created_comment

    async def complete_review(
        self,
        review_id: str,
        summary: str,
        score: float,
        security_score: float,
        performance_score: float,
        quality_score: float,
    ) -> Review:
        review = await self.get_review(review_id)
        review.status = "completed"
        review.summary = summary
        review.score = score
        review.security_score = security_score
        review.performance_score = performance_score
        review.quality_score = quality_score
        review.completed_at = datetime.now(timezone.utc)

        await self.session.commit()
        await self.session.refresh(review)
        return review
