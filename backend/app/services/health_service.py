"""Health Check Service inspecting database, redis, and system health."""

import time
from datetime import datetime, timezone
import redis.asyncio as aioredis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.health import ComponentStatus, HealthCheckResponse

logger = get_logger("openreview.health")
settings = get_settings()


class HealthService:
    """Evaluates readiness and liveness of all backing services."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_database(self) -> ComponentStatus:
        start = time.perf_counter()
        try:
            await self.session.execute(text("SELECT 1"))
            latency = (time.perf_counter() - start) * 1000

            # Check pgvector if PostgreSQL
            message = "Connected"
            if not settings.is_sqlite:
                try:
                    result = await self.session.execute(
                        text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
                    )
                    has_vector = result.scalar_one_or_none()
                    if has_vector:
                        message += " (pgvector extension active)"
                except Exception:
                    pass

            return ComponentStatus(
                status="healthy",
                latency_ms=round(latency, 2),
                message=message,
            )
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return ComponentStatus(
                status="unhealthy",
                latency_ms=None,
                message=str(e),
            )

    async def check_redis(self) -> ComponentStatus:
        start = time.perf_counter()
        try:
            client = aioredis.from_url(
                settings.REDIS_URL,
                socket_connect_timeout=2.0,
                socket_timeout=2.0,
            )
            pong = await client.ping()
            await client.aclose()
            latency = (time.perf_counter() - start) * 1000

            if pong:
                return ComponentStatus(
                    status="healthy",
                    latency_ms=round(latency, 2),
                    message="PONG received",
                )
            return ComponentStatus(
                status="unhealthy",
                latency_ms=None,
                message="Unexpected ping response",
            )
        except Exception as e:
            # In local dev if Redis is not started yet, mark as degraded
            logger.info(f"Redis health check note: {e}")
            return ComponentStatus(
                status="degraded",
                latency_ms=None,
                message=f"Redis unavailable ({e.__class__.__name__})",
            )

    async def get_full_health(self) -> HealthCheckResponse:
        db_status = await self.check_database()
        redis_status = await self.check_redis()

        overall = "healthy"
        if db_status.status == "unhealthy":
            overall = "unhealthy"
        elif db_status.status == "degraded" or redis_status.status in ("degraded", "unhealthy"):
            overall = "degraded"

        return HealthCheckResponse(
            status=overall,
            version="0.1.0",
            environment=settings.APP_ENV,
            timestamp=datetime.now(timezone.utc).isoformat(),
            components={
                "database": db_status,
                "redis": redis_status,
            },
        )
