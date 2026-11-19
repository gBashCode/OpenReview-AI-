"""Analytics and Enterprise Audit Logs Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.analytics.schemas import AuditLogRead, UsageStatsRead
from app.analytics.service import AnalyticsService
from app.database.session import get_db
from app.organizations.models import Organization

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_analytics_service(session: AsyncSession = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(session)


@router.get("/stats", response_model=UsageStatsRead, summary="Get organization review and quality metrics")
async def get_usage_statistics(
    organization_id: Optional[str] = Header(None, alias="X-Organization-ID"),
    query_org_id: Optional[str] = Query(None, alias="organization_id"),
    session: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(get_analytics_service),
) -> UsageStatsRead:
    target_org_id = organization_id or query_org_id
    if not target_org_id:
        stmt_org = select(Organization.id).order_by(Organization.created_at)
        target_org_id = (await session.execute(stmt_org)).scalars().first() or "default-org"

    return await service.get_usage_stats(target_org_id)


@router.get("/audit-logs", response_model=List[AuditLogRead], summary="List enterprise audit log entries")
async def list_audit_logs(
    organization_id: Optional[str] = Header(None, alias="X-Organization-ID"),
    query_org_id: Optional[str] = Query(None, alias="organization_id"),
    action: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(get_analytics_service),
) -> List[AuditLogRead]:
    target_org_id = organization_id or query_org_id
    if not target_org_id:
        stmt_org = select(Organization.id).order_by(Organization.created_at)
        target_org_id = (await session.execute(stmt_org)).scalars().first() or "default-org"

    logs, _ = await service.list_audit_logs(
        organization_id=target_org_id,
        action=action,
        skip=skip,
        limit=limit,
    )
    return [AuditLogRead.model_validate(log) for log in logs]
