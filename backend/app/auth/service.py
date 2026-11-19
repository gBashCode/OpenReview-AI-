"""Authentication and User Management Service."""

import re
from typing import Optional, Tuple
import httpx
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.schemas import LoginRequest, RegisterRequest, Token
from app.core.config import get_settings
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

    @staticmethod
    def get_github_oauth_url(redirect_uri: Optional[str] = None, state: Optional[str] = None) -> str:
        """Constructs GitHub OAuth authorize URL."""
        settings = get_settings()
        client_id = settings.GITHUB_CLIENT_ID
        if not client_id:
            raise AuthenticationError("GITHUB_CLIENT_ID is not configured in application settings.")

        base_url = "https://github.com/login/oauth/authorize"
        params = [
            f"client_id={client_id}",
            "scope=read:user,user:email",
        ]
        if redirect_uri:
            params.append(f"redirect_uri={redirect_uri}")
        if state:
            params.append(f"state={state}")
        return f"{base_url}?{'&'.join(params)}"

    async def authenticate_github_code(
        self,
        code: str,
        redirect_uri: Optional[str] = None,
    ) -> Tuple[User, Token]:
        """Exchanges GitHub OAuth code for user profile, finds/creates user, and issues JWT."""
        settings = get_settings()
        client_id = settings.GITHUB_CLIENT_ID
        client_secret = settings.GITHUB_CLIENT_SECRET

        if not client_id or not client_secret:
            raise AuthenticationError("GitHub OAuth credentials (client_id / client_secret) are not configured.")

        async with httpx.AsyncClient(timeout=15.0) as client:
            token_payload = {
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
            }
            if redirect_uri:
                token_payload["redirect_uri"] = redirect_uri

            token_resp = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json", "User-Agent": "OpenReviewAI-App/1.0"},
                data=token_payload,
            )

            if token_resp.status_code != 200:
                raise AuthenticationError("Failed to communicate with GitHub OAuth token endpoint.")

            token_data = token_resp.json()
            if "error" in token_data:
                err_msg = token_data.get("error_description") or token_data.get("error")
                raise AuthenticationError(f"GitHub OAuth error: {err_msg}")

            github_access_token = token_data.get("access_token")
            if not github_access_token:
                raise AuthenticationError("No access token returned from GitHub.")

            # Fetch user profile
            user_resp = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {github_access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                    "User-Agent": "OpenReviewAI-App/1.0",
                },
            )

            if user_resp.status_code != 200:
                raise AuthenticationError(f"Failed to fetch GitHub user details: {user_resp.text}")

            gh_user = user_resp.json()
            github_id = gh_user.get("id")
            gh_login = gh_user.get("login")
            gh_name = gh_user.get("name") or gh_login
            gh_avatar = gh_user.get("avatar_url")
            gh_email = gh_user.get("email")

            # If user email is private, fetch primary verified email from /user/emails
            if not gh_email:
                emails_resp = await client.get(
                    "https://api.github.com/user/emails",
                    headers={
                        "Authorization": f"Bearer {github_access_token}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28",
                        "User-Agent": "OpenReviewAI-App/1.0",
                    },
                )
                if emails_resp.status_code == 200:
                    emails = emails_resp.json()
                    for em in emails:
                        if em.get("primary") and em.get("verified"):
                            gh_email = em.get("email")
                            break
                    if not gh_email and emails:
                        gh_email = emails[0].get("email")

            if not gh_email:
                gh_email = f"{gh_login}@users.noreply.github.com"

        # Check existing user in local database
        stmt = select(User).where(
            or_(User.github_id == github_id, User.email == gh_email)
        )
        user = (await self.session.execute(stmt)).scalar_one_or_none()

        if user:
            # Update user metadata
            user.github_id = github_id
            if gh_avatar:
                user.avatar_url = gh_avatar
            if gh_name and not user.full_name:
                user.full_name = gh_name
            user.is_active = True
            await self.session.commit()
            await self.session.refresh(user)
        else:
            # Generate collision-free username
            base_username = re.sub(r"[^a-zA-Z0-9_-]", "", gh_login)[:40]
            username = base_username
            counter = 1
            while (await self.session.execute(select(User).where(User.username == username))).scalar_one_or_none():
                username = f"{base_username[:35]}_{counter}"
                counter += 1

            user = User(
                email=gh_email,
                username=username,
                full_name=gh_name,
                avatar_url=gh_avatar,
                github_id=github_id,
                hashed_password=hash_password(f"github-oauth-{github_id}-{gh_login}"),
                is_active=True,
                is_superuser=False,
            )
            self.session.add(user)
            await self.session.flush()

            # Assign to organization
            org_stmt = select(Organization).limit(1)
            org = (await self.session.execute(org_stmt)).scalars().first()
            if not org:
                org = Organization(
                    name=f"{gh_name}'s Team",
                    slug=f"{username.lower()}-team",
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
            extra_claims={"email": user.email, "username": user.username, "github_id": user.github_id},
        )
        token = Token(access_token=token_str, expires_in=86400)
        return user, token
