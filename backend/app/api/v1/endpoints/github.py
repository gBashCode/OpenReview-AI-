"""GitHub App Webhook, Installation Callback, and Repository Ingestion Endpoints."""

import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, Query, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.dependencies import get_current_user_optional
from app.core.exceptions import AuthenticationError, NotFoundError
from app.core.logging import get_logger
from app.database.session import get_db
from app.github.github_auth_service import GitHubAuthService
from app.github.github_pull_request_service import GitHubPullRequestService
from app.github.github_repository_service import GitHubRepositoryService
from app.github.github_webhook_service import GitHubWebhookService
from app.github.models import GitHubInstallation
from app.github.publishing_engine import GitHubReviewPublishingEngine
from app.github.schemas import (
    GitHubInstallationRead,
    GitHubPublishRequest,
    GitHubPublishResult,
    GitHubRepositoryItem,
)
from app.organizations.models import Organization, OrganizationMember
from app.repositories.schemas import RepositoryRead
from app.users.models import User

logger = get_logger("openreview.github.endpoints")
settings = get_settings()

router = APIRouter(prefix="/github", tags=["GitHub App"])


def get_webhook_service(session: AsyncSession = Depends(get_db)) -> GitHubWebhookService:
    return GitHubWebhookService(session)


def get_pr_service(session: AsyncSession = Depends(get_db)) -> GitHubPullRequestService:
    return GitHubPullRequestService(session)


def get_repo_service(session: AsyncSession = Depends(get_db)) -> GitHubRepositoryService:
    return GitHubRepositoryService(session)


@router.post("/webhook", summary="GitHub App Webhook Ingestion Endpoint")
async def github_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    x_github_event: Optional[str] = Header(None, alias="X-GitHub-Event"),
    x_github_delivery: Optional[str] = Header(None, alias="X-GitHub-Delivery"),
    webhook_service: GitHubWebhookService = Depends(get_webhook_service),
    pr_service: GitHubPullRequestService = Depends(get_pr_service),
) -> JSONResponse:
    """Ingests, authenticates, and dispatches incoming GitHub webhook events."""
    raw_body = await request.body()

    # 1. Verify HMAC-SHA256 signature
    is_valid = GitHubWebhookService.verify_signature(raw_body, x_hub_signature_256)
    if not is_valid:
        logger.warning("Rejected webhook delivery with invalid HMAC signature.")
        raise AuthenticationError("Invalid X-Hub-Signature-256 signature.")

    # 2. Idempotency & Deduplication
    if GitHubWebhookService.is_duplicate(x_github_delivery):
        logger.info(f"Duplicate webhook delivery [{x_github_delivery}] safely ignored.")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "duplicate_ignored", "delivery_id": x_github_delivery},
        )

    # 3. Parse JSON payload
    try:
        payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except Exception as exc:
        logger.error(f"Failed to parse webhook JSON payload: {exc}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Malformed JSON payload"},
        )

    logger.info(f"Received GitHub webhook event: [{x_github_event}] (action: {payload.get('action')})")

    # 4. Dispatch by event type
    if x_github_event == "ping":
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "pong", "zen": payload.get("zen")},
        )

    elif x_github_event == "pull_request":
        result = await pr_service.handle_pull_request_event(payload)
        return JSONResponse(status_code=status.HTTP_200_OK, content=result)

    elif x_github_event == "installation":
        result = await webhook_service.handle_installation_event(payload)
        return JSONResponse(status_code=status.HTTP_200_OK, content=result)

    elif x_github_event == "installation_repositories":
        result = await webhook_service.handle_installation_repositories_event(payload)
        return JSONResponse(status_code=status.HTTP_200_OK, content=result)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "acknowledged", "event": x_github_event},
    )


@router.get("/installations/connect", summary="Get GitHub App installation URL")
async def get_connect_url(state: Optional[str] = Query(None)) -> Dict[str, str]:
    """Provides the external redirect URL for installing the OpenReview AI GitHub App."""
    url = GitHubAuthService.get_installation_url(state=state)
    return {"installation_url": url}


@router.get("/installations/callback", summary="GitHub App installation redirect callback")
async def installation_callback(
    installation_id: int = Query(..., description="GitHub installation ID"),
    setup_action: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(get_current_user_optional),
    session: AsyncSession = Depends(get_db),
    repo_service: GitHubRepositoryService = Depends(get_repo_service),
) -> Dict[str, Any]:
    """Receives developer redirect from GitHub App post-install and syncs accessible repos."""
    logger.info(f"Processing installation callback for installation_id={installation_id}")

    # Determine organization
    org_id = None
    if current_user:
        stmt_m = select(OrganizationMember.organization_id).where(OrganizationMember.user_id == current_user.id)
        org_id = (await session.execute(stmt_m)).scalars().first()

    if not org_id:
        stmt_org = select(Organization.id).order_by(Organization.created_at)
        org_id = (await session.execute(stmt_org)).scalars().first()
        if not org_id:
            org = Organization(name="Primary Team", slug="primary-team", plan="team")
            session.add(org)
            await session.flush()
            org_id = org.id

    # Check or create installation in database
    stmt_inst = select(GitHubInstallation).where(GitHubInstallation.installation_id == installation_id)
    inst = (await session.execute(stmt_inst)).scalar_one_or_none()
    if not inst:
        inst = GitHubInstallation(
            organization_id=org_id,
            installation_id=installation_id,
            account_login=f"github-install-{installation_id}",
            account_type="Organization",
        )
        session.add(inst)
        await session.flush()

    # Synchronize repositories
    synced_repos = await repo_service.sync_installation_repositories(
        organization_id=org_id,
        installation_id=installation_id,
        installation_db_id=inst.id,
    )

    return {
        "status": "installed",
        "installation_id": installation_id,
        "organization_id": org_id,
        "synced_repositories_count": len(synced_repos),
        "repositories": [r.full_name for r in synced_repos],
    }


@router.get(
    "/installations",
    response_model=List[GitHubInstallationRead],
    summary="List active GitHub App installations",
)
async def list_installations(
    organization_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db),
) -> List[GitHubInstallationRead]:
    stmt = select(GitHubInstallation)
    if organization_id:
        stmt = stmt.where(GitHubInstallation.organization_id == organization_id)
    result = await session.execute(stmt)
    return [GitHubInstallationRead.model_validate(inst) for inst in result.scalars().all()]


@router.get(
    "/installations/{installation_id}/repositories",
    response_model=List[GitHubRepositoryItem],
    summary="List repositories accessible through an installation",
)
async def list_remote_repositories(
    installation_id: int,
    repo_service: GitHubRepositoryService = Depends(get_repo_service),
) -> List[GitHubRepositoryItem]:
    return await repo_service.list_installation_repositories(installation_id)


@router.post(
    "/installations/{installation_id}/sync",
    response_model=List[RepositoryRead],
    summary="Sync remote GitHub repositories for an installation",
)
async def sync_repositories(
    installation_id: int,
    organization_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db),
    repo_service: GitHubRepositoryService = Depends(get_repo_service),
) -> List[RepositoryRead]:
    stmt_inst = select(GitHubInstallation).where(GitHubInstallation.installation_id == installation_id)
    inst = (await session.execute(stmt_inst)).scalar_one_or_none()
    target_org_id = organization_id or (inst.organization_id if inst else None)

    if not target_org_id:
        stmt_org = select(Organization.id).order_by(Organization.created_at)
        target_org_id = (await session.execute(stmt_org)).scalars().first() or "default-org"

    synced = await repo_service.sync_installation_repositories(
        organization_id=target_org_id,
        installation_id=installation_id,
        installation_db_id=inst.id if inst else None,
    )
    return [RepositoryRead.model_validate(r) for r in synced]


@router.post(
    "/publish",
    response_model=GitHubPublishResult,
    summary="Publish verified findings, review summary, and check runs to target GitHub PR",
)
async def publish_github_review(
    payload: GitHubPublishRequest,
    session: AsyncSession = Depends(get_db),
) -> GitHubPublishResult:
    """Executes the GitHub Review Publishing Engine directly."""
    engine = GitHubReviewPublishingEngine(session=session)
    return await engine.publish_review(payload)

