"""Findings API Endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.autofix.schemas import PatchCreate, PatchRead
from app.autofix.service import AutofixService
from app.database.session import get_db
from app.findings.schemas import FindingRead, FindingUpdate
from app.findings.service import FindingService

router = APIRouter(prefix="/findings", tags=["Findings"])


def get_finding_service(session: AsyncSession = Depends(get_db)) -> FindingService:
    return FindingService(session)


def get_autofix_service(session: AsyncSession = Depends(get_db)) -> AutofixService:
    return AutofixService(session)


@router.get("/{finding_id}", response_model=FindingRead, summary="Get finding by ID")
async def get_finding(
    finding_id: str,
    service: FindingService = Depends(get_finding_service),
) -> FindingRead:
    finding = await service.get_by_id(finding_id)
    return FindingRead.model_validate(finding)


@router.patch("/{finding_id}", response_model=FindingRead, summary="Update finding resolution or message")
async def update_finding(
    finding_id: str,
    payload: FindingUpdate,
    service: FindingService = Depends(get_finding_service),
) -> FindingRead:
    finding = await service.update(finding_id, payload)
    return FindingRead.model_validate(finding)


@router.get(
    "/{finding_id}/patches",
    response_model=List[PatchRead],
    summary="List autofix patches for finding",
)
async def list_finding_patches(
    finding_id: str,
    autofix_service: AutofixService = Depends(get_autofix_service),
) -> List[PatchRead]:
    patches = await autofix_service.list_by_finding(finding_id)
    return [PatchRead.model_validate(p) for p in patches]


@router.post(
    "/{finding_id}/patches",
    response_model=PatchRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create or propose autofix patch for finding",
)
async def create_finding_patch(
    finding_id: str,
    payload: PatchCreate,
    autofix_service: AutofixService = Depends(get_autofix_service),
) -> PatchRead:
    payload.finding_id = finding_id
    patch = await autofix_service.create_patch(payload)
    return PatchRead.model_validate(patch)
