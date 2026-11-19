"""Analytics and AuditLog Pydantic schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AuditLogBase(BaseModel):
    organization_id: str
    user_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: str
    metadata_json: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditLogRead(AuditLogBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UsageStatsRead(BaseModel):
    total_reviews: int
    total_findings: int
    total_patches_applied: int
    avg_quality_score: float
    security_issues_prevented: int
    active_repositories: int
