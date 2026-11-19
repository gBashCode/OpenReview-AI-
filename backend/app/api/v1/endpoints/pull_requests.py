"""Pull Request Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError
from app.database.session import get_db
from app.pull_requests.models import PullRequest
from app.pull_requests.service import PullRequestService
from app.reviews.models import Review
from app.schemas.pull_request import PullRequestCreate, PullRequestRead
from app.schemas.review import ReviewRead

router = APIRouter(prefix="/pull-requests", tags=["Pull Requests"])


def get_pr_service(session: AsyncSession = Depends(get_db)) -> PullRequestService:
    return PullRequestService(session)


@router.get("", response_model=List[PullRequestRead], summary="List pull requests")
async def list_pull_requests(
    repository_id: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
) -> List[PullRequestRead]:
    stmt = select(PullRequest).order_by(PullRequest.updated_at.desc()).offset(skip).limit(limit)
    if repository_id:
        stmt = stmt.where(PullRequest.repository_id == repository_id)
    if state:
        stmt = stmt.where(PullRequest.state == state)
    result = await session.execute(stmt)
    return [PullRequestRead.model_validate(pr) for pr in result.scalars().all()]


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
    return PullRequestRead.model_validate(pr)


@router.get("/{pr_id}", response_model=PullRequestRead, summary="Get PR by ID")
async def get_pull_request(
    pr_id: str,
    session: AsyncSession = Depends(get_db),
) -> PullRequestRead:
    stmt = select(PullRequest).where(PullRequest.id == pr_id)
    pr = (await session.execute(stmt)).scalar_one_or_none()
    if not pr:
        raise NotFoundError("PullRequest", pr_id)
    return PullRequestRead.model_validate(pr)


@router.get("/{pr_id}/reviews", response_model=List[ReviewRead], summary="List reviews for PR")
async def list_pr_reviews(
    pr_id: str,
    session: AsyncSession = Depends(get_db),
) -> List[ReviewRead]:
    stmt = select(Review).where(Review.pull_request_id == pr_id).order_by(Review.created_at.desc())
    result = await session.execute(stmt)
    return [ReviewRead.model_validate(r) for r in result.scalars().all()]
