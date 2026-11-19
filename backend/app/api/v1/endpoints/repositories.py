"""Repository Management API Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import PaginationParams, get_current_user_optional
from app.database.session import get_db
from app.indexing.models import RepositoryIndex
from app.indexing.schemas import (
    ArchitectureSummaryResponse,
    ContextRetrievalRequest,
    PRContextEvidenceResponse,
    RelatedFilesResponse,
    RepositoryIndexCreate,
    RepositoryIndexRead,
    SemanticSearchRequest,
    SemanticSearchResult,
    SymbolSearchResult,
)
from app.indexing.service import IndexingService
from app.organizations.models import Organization
from app.repositories.models import Repository
from app.repositories.schemas import RepositoryCreate, RepositoryRead, RepositoryUpdate
from app.repositories.service import RepositoryService
from app.users.models import User

router = APIRouter(prefix="/repositories", tags=["Repositories"])


def get_repo_service(session: AsyncSession = Depends(get_db)) -> RepositoryService:
    return RepositoryService(session)


def get_index_service(session: AsyncSession = Depends(get_db)) -> IndexingService:
    return IndexingService(session)


@router.get("", response_model=List[RepositoryRead], summary="List repositories")
async def list_repositories(
    organization_id: Optional[str] = Header(None, alias="X-Organization-ID"),
    query_org_id: Optional[str] = Query(None, alias="organization_id"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    repo_service: RepositoryService = Depends(get_repo_service),
) -> List[RepositoryRead]:
    target_org_id = organization_id or query_org_id
    if target_org_id:
        repos, _ = await repo_service.list_by_organization(
            organization_id=target_org_id,
            skip=skip,
            limit=limit,
        )
        return [RepositoryRead.model_validate(r) for r in repos]

    # Global/Tenant query fallback
    stmt = select(Repository).order_by(Repository.full_name).offset(skip).limit(limit)
    res = await session.execute(stmt)
    return [RepositoryRead.model_validate(r) for r in res.scalars().all()]


@router.post(
    "",
    response_model=RepositoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register repository for AI reviews",
)
async def register_repository(
    payload: RepositoryCreate,
    current_user: Optional[User] = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db),
    repo_service: RepositoryService = Depends(get_repo_service),
) -> RepositoryRead:
    # Ensure repository is tied to an organization
    if not payload.organization_id:
        # Find user's organization or first available
        stmt_org = select(Organization).order_by(Organization.created_at)
        org = (await session.execute(stmt_org)).scalars().first()
        if not org:
            org = Organization(
                name="Default Team",
                slug="default-team",
                plan="team",
            )
            session.add(org)
            await session.flush()
        payload.organization_id = org.id

    repo = await repo_service.create(payload)
    return RepositoryRead.model_validate(repo)


@router.get("/{repository_id}", response_model=RepositoryRead, summary="Get repository by ID")
async def get_repository(
    repository_id: str,
    repo_service: RepositoryService = Depends(get_repo_service),
) -> RepositoryRead:
    repo = await repo_service.get_by_id(repository_id)
    return RepositoryRead.model_validate(repo)


@router.patch("/{repository_id}", response_model=RepositoryRead, summary="Update repository settings")
async def update_repository(
    repository_id: str,
    payload: RepositoryUpdate,
    repo_service: RepositoryService = Depends(get_repo_service),
) -> RepositoryRead:
    repo = await repo_service.update(repository_id, payload)
    return RepositoryRead.model_validate(repo)


@router.delete(
    "/{repository_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unlink repository",
)
async def delete_repository(
    repository_id: str,
    repo_service: RepositoryService = Depends(get_repo_service),
) -> None:
    await repo_service.delete(repository_id)


@router.get(
    "/{repository_id}/indexes",
    response_model=List[RepositoryIndexRead],
    summary="List code symbol indexes for repository",
)
async def list_repository_indexes(
    repository_id: str,
    index_service: IndexingService = Depends(get_index_service),
) -> List[RepositoryIndexRead]:
    indexes = await index_service.list_by_repository(repository_id)
    return [RepositoryIndexRead.model_validate(idx) for idx in indexes]


@router.post(
    "/{repository_id}/indexes",
    response_model=RepositoryIndexRead,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger semantic code indexing and symbol extraction",
)
async def trigger_indexing(
    repository_id: str,
    payload: RepositoryIndexCreate,
    index_service: IndexingService = Depends(get_index_service),
) -> RepositoryIndexRead:
    payload.repository_id = repository_id
    index_record = await index_service.trigger_index(payload)
    return RepositoryIndexRead.model_validate(index_record)


@router.get(
    "/{repository_id}/indexes/{index_id}",
    response_model=RepositoryIndexRead,
    summary="Get status and details of a specific index pass",
)
async def get_index_details(
    repository_id: str,
    index_id: str,
    index_service: IndexingService = Depends(get_index_service),
) -> RepositoryIndexRead:
    index = await index_service.get_by_id(index_id)
    return RepositoryIndexRead.model_validate(index)


@router.get(
    "/{repository_id}/symbols",
    response_model=List[SymbolSearchResult],
    summary="Search code symbols (functions, classes, interfaces)",
)
async def search_symbols(
    repository_id: str,
    query: str = Query(..., min_length=1, description="Symbol name or prefix"),
    kind: Optional[str] = Query(None, description="Symbol kind filter (function, class, method, etc.)"),
    file_path: Optional[str] = Query(None, description="Optional file path filter"),
    limit: int = Query(20, ge=1, le=100),
    index_service: IndexingService = Depends(get_index_service),
) -> List[SymbolSearchResult]:
    return await index_service.search_symbols(
        repository_id=repository_id,
        query=query,
        kind=kind,
        file_path=file_path,
        limit=limit,
    )


@router.post(
    "/{repository_id}/search",
    response_model=List[SemanticSearchResult],
    summary="Semantic vector search over repository code chunks",
)
async def search_code_semantic(
    repository_id: str,
    payload: SemanticSearchRequest,
    index_service: IndexingService = Depends(get_index_service),
) -> List[SemanticSearchResult]:
    return await index_service.search_semantic(
        repository_id=repository_id,
        query=payload.query,
        top_k=payload.top_k,
        min_similarity=payload.min_similarity,
    )


@router.post(
    "/{repository_id}/context",
    response_model=PRContextEvidenceResponse,
    summary="Hybrid context retrieval for pull request code review",
)
async def retrieve_pr_context(
    repository_id: str,
    payload: ContextRetrievalRequest,
    index_service: IndexingService = Depends(get_index_service),
) -> PRContextEvidenceResponse:
    return await index_service.retrieve_pr_context(
        repository_id=repository_id,
        changed_files=payload.changed_files,
        top_k_semantic=payload.top_k_semantic,
    )


@router.get(
    "/{repository_id}/architecture",
    response_model=ArchitectureSummaryResponse,
    summary="Get repository architecture and framework summary",
)
async def get_architecture_summary(
    repository_id: str,
    index_service: IndexingService = Depends(get_index_service),
) -> ArchitectureSummaryResponse:
    return await index_service.get_architecture_summary(repository_id)


@router.get(
    "/{repository_id}/related-files",
    response_model=RelatedFilesResponse,
    summary="Get related dependencies, dependents, and tests for a file",
)
async def get_related_files(
    repository_id: str,
    file_path: str = Query(..., description="Target file path in repository"),
    index_service: IndexingService = Depends(get_index_service),
) -> RelatedFilesResponse:
    return await index_service.get_related_files(repository_id=repository_id, file_path=file_path)

