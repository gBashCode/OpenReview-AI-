"""Health and Readiness endpoints."""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from app.core.dependencies import get_health_service
from app.schemas.health import HealthCheckResponse
from app.services.health_service import HealthService

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=HealthCheckResponse,
    summary="Comprehensive service health evaluation",
)
async def get_health(
    service: HealthService = Depends(get_health_service),
) -> HealthCheckResponse:
    """Returns detailed health status across PostgreSQL, Redis, and backing components."""
    return await service.get_full_health()


@router.get(
    "/live",
    summary="Kubernetes / Docker liveness probe",
)
async def get_liveness():
    """Simple ping checking if the web process is running."""
    return {"status": "alive"}


@router.get(
    "/ready",
    summary="Kubernetes / Docker readiness probe",
)
async def get_readiness(
    service: HealthService = Depends(get_health_service),
):
    """Verifies backing database connectivity before routing user traffic."""
    db_health = await service.check_database()
    if db_health.status == "unhealthy":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "reason": db_health.message},
        )
    return {"status": "ready", "database": db_health.message}
