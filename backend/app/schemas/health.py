"""Health check schemas."""

from typing import Dict, Literal, Optional
from pydantic import BaseModel, Field


class ComponentStatus(BaseModel):
    status: Literal["healthy", "unhealthy", "degraded"]
    latency_ms: Optional[float] = None
    message: Optional[str] = None


class HealthCheckResponse(BaseModel):
    status: Literal["healthy", "unhealthy", "degraded"]
    version: str
    environment: str
    timestamp: str
    components: Dict[str, ComponentStatus] = Field(default_factory=dict)
