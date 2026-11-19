"""Organization and Team Member Service."""

import re
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.organizations.models import Organization, OrganizationMember
from app.organizations.schemas import OrganizationCreate, OrganizationUpdate
from app.users.models import User


class OrganizationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_user_organizations(self, user_id: str) -> List[Organization]:
        """Lists all organizations that the given user belongs to."""
        stmt = (
            select(Organization)
            .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
            .where(OrganizationMember.user_id == user_id)
            .order_by(Organization.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, organization_id: str) -> Organization:
        """Retrieves an organization by its UUID."""
        stmt = select(Organization).where(Organization.id == organization_id)
        org = (await self.session.execute(stmt)).scalar_one_or_none()
        if not org:
            raise NotFoundError("Organization", organization_id)
        return org

    async def get_by_slug(self, slug: str) -> Organization:
        """Retrieves an organization by unique URL slug."""
        stmt = select(Organization).where(Organization.slug == slug)
        org = (await self.session.execute(stmt)).scalar_one_or_none()
        if not org:
            raise NotFoundError("Organization", slug)
        return org

    async def create(self, request: OrganizationCreate, creator_user_id: str) -> Organization:
        """Creates a new organization and assigns the creator as admin."""
        slug = request.slug
        if not slug:
            clean = re.sub(r"[^a-z0-9-]", "", request.name.lower().replace(" ", "-"))
            slug = f"{clean}-{creator_user_id[:6]}"

        stmt = select(Organization).where(Organization.slug == slug)
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ConflictError(f"Organization slug '{slug}' is already taken.")

        org = Organization(
            name=request.name,
            slug=slug,
            avatar_url=request.avatar_url,
            plan=request.plan or "team",
        )
        self.session.add(org)
        await self.session.flush()

        member = OrganizationMember(
            organization_id=org.id,
            user_id=creator_user_id,
            role="admin",
        )
        self.session.add(member)
        await self.session.commit()
        await self.session.refresh(org)
        return org

    async def update(self, organization_id: str, request: OrganizationUpdate) -> Organization:
        """Updates organization details."""
        org = await self.get_by_id(organization_id)
        if request.name is not None:
            org.name = request.name
        if request.avatar_url is not None:
            org.avatar_url = request.avatar_url
        if request.plan is not None:
            org.plan = request.plan
        if request.max_repos is not None:
            org.max_repos = request.max_repos

        await self.session.commit()
        await self.session.refresh(org)
        return org

    async def list_members(self, organization_id: str) -> List[OrganizationMember]:
        """Lists all members of an organization with joined user profiles."""
        stmt = (
            select(OrganizationMember)
            .options(selectinload(OrganizationMember.user))
            .where(OrganizationMember.organization_id == organization_id)
            .order_by(OrganizationMember.created_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add_member(self, organization_id: str, user_id: str, role: str = "reviewer") -> OrganizationMember:
        """Adds a user to an organization."""
        await self.get_by_id(organization_id)

        # Check if user exists
        stmt_user = select(User).where(User.id == user_id)
        user = (await self.session.execute(stmt_user)).scalar_one_or_none()
        if not user:
            raise NotFoundError("User", user_id)

        # Check existing membership
        stmt = select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id,
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ConflictError("User is already a member of this organization.")

        member = OrganizationMember(
            organization_id=organization_id,
            user_id=user_id,
            role=role,
        )
        self.session.add(member)
        await self.session.commit()

        stmt_loaded = (
            select(OrganizationMember)
            .options(selectinload(OrganizationMember.user))
            .where(OrganizationMember.id == member.id)
        )
        return (await self.session.execute(stmt_loaded)).scalar_one()

    async def update_member_role(self, organization_id: str, user_id: str, new_role: str) -> OrganizationMember:
        """Updates the role of an organization member."""
        stmt = select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id,
        )
        member = (await self.session.execute(stmt)).scalar_one_or_none()
        if not member:
            raise NotFoundError("OrganizationMember", f"{organization_id}/{user_id}")

        member.role = new_role
        await self.session.commit()

        stmt_loaded = (
            select(OrganizationMember)
            .options(selectinload(OrganizationMember.user))
            .where(OrganizationMember.id == member.id)
        )
        return (await self.session.execute(stmt_loaded)).scalar_one()

    async def remove_member(self, organization_id: str, user_id: str) -> None:
        """Removes a member from an organization, ensuring at least one admin remains."""
        stmt = select(OrganizationMember).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id,
        )
        member = (await self.session.execute(stmt)).scalar_one_or_none()
        if not member:
            raise NotFoundError("OrganizationMember", f"{organization_id}/{user_id}")

        # Check if last admin
        if member.role == "admin":
            stmt_admin_count = (
                select(func.count(OrganizationMember.id))
                .where(
                    OrganizationMember.organization_id == organization_id,
                    OrganizationMember.role == "admin",
                )
            )
            admin_count = (await self.session.execute(stmt_admin_count)).scalar() or 0
            if admin_count <= 1:
                raise PermissionDeniedError("Cannot remove the sole administrator of the organization.")

        await self.session.delete(member)
        await self.session.commit()
