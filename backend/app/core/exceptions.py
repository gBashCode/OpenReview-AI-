"""Custom domain exception hierarchy and FastAPI exception handlers."""

from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.logging import get_logger

logger = get_logger("openreview.exceptions")


class AppException(Exception):
    """Base class for all application domain exceptions."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class NotFoundError(AppException):
    """Resource was not found."""

    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} with identifier '{identifier}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            details={"resource": resource, "identifier": str(identifier)},
        )


class ConflictError(AppException):
    """Resource already exists or operation conflicts with current state."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT",
            details=details,
        )


class ValidationError(AppException):
    """Business rule validation failure."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class AuthenticationError(AppException):
    """Invalid or missing credentials."""

    def __init__(self, message: str = "Authentication failed."):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED",
        )


class PermissionDeniedError(AppException):
    """Action forbidden for the authenticated user/token."""

    def __init__(self, message: str = "Access forbidden."):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN",
        )


class LLMProviderError(AppException):
    """Error communicating with an external LLM provider."""

    def __init__(self, provider: str, message: str):
        super().__init__(
            message=f"LLM Provider [{provider}] error: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="LLM_PROVIDER_ERROR",
            details={"provider": provider},
        )


class DatabaseConnectionError(AppException):
    """Database connectivity failure."""

    def __init__(self, message: str = "Database connection error"):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="DATABASE_UNAVAILABLE",
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handles domain exceptions thrown across business logic."""
    logger.warning(
        f"Domain exception {exc.error_code} on {request.method} {request.url.path}: {exc.message}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handles request body and query param validation errors."""
    errors = exc.errors()
    logger.warning(
        f"Validation error on {request.method} {request.url.path}: {len(errors)} issues"
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "REQUEST_VALIDATION_ERROR",
                "message": "Input validation failed. Please inspect the details.",
                "details": errors,
            }
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unexpected internal server errors."""
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {str(exc)}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal server error occurred.",
            }
        },
    )
