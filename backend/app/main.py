"""Main FastAPI Application Entrypoint for OpenReview AI.

Configures application lifecycle, CORS, routing, structured error handling,
and API versioning under /api/v1.
"""

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import get_logger, setup_logging
import app.models  # Ensure all 16 models are registered with Base.metadata
from app.database.base import Base
from app.database.session import check_db_connectivity, engine

settings = get_settings()
setup_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)
logger = get_logger("openreview.main")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware attaching a unique X-Request-ID to each incoming HTTP request."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        start_time = time.perf_counter()

        response = await call_next(request)

        duration = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration:.2f}ms"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan manager executing startup verification and graceful shutdown."""
    logger.info(f"Starting {settings.APP_NAME} in [{settings.APP_ENV}] mode...")

    # For local SQLite development, ensure tables are automatically generated
    if settings.is_sqlite:
        logger.info("Initializing database tables for local SQLite development...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # Verify backing database connectivity
    db_connected = await check_db_connectivity()
    if db_connected:
        logger.info(f"Database connectivity confirmed at {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'local'}")
    else:
        logger.warning(
            "Backing database is currently unreachable. Health checks will report degraded status."
        )

    yield

    logger.info(f"Shutting down {settings.APP_NAME}...")
    await engine.dispose()


def create_application() -> FastAPI:
    """Factory creating and configuring the primary FastAPI instance."""
    app = FastAPI(
        title=settings.APP_NAME,
        description="Autonomous Multi-Agent Code Review Platform API",
        version="0.1.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # Configure CORS securely
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time"],
    )

    # Context & Tracing middleware
    app.add_middleware(RequestContextMiddleware)

    # Register Exception Handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Mount versioned API routes (/api/v1)
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    # Root redirect / ping
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": "0.1.0",
            "status": "operational",
            "docs": "/docs" if settings.DEBUG else "disabled",
            "api_v1": settings.API_V1_PREFIX,
        }

    return app


app = create_application()
