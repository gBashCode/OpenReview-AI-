"""FastAPI Dependency Injection providers."""

from typing import Optional
from fastapi import Depends, Header, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import Settings, get_settings
from app.core.exceptions import AuthenticationError, NotFoundError, PermissionDeniedError
from app.core.security import decode_token
from app.database.session import get_db
from app.organizations.models import OrganizationMember
from app.users.models import User
from app.services.health_service import HealthService
from app.services.repository_service import RepositoryService
from app.services.review_service import ReviewService

security_bearer = HTTPBearer(auto_error=False)

ROLE_HIERARCHY = {
    "auditor": 1,
    "reviewer": 2,
    "maintainer": 3,
    "admin": 4,
}


def get_health_service(session: AsyncSession = Depends(get_db)) -> HealthService:
    """Provides HealthService instance injected with active db session."""
    return HealthService(session)


def get_repository_service(session: AsyncSession = Depends(get_db)) -> RepositoryService:
    """Provides RepositoryService instance injected with active db session."""
    return RepositoryService(session)


def get_review_service(session: AsyncSession = Depends(get_db)) -> ReviewService:
    """Provides ReviewService instance injected with active db session."""
    return ReviewService(session)


class PaginationParams:
    """Reusable query pagination dependency."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number starting from 1"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size
        self.limit = page_size


async def get_current_user_optional(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    session: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Retrieves authenticated user from JWT if present, else returns None."""
    if not auth or not auth.credentials:
        return None
    try:
        payload = decode_token(auth.credentials)
        user_id = payload.get("sub")
        if not user_id:
            return None
        stmt = select(User).where(User.id == user_id, User.is_active == True)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    except Exception:
        return None


async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Enforces JWT authentication and returns current active User."""
    if not auth or not auth.credentials:
        raise AuthenticationError("Authorization header with Bearer token is required.")

    try:
        payload = decode_token(auth.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Token payload missing subject claim.")
    except Exception as exc:
        raise AuthenticationError(f"Invalid or expired authentication token: {str(exc)}")

    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise AuthenticationError("User associated with this token no longer exists.")
    if not user.is_active:
        raise AuthenticationError("User account has been deactivated.")

    return user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Verifies that the authenticated user possesses superuser privileges."""
    if not current_user.is_superuser:
        raise PermissionDeniedError("Administrative superuser privileges required.")
    return current_user


class RequireOrgRole:
    """Dependency factory checking that the user belongs to an organization with at least required_role."""

    def __init__(self, required_role: str = "reviewer"):
        self.required_role = required_role
        self.min_level = ROLE_HIERARCHY.get(required_role, 1)

    async def __call__(
        self,
        org_id_header: Optional[str] = Header(None, alias="X-Organization-ID"),
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_db),
    ) -> OrganizationMember:
        if current_user.is_superuser:
            # Superuser bypasses tenant checks with a virtual or owner membership
            return OrganizationMember(
                organization_id=org_id_header or "superuser-org",
                user_id=current_user.id,
                role="admin",
            )

        if not org_id_header:
            # Check if user belongs to at least one organization
            stmt = select(OrganizationMember).where(OrganizationMember.user_id == current_user.id)
            result = await session.execute(stmt)
            member = result.scalars().first()
            if not member:
                raise PermissionDeniedError("User does not belong to any organization.")
            return member

        stmt = select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id_header,
            OrganizationMember.user_id == current_user.id,
        )
        result = await session.execute(stmt)
        member = result.scalar_one_or_none()

        if not member:
            raise PermissionDeniedError(f"User is not a member of organization '{org_id_header}'.")

        member_level = ROLE_HIERARCHY.get(member.role, 0)
        if member_level < self.min_level:
            raise PermissionDeniedError(
                f"Insufficient permissions: requires '{self.required_role}' role, but user has '{member.role}'."
            )

        return member
