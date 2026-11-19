"""Finding Verification API Endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.verification.policy import ReviewPolicyEngine
from app.verification.schemas import (
    CandidateFinding,
    ReviewPolicyConfig,
    VerificationBatchResult,
    VerifiedFinding,
)
from app.verification.service import FindingVerificationService

router = APIRouter(prefix="/verification", tags=["Finding Verification"])


class VerifySingleRequest(BaseModel):
    finding: CandidateFinding
    repository_files: Optional[Dict[str, str]] = Field(default=None, description="Optional repository file map")
    changed_files: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional PR changed files list")
    policy: Optional[ReviewPolicyConfig] = Field(default=None, description="Custom review policy")


class VerifyBatchRequest(BaseModel):
    findings: List[CandidateFinding]
    repository_files: Optional[Dict[str, str]] = Field(default=None, description="Optional repository file map")
    changed_files: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional PR changed files list")
    test_files: Optional[List[str]] = Field(default=None, description="Optional test file list")
    policy: Optional[ReviewPolicyConfig] = Field(default=None, description="Custom review policy")


def get_verification_service(session: AsyncSession = Depends(get_db)) -> FindingVerificationService:
    return FindingVerificationService(session)


@router.post(
    "/verify",
    response_model=VerifiedFinding,
    summary="Verify an individual code finding through the 12-step pipeline",
)
async def verify_individual_finding(
    payload: VerifySingleRequest,
    service: FindingVerificationService = Depends(get_verification_service),
) -> VerifiedFinding:
    """Executes the full 12-step verification engine to eliminate false positives and calibrate confidence."""
    return service.verify_candidate(
        candidate=payload.finding,
        repository_files=payload.repository_files,
        changed_files=payload.changed_files,
        policy=payload.policy,
    )


@router.post(
    "/verify-batch",
    response_model=VerificationBatchResult,
    summary="Verify a batch of candidate findings with inter-finding deduplication",
)
async def verify_findings_batch(
    payload: VerifyBatchRequest,
    service: FindingVerificationService = Depends(get_verification_service),
) -> VerificationBatchResult:
    """Verifies candidate findings, removes duplicates, applies review policies, and sets publishability."""
    return service.verify_candidates_batch(
        candidates=payload.findings,
        repository_files=payload.repository_files,
        changed_files=payload.changed_files,
        test_files=payload.test_files,
        policy=payload.policy,
    )


@router.post(
    "/reviews/{review_id}",
    response_model=VerificationBatchResult,
    summary="Run verification pipeline on all persisted findings for a review",
)
async def verify_review_findings(
    review_id: str,
    policy_name: Optional[str] = Query(default="standard", description="standard, strict, security, permissive"),
    service: FindingVerificationService = Depends(get_verification_service),
) -> VerificationBatchResult:
    """Verifies all findings recorded for a PR review and updates database records."""
    if policy_name == "strict":
        policy = ReviewPolicyEngine.get_strict_policy()
    elif policy_name == "security":
        policy = ReviewPolicyEngine.get_security_only_policy()
    elif policy_name == "permissive":
        policy = ReviewPolicyEngine.get_permissive_policy()
    else:
        policy = ReviewPolicyEngine.get_standard_policy()

    return await service.verify_review_findings(review_id, policy=policy)


@router.get(
    "/policies",
    summary="List available review policy profiles",
)
async def list_policies():
    """Returns preset review policies for CI/CD gates and comment publishing."""
    return {
        "standard": ReviewPolicyEngine.get_standard_policy(),
        "strict": ReviewPolicyEngine.get_strict_policy(),
        "security_only": ReviewPolicyEngine.get_security_only_policy(),
        "permissive": ReviewPolicyEngine.get_permissive_policy(),
    }
