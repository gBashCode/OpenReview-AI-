"""Autofix Patch Pydantic schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class PatchBase(BaseModel):
    finding_id: str
    original_code: str
    proposed_code: str
    diff_content: str
    status: str = "pending"  # pending, approved, rejected, applied, failed
    rejection_reason: Optional[str] = None


class PatchCreate(BaseModel):
    finding_id: str
    original_code: str
    proposed_code: str
    diff_content: Optional[str] = None


class PatchDecisionRequest(BaseModel):
    decision: str  # approve, reject
    rejection_reason: Optional[str] = None


class PatchRead(PatchBase):
    id: str
    applied_by_user_id: Optional[str] = None
    commit_sha: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
