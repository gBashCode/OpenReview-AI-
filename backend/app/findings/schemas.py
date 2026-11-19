"""Finding Pydantic schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class FindingBase(BaseModel):
    review_id: str
    file_path: str
    line_number: Optional[int] = None
    end_line_number: Optional[int] = None
    side: str = "RIGHT"
    category: str = Field(..., description="security, bug, performance, style, architecture")
    severity: str = Field(..., description="critical, high, medium, low, info")
    title: str
    message: str
    suggested_patch: Optional[str] = None
    agent_name: Optional[str] = None
    confidence_score: Optional[float] = None
    discussion_state: Optional[str] = "Accepted"
    evidence: Optional[str] = None
    verification_status: Optional[str] = "Confirmed"
    root_cause: Optional[str] = None
    impact: Optional[str] = None
    actionability_score: Optional[float] = None
    is_publishable: bool = True
    rejection_reason: Optional[str] = None
    is_resolved: bool = False
    github_comment_id: Optional[str] = None


class FindingCreate(FindingBase):
    pass


class FindingUpdate(BaseModel):
    is_resolved: Optional[bool] = None
    suggested_patch: Optional[str] = None
    github_comment_id: Optional[str] = None


class FindingRead(FindingBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
