"""API v1 Router Aggregator."""

from fastapi import APIRouter
from app.api.v1.endpoints import health, pull_requests, repositories, reviews

api_v1_router = APIRouter()

api_v1_router.include_router(health.router)
api_v1_router.include_router(repositories.router)
api_v1_router.include_router(pull_requests.router)
api_v1_router.include_router(reviews.router)
