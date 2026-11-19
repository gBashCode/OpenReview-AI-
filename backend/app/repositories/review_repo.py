"""Review and Comment Data Access Objects."""

from typing import List, Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.review import Review
from app.models.review_comment import ReviewComment
from app.repositories.base import BaseRepository


class ReviewRepo(BaseRepository[Review]):
    """Data access layer for Review entities."""

    def __init__(self, session: AsyncSession):
        super().__init__(Review, session)

    async def get_with_comments(self, review_id: str) -> Optional[Review]:
        """Fetch review along with all nested comments and findings."""
        result = await self.session.execute(
            select(Review)
            .options(selectinload(Review.findings))
            .where(Review.id == review_id)
        )
        return result.scalar_one_or_none()

    async def list_by_pr(self, pull_request_id: str) -> Sequence[Review]:
        result = await self.session.execute(
            select(Review)
            .where(Review.pull_request_id == pull_request_id)
            .order_by(Review.created_at.desc())
        )
        return result.scalars().all()


class ReviewCommentRepo(BaseRepository[ReviewComment]):
    """Data access layer for ReviewComment entities."""

    def __init__(self, session: AsyncSession):
        super().__init__(ReviewComment, session)

    async def list_by_review(self, review_id: str) -> Sequence[ReviewComment]:
        result = await self.session.execute(
            select(ReviewComment)
            .where(ReviewComment.review_id == review_id)
            .order_by(ReviewComment.file_path, ReviewComment.line_number)
        )
        return result.scalars().all()
