"""Analytics and Audit Logging Service."""

import json
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.analytics.models import AuditLog
from app.analytics.schemas import UsageStatsRead
from app.autofix.models import Patch
from app.findings.models import Finding
from app.pull_requests.models import PullRequest
from app.repositories.models import Repository
from app.reviews.models import Review


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_audit_log(
        self,
        organization_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Appends an enterprise audit log record."""
        meta_str = json.dumps(metadata) if metadata else None
        log_entry = AuditLog(
            organization_id=organization_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_json=meta_str,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.session.add(log_entry)
        await self.session.commit()
        await self.session.refresh(log_entry)
        return log_entry

    async def list_audit_logs(
        self,
        organization_id: str,
        action: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[AuditLog], int]:
        """Lists audit logs for an organization with pagination."""
        stmt = select(AuditLog).where(AuditLog.organization_id == organization_id)
        if action:
            stmt = stmt.where(AuditLog.action == action)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def get_usage_stats(self, organization_id: str) -> UsageStatsRead:
        """Aggregates high-level metrics for an organization dashboard."""
        # Count active repos
        stmt_repo = (
            select(func.count(Repository.id))
            .where(Repository.organization_id == organization_id, Repository.is_active == True)
        )
        active_repos = (await self.session.execute(stmt_repo)).scalar() or 0

        # Count total reviews
        stmt_rev = (
            select(func.count(Review.id), func.avg(Review.score))
            .join(PullRequest, Review.pull_request_id == PullRequest.id)
            .join(Repository, PullRequest.repository_id == Repository.id)
            .where(Repository.organization_id == organization_id)
        )
        rev_res = (await self.session.execute(stmt_rev)).first()
        total_reviews = rev_res[0] or 0
        avg_score = float(rev_res[1] or 92.5)

        # Count findings & security findings
        stmt_findings = (
            select(
                func.count(Finding.id),
                func.count(func.nullif(Finding.category != "security", True)),
            )
            .join(Review, Finding.review_id == Review.id)
            .join(PullRequest, Review.pull_request_id == PullRequest.id)
            .join(Repository, PullRequest.repository_id == Repository.id)
            .where(Repository.organization_id == organization_id)
        )
        finding_res = (await self.session.execute(stmt_findings)).first()
        total_findings = finding_res[0] or 0
        sec_findings = finding_res[1] or 0

        # Count applied patches
        stmt_patches = (
            select(func.count(Patch.id))
            .join(Finding, Patch.finding_id == Finding.id)
            .join(Review, Finding.review_id == Review.id)
            .join(PullRequest, Review.pull_request_id == PullRequest.id)
            .join(Repository, PullRequest.repository_id == Repository.id)
            .where(Repository.organization_id == organization_id, Patch.status == "approved")
        )
        applied_patches = (await self.session.execute(stmt_patches)).scalar() or 0

        return UsageStatsRead(
            total_reviews=total_reviews,
            total_findings=total_findings,
            total_patches_applied=applied_patches,
            avg_quality_score=round(avg_score, 1),
            security_issues_prevented=sec_findings,
            active_repositories=active_repos,
        )
