"""API v1 Router Aggregator."""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    ai,
    analytics,
    analyzer,
    auth,
    autofix,
    findings,
    github,
    health,
    organizations,
    pull_requests,
    repositories,
    reviews,
    users,
)

api_v1_router = APIRouter()

api_v1_router.include_router(health.router)
api_v1_router.include_router(ai.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(users.router)
api_v1_router.include_router(organizations.router)
api_v1_router.include_router(repositories.router)
api_v1_router.include_router(pull_requests.router)
api_v1_router.include_router(analyzer.router)
api_v1_router.include_router(reviews.router)
api_v1_router.include_router(findings.router)
api_v1_router.include_router(autofix.router)
api_v1_router.include_router(analytics.router)
api_v1_router.include_router(github.router)
