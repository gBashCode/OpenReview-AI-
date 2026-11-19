"""Repository Management Endpoints."""

from typing import List
from fastapi import APIRouter, Depends, Query, status
from app.core.dependencies import get_repository_service
from app.schemas.repository import (
    RepositoryCreate,
    RepositoryRead,
    RepositoryUpdate,
)
from app.services.repository_service import RepositoryService

router = APIRouter(prefix="/repositories", tags=["Repositories"])


@router.get("", response_model=List[RepositoryRead], summary="List connected repositories")
async def list_repositories(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: RepositoryService = Depends(get_repository_service),
) -> List[RepositoryRead]:
    return await service.list_repositories(skip=skip, limit=limit)


@router.post(
    "",
    response_model=RepositoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register repository for AI reviews",
)
async def register_repository(
    payload: RepositoryCreate,
    service: RepositoryService = Depends(get_repository_service),
) -> RepositoryRead:
    return await service.register_repository(payload)


@router.get("/{repository_id}", response_model=RepositoryRead, summary="Get repository by ID")
async def get_repository(
    repository_id: str,
    service: RepositoryService = Depends(get_repository_service),
) -> RepositoryRead:
    return await service.get_repository(repository_id)


@router.patch("/{repository_id}", response_model=RepositoryRead, summary="Update repository settings")
async def update_repository(
    repository_id: str,
    payload: RepositoryUpdate,
    service: RepositoryService = Depends(get_repository_service),
) -> RepositoryRead:
    return await service.update_repository(repository_id, payload)


@router.delete(
    "/{repository_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unlink repository",
)
async def delete_repository(
    repository_id: str,
    service: RepositoryService = Depends(get_repository_service),
) -> None:
    await service.delete_repository(repository_id)
