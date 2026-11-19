"""Findings Service."""

from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import NotFoundError
from app.findings.models import Finding
from app.findings.schemas import FindingCreate, FindingUpdate
from app.reviews.models import Review


class FindingService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_review(
        self,
        review_id: str,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        is_resolved: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Finding], int]:
        """Lists findings for a review with optional filters."""
        stmt = (
            select(Finding)
            .options(selectinload(Finding.patches))
            .where(Finding.review_id == review_id)
        )
        if category:
            stmt = stmt.where(Finding.category == category)
        if severity:
            stmt = stmt.where(Finding.severity == severity)
        if is_resolved is not None:
            stmt = stmt.where(Finding.is_resolved == is_resolved)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(Finding.severity.desc(), Finding.file_path).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def list_all(
        self,
        review_id: Optional[str] = None,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        is_resolved: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Finding], int]:
        """Lists findings across reviews with rich filtering, search, and pagination."""
        stmt = select(Finding).options(selectinload(Finding.patches))
        if review_id:
            stmt = stmt.where(Finding.review_id == review_id)
        if category:
            stmt = stmt.where(Finding.category.ilike(f"%{category}%"))
        if severity:
            stmt = stmt.where(Finding.severity.ilike(f"%{severity}%"))
        if is_resolved is not None:
            stmt = stmt.where(Finding.is_resolved == is_resolved)
        if search:
            stmt = stmt.where(
                (Finding.title.ilike(f"%{search}%"))
                | (Finding.message.ilike(f"%{search}%"))
                | (Finding.file_path.ilike(f"%{search}%"))
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(Finding.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def get_by_id(self, finding_id: str) -> Finding:
        """Retrieves a finding by UUID."""
        stmt = (
            select(Finding)
            .options(selectinload(Finding.patches), selectinload(Finding.discussions))
            .where(Finding.id == finding_id)
        )
        finding = (await self.session.execute(stmt)).scalar_one_or_none()
        if not finding:
            raise NotFoundError("Finding", finding_id)
        return finding

    async def create(self, data: FindingCreate) -> Finding:
        """Creates a new finding and increments review's findings_count."""
        stmt_rev = select(Review).where(Review.id == data.review_id)
        review = (await self.session.execute(stmt_rev)).scalar_one_or_none()
        if not review:
            raise NotFoundError("Review", data.review_id)

        finding = Finding(
            review_id=data.review_id,
            file_path=data.file_path,
            line_number=data.line_number,
            end_line_number=data.end_line_number,
            side=data.side or "RIGHT",
            category=data.category,
            severity=data.severity,
            title=data.title,
            message=data.message,
            suggested_patch=data.suggested_patch,
            agent_name=data.agent_name,
            confidence_score=data.confidence_score,
            is_resolved=data.is_resolved,
            github_comment_id=data.github_comment_id,
        )
        self.session.add(finding)
        review.findings_count += 1
        await self.session.commit()
        await self.session.refresh(finding)
        return finding

    async def update(self, finding_id: str, data: FindingUpdate) -> Finding:
        """Updates finding resolution status or patch."""
        finding = await self.get_by_id(finding_id)
        if data.is_resolved is not None:
            finding.is_resolved = data.is_resolved
        if data.suggested_patch is not None:
            finding.suggested_patch = data.suggested_patch
        if data.github_comment_id is not None:
            finding.github_comment_id = data.github_comment_id

        await self.session.commit()
        await self.session.refresh(finding)
        return finding
