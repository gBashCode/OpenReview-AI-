"""Pull Request Endpoints."""

from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.pull_request import PullRequest
from app.schemas.pull_request import PullRequestCreate, PullRequestRead
from app.schemas.review import ReviewRead
from app.services.review_service import ReviewService
from app.core.dependencies import get_review_service
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/pull-requests", tags=["Pull Requests"])


@router.get("", response_model=List[PullRequestRead], summary="List pull requests")
async def list_pull_requests(
    repository_id: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
) -> List[PullRequestRead]:
    query = select(PullRequest).order_by(PullRequest.updated_at.desc()).offset(skip).limit(limit)
    if repository_id:
        query = query.where(PullRequest.repository_id == repository_id)
    result = await session.execute(query)
    return list(result.scalars().all())


@router.post(
    "",
    response_model=PullRequestRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a pull request",
)
async def create_pull_request(
    payload: PullRequestCreate,
    session: AsyncSession = Depends(get_db),
) -> PullRequestRead:
    pr = PullRequest(
        repository_id=payload.repository_id,
        github_pr_id=payload.github_pr_id,
        pr_number=payload.pr_number,
        title=payload.title,
        description=payload.description,
        head_branch=payload.head_branch,
        base_branch=payload.base_branch,
        head_sha=payload.head_sha,
        base_sha=payload.base_sha,
        author_username=payload.author_username,
        state=payload.state,
    )
    session.add(pr)
    await session.commit()
    await session.refresh(pr)
    return pr


@router.get("/{pr_id}", response_model=PullRequestRead, summary="Get PR by ID")
async def get_pull_request(
    pr_id: str,
    session: AsyncSession = Depends(get_db),
) -> PullRequestRead:
    result = await session.execute(select(PullRequest).where(PullRequest.id == pr_id))
    pr = result.scalar_one_or_none()
    if not pr:
        raise NotFoundError("PullRequest", pr_id)
    return pr


@router.get("/{pr_id}/reviews", response_model=List[ReviewRead], summary="List reviews for PR")
async def list_pr_reviews(
    pr_id: str,
    service: ReviewService = Depends(get_review_service),
) -> List[ReviewRead]:
    return await service.list_reviews_for_pr(pr_id)
