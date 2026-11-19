"""Sentry SDK integration and error monitoring for FastAPI and Celery."""

from typing import Optional
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("openreview.sentry")
settings = get_settings()


def init_sentry() -> bool:
    """Initializes Sentry SDK with FastAPI, Celery, and SQLAlchemy integrations."""
    if not settings.SENTRY_DSN:
        logger.info("Sentry DSN not configured; error monitoring via Sentry is disabled.")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.celery import CeleryIntegration
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        def before_send(event, hint):
            """Sanitize sensitive headers and authorization parameters before shipping to Sentry."""
            if "request" in event:
                req = event["request"]
                if "headers" in req:
                    for sensitive in ("authorization", "cookie", "x-api-key"):
                        if sensitive in req["headers"]:
                            req["headers"][sensitive] = "[REDACTED]"
            return event

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.APP_ENV,
            release=f"{settings.APP_NAME}@0.1.0",
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=0.1 if settings.is_production else 0.0,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                CeleryIntegration(monitor_beat_tasks=True),
                SqlalchemyIntegration(),
            ],
            before_send=before_send,
            send_default_pii=False,
        )
        logger.info(f"Sentry initialized successfully for environment: {settings.APP_ENV}")
        return True

    except ImportError:
        logger.warning("sentry-sdk package not installed. Sentry initialization skipped.")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        return False
