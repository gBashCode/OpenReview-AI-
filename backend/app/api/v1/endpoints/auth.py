"""Authentication API Endpoints."""

from typing import Any, Dict
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.schemas import LoginRequest, RegisterRequest, Token
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
    "/me",
    response_model=UserRead,
    summary="Get authenticated user profile",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    return UserRead.model_validate(current_user)
