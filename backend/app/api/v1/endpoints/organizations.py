"""Organization and Team Management Endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import RequireOrgRole, get_current_user
from app.database.session import get_db
from app.organizations.models import OrganizationMember
from app.organizations.schemas import (
    OrganizationCreate,
    OrganizationMemberCreate,
    OrganizationMemberRead,
    OrganizationMemberUpdate,
    OrganizationRead,
    OrganizationUpdate,
)
from app.organizations.service import OrganizationService
from app.users.models import User

router = APIRouter(prefix="/organizations", tags=["Organizations"])


def get_org_service(session: AsyncSession = Depends(get_db)) -> OrganizationService:
    return OrganizationService(session)


@router.get("", response_model=List[OrganizationRead], summary="List user's organizations")
async def list_user_organizations(
    current_user: User = Depends(get_current_user),
    service: OrganizationService = Depends(get_org_service),
) -> List[OrganizationRead]:
    orgs = await service.list_user_organizations(current_user.id)
    return [OrganizationRead.model_validate(org) for org in orgs]


@router.post(
    "",
    response_model=OrganizationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new organization",
)
async def create_organization(
    payload: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    service: OrganizationService = Depends(get_org_service),
) -> OrganizationRead:
    org = await service.create(payload, creator_user_id=current_user.id)
    return OrganizationRead.model_validate(org)


@router.get("/{organization_id}", response_model=OrganizationRead, summary="Get organization by ID")
async def get_organization(
    organization_id: str,
    _: OrganizationMember = Depends(RequireOrgRole("reviewer")),
    service: OrganizationService = Depends(get_org_service),
) -> OrganizationRead:
    org = await service.get_by_id(organization_id)
    return OrganizationRead.model_validate(org)


@router.patch("/{organization_id}", response_model=OrganizationRead, summary="Update organization settings")
async def update_organization(
    organization_id: str,
    payload: OrganizationUpdate,
    _: OrganizationMember = Depends(RequireOrgRole("admin")),
    service: OrganizationService = Depends(get_org_service),
) -> OrganizationRead:
    org = await service.update(organization_id, payload)
    return OrganizationRead.model_validate(org)


@router.get(
    "/{organization_id}/members",
    response_model=List[OrganizationMemberRead],
    summary="List organization team members",
)
async def list_members(
    organization_id: str,
    _: OrganizationMember = Depends(RequireOrgRole("reviewer")),
    service: OrganizationService = Depends(get_org_service),
) -> List[OrganizationMemberRead]:
    members = await service.list_members(organization_id)
    return [OrganizationMemberRead.model_validate(m) for m in members]


@router.post(
    "/{organization_id}/members",
    response_model=OrganizationMemberRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a team member to the organization",
)
async def add_member(
    organization_id: str,
    payload: OrganizationMemberCreate,
    _: OrganizationMember = Depends(RequireOrgRole("admin")),
    service: OrganizationService = Depends(get_org_service),
) -> OrganizationMemberRead:
    member = await service.add_member(organization_id, payload.user_id, payload.role)
    return OrganizationMemberRead.model_validate(member)


@router.patch(
    "/{organization_id}/members/{user_id}",
    response_model=OrganizationMemberRead,
    summary="Update a team member's role",
)
async def update_member_role(
    organization_id: str,
    user_id: str,
    payload: OrganizationMemberUpdate,
    _: OrganizationMember = Depends(RequireOrgRole("admin")),
    service: OrganizationService = Depends(get_org_service),
) -> OrganizationMemberRead:
    member = await service.update_member_role(organization_id, user_id, payload.role)
    return OrganizationMemberRead.model_validate(member)


@router.delete(
    "/{organization_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a team member from the organization",
)
async def remove_member(
    organization_id: str,
    user_id: str,
    _: OrganizationMember = Depends(RequireOrgRole("admin")),
    service: OrganizationService = Depends(get_org_service),
) -> None:
    await service.remove_member(organization_id, user_id)
