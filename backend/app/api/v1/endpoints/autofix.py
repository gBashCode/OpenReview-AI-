"""Autofix Patch and Sandbox Verification Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.autofix.schemas import (
    CommitPatchRequest,
    CreatePrRequest,
    GenerateAutoFixRequest,
    PatchDecisionRequest,
    PatchPreviewResponse,
    PatchRead,
    PatchReportResponse,
    RollbackPatchRequest,
)
from app.autofix.service import AutofixService
from app.core.dependencies import get_current_user_optional
from app.database.session import get_db
from app.users.models import User
from app.verification.schemas import TestRunRead

router = APIRouter(prefix="/autofix", tags=["AutoFix"])


def get_autofix_service(session: AsyncSession = Depends(get_db)) -> AutofixService:
    return AutofixService(session)


@router.post(
    "/generate",
    response_model=PatchRead,
    status_code=status.HTTP_201_CREATED,
    summary="Generate minimal patch and run sandbox validation",
)
async def generate_autofix_patch(
    payload: GenerateAutoFixRequest,
    service: AutofixService = Depends(get_autofix_service),
) -> PatchRead:
    """Executes the complete 14-step AutoFix pipeline to generate a minimal, validated patch."""
    patch = await service.generate_autofix_for_finding(
        finding_id=payload.finding_id,
        regression_test_code=payload.regression_test_code,
    )
    return PatchRead.model_validate(patch)


@router.get("/{patch_id}", response_model=PatchRead, summary="Get patch details")
async def get_patch(
    patch_id: str,
    service: AutofixService = Depends(get_autofix_service),
) -> PatchRead:
    patch = await service.get_by_id(patch_id)
    return PatchRead.model_validate(patch)


@router.get(
    "/{patch_id}/preview",
    response_model=PatchPreviewResponse,
    summary="Get before-and-after code preview and unified diff",
)
async def get_patch_preview(
    patch_id: str,
    service: AutofixService = Depends(get_autofix_service),
) -> PatchPreviewResponse:
    """Retrieves side-by-side original and proposed code with diff and rollback patch."""
    return await service.get_preview(patch_id)


@router.get(
    "/{patch_id}/report",
    response_model=PatchReportResponse,
    summary="Get diagnostic patch report and sandbox test execution logs",
)
async def get_patch_report(
    patch_id: str,
    service: AutofixService = Depends(get_autofix_service),
) -> PatchReportResponse:
    """Retrieves comprehensive validation telemetry, linter status, and failure explanations."""
    return await service.get_report(patch_id)


@router.post(
    "/{patch_id}/decision",
    response_model=PatchRead,
    summary="Approve or reject an autofix patch",
)
async def process_patch_decision(
    patch_id: str,
    payload: PatchDecisionRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    service: AutofixService = Depends(get_autofix_service),
) -> PatchRead:
    """Records human review decision (approve or reject with reason)."""
    user_id = current_user.id if current_user else None
    patch = await service.process_decision(patch_id, payload, user_id=user_id)
    return PatchRead.model_validate(patch)


@router.post(
    "/{patch_id}/commit",
    response_model=PatchRead,
    summary="Explicit human approval: commit patch to target branch",
)
async def commit_patch(
    patch_id: str,
    payload: Optional[CommitPatchRequest] = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
    service: AutofixService = Depends(get_autofix_service),
) -> PatchRead:
    """Requires human approval to commit the verified patch to the PR branch."""
    user_id = current_user.id if current_user else None
    patch = await service.approve_and_commit(patch_id, payload, user_id=user_id)
    return PatchRead.model_validate(patch)


@router.post(
    "/{patch_id}/create-pr",
    response_model=PatchRead,
    summary="Explicit human approval: open a dedicated fix Pull Request",
)
async def create_fix_pr(
    patch_id: str,
    payload: Optional[CreatePrRequest] = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
    service: AutofixService = Depends(get_autofix_service),
) -> PatchRead:
    """Requires human approval to open an automated remediation Pull Request on GitHub."""
    user_id = current_user.id if current_user else None
    patch = await service.approve_and_create_pr(patch_id, payload, user_id=user_id)
    return PatchRead.model_validate(patch)


@router.post(
    "/{patch_id}/rollback",
    response_model=PatchRead,
    summary="Rollback an applied patch using the inverse diff",
)
async def rollback_patch(
    patch_id: str,
    payload: Optional[RollbackPatchRequest] = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
    service: AutofixService = Depends(get_autofix_service),
) -> PatchRead:
    """Applies the inverse rollback patch to revert previously committed changes."""
    user_id = current_user.id if current_user else None
    patch = await service.rollback_patch(patch_id, payload, user_id=user_id)
    return PatchRead.model_validate(patch)


@router.get(
    "/{patch_id}/test-runs",
    response_model=List[TestRunRead],
    summary="List sandbox test runs for patch",
)
async def list_patch_test_runs(
    patch_id: str,
    service: AutofixService = Depends(get_autofix_service),
) -> List[TestRunRead]:
    patch = await service.get_by_id(patch_id)
    return [TestRunRead.model_validate(tr) for tr in patch.test_runs]
