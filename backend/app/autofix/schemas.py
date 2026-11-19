"""Autofix Patch Pydantic Schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.verification.schemas import TestRunRead


class PatchBase(BaseModel):
    finding_id: str
    original_code: str
    proposed_code: str
    diff_content: str
    status: str = "pending"  # pending, approved, rejected, applied, failed, rolled_back
    rejection_reason: Optional[str] = None
    rollback_diff: Optional[str] = None
    formatter_status: Optional[str] = "passed"
    linter_status: Optional[str] = "passed"
    sandbox_status: Optional[str] = "passed"
    regression_status: Optional[str] = "passed"
    failure_explanation: Optional[str] = None
    branch_name: Optional[str] = None
    pr_url: Optional[str] = None


class PatchCreate(BaseModel):
    finding_id: str
    original_code: str
    proposed_code: str
    diff_content: Optional[str] = None


class GenerateAutoFixRequest(BaseModel):
    finding_id: str
    regression_test_code: Optional[str] = None


class PatchDecisionRequest(BaseModel):
    decision: str = Field(description="'approve' or 'reject'")
    rejection_reason: Optional[str] = None


class CommitPatchRequest(BaseModel):
    commit_message: Optional[str] = None
    branch_name: Optional[str] = None


class CreatePrRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    target_branch: Optional[str] = None


class RollbackPatchRequest(BaseModel):
    reason: Optional[str] = None


class PatchPreviewResponse(BaseModel):
    patch_id: str
    finding_id: str
    file_path: str
    original_code: str
    proposed_code: str
    diff_content: str
    rollback_diff: Optional[str] = None
    status: str
    formatter_status: Optional[str] = "passed"
    linter_status: Optional[str] = "passed"
    sandbox_status: Optional[str] = "passed"


class PatchReportResponse(BaseModel):
    patch_id: str
    finding_id: str
    file_path: str
    status: str
    diff_content: str
    rollback_diff: Optional[str] = None
    formatter_status: str
    linter_status: str
    sandbox_status: str
    regression_status: str
    failure_explanation: Optional[str] = None
    branch_name: Optional[str] = None
    pr_url: Optional[str] = None
    test_runs: List[TestRunRead] = Field(default_factory=list)


class PatchRead(PatchBase):
    id: str
    applied_by_user_id: Optional[str] = None
    commit_sha: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    test_runs: List[TestRunRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
