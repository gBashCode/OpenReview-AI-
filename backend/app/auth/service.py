"""Authentication and User Management Service."""

import re
from typing import Optional, Tuple
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.schemas import LoginRequest, RegisterRequest, Token
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.core.security import create_access_token, hash_password, verify_password
from app.organizations.models import Organization, OrganizationMember
from app.users.models import User


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def register(self, request: RegisterRequest) -> Tuple[User, Token]:
        """Registers a new user and creates an initial organization if requested."""
        stmt = select(User).where(
            or_(User.email == request.email, User.username == request.username)
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing:
            if existing.email == request.email:
                raise ConflictError("A user with this email address already exists.")
            raise ConflictError("A user with this username already exists.")

        user = User(
            email=request.email,
            username=request.username,
            full_name=request.full_name,
            hashed_password=hash_password(request.password),
            is_active=True,
            is_superuser=False,
        )
        self.session.add(user)
        await self.session.flush()

        # If user specified organization name or by default create a personal workspace
        org_name = request.organization_name or f"{request.username}'s Team"
        slug_clean = re.sub(r"[^a-z0-9-]", "", org_name.lower().replace(" ", "-"))
        slug = f"{slug_clean}-{user.id[:6]}"

        org = Organization(
            name=org_name,
            slug=slug,
            plan="team",
            max_repos=50,
        )
        self.session.add(org)
        await self.session.flush()

        membership = OrganizationMember(
            organization_id=org.id,
            user_id=user.id,
            role="admin",
        )
        self.session.add(membership)
        await self.session.commit()
        await self.session.refresh(user)

        token_str = create_access_token(
            subject=user.id,
            extra_claims={"email": user.email, "username": user.username},
        )
        token = Token(access_token=token_str, expires_in=86400)
        return user, token

    async def login(self, request: LoginRequest) -> Tuple[User, Token]:
        """Authenticates user credentials and returns JWT token."""
        stmt = select(User).where(User.email == request.email)
        user = (await self.session.execute(stmt)).scalar_one_or_none()

        if not user or not verify_password(request.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password.")

        if not user.is_active:
            raise AuthenticationError("This account has been deactivated.")

        token_str = create_access_token(
            subject=user.id,
            extra_claims={"email": user.email, "username": user.username},
        )
        token = Token(access_token=token_str, expires_in=86400)
        return user, token

    async def get_user_by_id(self, user_id: str) -> User:
        """Retrieves a user by primary ID."""
        stmt = select(User).where(User.id == user_id)
        user = (await self.session.execute(stmt)).scalar_one_or_none()
        if not user:
            raise NotFoundError("User", user_id)
        return user
