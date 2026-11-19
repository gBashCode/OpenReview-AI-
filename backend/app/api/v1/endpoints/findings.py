"""Findings API Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
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


@router.get("", response_model=List[FindingRead], summary="List findings with filters")
async def list_findings(
    review_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    is_resolved: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: FindingService = Depends(get_finding_service),
) -> List[FindingRead]:
    findings, _ = await service.list_all(
        review_id=review_id,
        category=category,
        severity=severity,
        is_resolved=is_resolved,
        search=search,
        skip=skip,
        limit=limit,
    )
    return [FindingRead.model_validate(f) for f in findings]



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
