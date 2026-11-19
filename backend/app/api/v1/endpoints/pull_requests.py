"""Pull Request Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.analyzer.schemas import PRAnalysisRequest, PRAnalysisResult
from app.analyzer.service import AnalyzerService
from app.core.dependencies import get_current_user_optional
from app.core.exceptions import NotFoundError
from app.database.session import get_db
from app.organizations.models import OrganizationMember
from app.pull_requests.models import PullRequest
from app.pull_requests.service import PullRequestService
from app.repositories.models import Repository
from app.reviews.models import Review
from app.schemas.pull_request import PullRequestCreate, PullRequestRead
from app.schemas.review import ReviewRead
from app.users.models import User

router = APIRouter(prefix="/pull-requests", tags=["Pull Requests"])


def get_pr_service(session: AsyncSession = Depends(get_db)) -> PullRequestService:
    return PullRequestService(session)


def get_analyzer_service(session: AsyncSession = Depends(get_db)) -> AnalyzerService:
    return AnalyzerService(session)


@router.get("", response_model=List[PullRequestRead], summary="List pull requests")
async def list_pull_requests(
    repository_id: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db),
) -> List[PullRequestRead]:
    if not current_user:
        return []

    # Get user's accessible organizations
    stmt_m = select(OrganizationMember.organization_id).where(OrganizationMember.user_id == current_user.id)
    user_org_ids = list((await session.execute(stmt_m)).scalars().all())
    if not user_org_ids:
        return []

    stmt_repos = select(Repository.id).where(Repository.organization_id.in_(user_org_ids))
    allowed_repo_ids = list((await session.execute(stmt_repos)).scalars().all())
    if not allowed_repo_ids:
        return []

    stmt = (
        select(PullRequest)
        .where(PullRequest.repository_id.in_(allowed_repo_ids))
        .order_by(PullRequest.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    if repository_id:
        if repository_id not in allowed_repo_ids:
            return []
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


@router.post(
    "/{pr_id}/analyze",
    response_model=PRAnalysisResult,
    summary="Trigger comprehensive Pull Request impact and risk analysis",
)
async def analyze_pull_request(
    pr_id: str,
    payload: Optional[PRAnalysisRequest] = None,
    service: AnalyzerService = Depends(get_analyzer_service),
) -> PRAnalysisResult:
    custom_diff = payload.raw_diff if payload else None
    return await service.analyze_pull_request(pull_request_id=pr_id, custom_diff=custom_diff)


@router.get(
    "/{pr_id}/analysis",
    response_model=PRAnalysisResult,
    summary="Get Pull Request impact, complexity, risk score, and review plan",
)
async def get_pull_request_analysis(
    pr_id: str,
    service: AnalyzerService = Depends(get_analyzer_service),
) -> PRAnalysisResult:
    return await service.analyze_pull_request(pull_request_id=pr_id)
