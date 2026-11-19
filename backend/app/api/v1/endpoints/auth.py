"""Authentication API Endpoints."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.schemas import (
    GitHubOAuthCallbackRequest,
    GitHubOAuthURLResponse,
    GoogleOAuthCallbackRequest,
    GoogleOAuthURLResponse,
    LoginRequest,
    RegisterRequest,
    Token,
)
from app.auth.service import AuthService
from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.users.models import User
from app.users.schemas import UserRead

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(session)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user and organization",
)
async def register(
    payload: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> Dict[str, Any]:
    user, token = await service.register(payload)
    return {
        "user": UserRead.model_validate(user),
        "token": token,
    }


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    summary="Authenticate with email and password",
)
async def login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> Dict[str, Any]:
    user, token = await service.login(payload)
    return {
        "user": UserRead.model_validate(user),
        "token": token,
    }


@router.get(
    "/github/url",
    response_model=GitHubOAuthURLResponse,
    summary="Get GitHub OAuth authorize URL",
)
async def get_github_oauth_url(
    redirect_uri: Optional[str] = Query(None, description="Frontend callback URL"),
    state: Optional[str] = Query(None, description="CSRF state"),
) -> GitHubOAuthURLResponse:
    """Returns the URL to redirect the user to GitHub for OAuth authorization."""
    url = AuthService.get_github_oauth_url(redirect_uri=redirect_uri, state=state)
    return GitHubOAuthURLResponse(url=url)


@router.post(
    "/github/callback",
    status_code=status.HTTP_200_OK,
    summary="Exchange GitHub OAuth code for JWT session",
)
async def github_oauth_callback(
    payload: GitHubOAuthCallbackRequest,
    service: AuthService = Depends(get_auth_service),
) -> Dict[str, Any]:
    """Exchanges an authorization code from GitHub for an active user session and JWT."""
    user, token = await service.authenticate_github_code(
        code=payload.code,
        redirect_uri=payload.redirect_uri,
    )
    return {
        "user": UserRead.model_validate(user),
        "token": token,
    }


@router.get(
    "/github/callback",
    summary="Browser redirect handler for GitHub OAuth",
)
async def github_oauth_redirect(
    code: str = Query(..., description="Authorization code from GitHub"),
    state: Optional[str] = Query(None),
    service: AuthService = Depends(get_auth_service),
) -> RedirectResponse:
    """Handles direct browser callback from GitHub and redirects to frontend with token."""
    user, token = await service.authenticate_github_code(code=code)
    frontend_url = f"http://localhost:5173/auth/callback?token={token.access_token}"
    return RedirectResponse(url=frontend_url)


@router.get(
    "/google/url",
    response_model=GoogleOAuthURLResponse,
    summary="Get Google OAuth authorize URL",
)
async def get_google_oauth_url(
    redirect_uri: Optional[str] = Query(None, description="Frontend callback URL"),
    state: Optional[str] = Query(None, description="CSRF state"),
) -> GoogleOAuthURLResponse:
    """Returns the URL to redirect the user to Google for OAuth authorization."""
    url = AuthService.get_google_oauth_url(redirect_uri=redirect_uri, state=state)
    return GoogleOAuthURLResponse(url=url)


@router.post(
    "/google/callback",
    status_code=status.HTTP_200_OK,
    summary="Exchange Google OAuth code for JWT session",
)
async def google_oauth_callback(
    payload: GoogleOAuthCallbackRequest,
    service: AuthService = Depends(get_auth_service),
) -> Dict[str, Any]:
    """Exchanges an authorization code from Google for an active user session and JWT."""
    user, token = await service.authenticate_google_code(
        code=payload.code,
        redirect_uri=payload.redirect_uri,
    )
    return {
        "user": UserRead.model_validate(user),
        "token": token,
    }


@router.get(
    "/google/callback",
    summary="Browser redirect handler for Google OAuth",
)
async def google_oauth_redirect(
    code: str = Query(..., description="Authorization code from Google"),
    state: Optional[str] = Query(None),
    service: AuthService = Depends(get_auth_service),
) -> RedirectResponse:
    """Handles direct browser callback from Google and redirects to frontend with token."""
    user, token = await service.authenticate_google_code(code=code)
    frontend_url = f"http://localhost:5173/auth/callback?token={token.access_token}"
    return RedirectResponse(url=frontend_url)


@router.post(
    "/demo",
    status_code=status.HTTP_200_OK,
    summary="Establish a 1-click sandbox demo session",
)
async def demo_login(
    service: AuthService = Depends(get_auth_service),
) -> Dict[str, Any]:
    """Establishes an isolated sandbox demo session with verified demo credentials."""
    user, token = await service.create_demo_session()
    return {
        "user": UserRead.model_validate(user),
        "token": token,
    }


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get authenticated user profile",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    return UserRead.model_validate(current_user)

