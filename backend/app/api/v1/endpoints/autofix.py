"""Autofix Patch and Sandbox Verification Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.autofix.schemas import PatchDecisionRequest, PatchRead
from app.autofix.service import AutofixService
from app.core.dependencies import get_current_user_optional
from app.database.session import get_db
from app.users.models import User
from app.verification.schemas import TestRunRead

router = APIRouter(prefix="/autofix", tags=["AutoFix"])


def get_autofix_service(session: AsyncSession = Depends(get_db)) -> AutofixService:
    return AutofixService(session)


@router.get("/{patch_id}", response_model=PatchRead, summary="Get patch details")
async def get_patch(
    patch_id: str,
    service: AutofixService = Depends(get_autofix_service),
) -> PatchRead:
    patch = await service.get_by_id(patch_id)
    return PatchRead.model_validate(patch)


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
    user_id = current_user.id if current_user else None
    patch = await service.process_decision(patch_id, payload, user_id=user_id)
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
