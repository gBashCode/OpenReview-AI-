"""OpenTelemetry (OTel) distributed tracing instrumentation."""

from typing import Optional
from fastapi import FastAPI
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("openreview.telemetry")
settings = get_settings()


def init_opentelemetry(app: Optional[FastAPI] = None) -> bool:
    """Configures OpenTelemetry TracerProvider, OTLP exporter, and automatic instrumentation."""
    if not settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        logger.info("OTEL_EXPORTER_OTLP_ENDPOINT not configured; OpenTelemetry tracing is disabled.")
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create(
            {
                SERVICE_NAME: "openreview-backend",
                SERVICE_VERSION: "0.1.0",
                "deployment.environment": settings.APP_ENV,
            }
        )

        provider = TracerProvider(resource=resource)
        otlp_exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True)
        processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

        # Instrument libraries
        HTTPXClientInstrumentor().instrument()
        SQLAlchemyInstrumentor().instrument()

        if app:
            FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)

        logger.info(f"OpenTelemetry tracing enabled with exporter: {settings.OTEL_EXPORTER_OTLP_ENDPOINT}")
        return True

    except ImportError:
        logger.warning("OpenTelemetry packages not installed. OTel initialization skipped.")
        return False
    except Exception as e:
        logger.error(f"OpenTelemetry initialization failed: {e}")
        return False
