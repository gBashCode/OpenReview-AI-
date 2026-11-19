"""Base Interfaces, Abstract Classes, and Data Models for LLM Providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Any, AsyncIterator, Dict, Generic, List, Optional, Type, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class LLMMessage(BaseModel):
    """Represents a standardized chat message across all model providers."""

    role: MessageRole
    content: str
    name: Optional[str] = None


class TokenUsage(BaseModel):
    """Token consumption accounting for request prompts and model completions."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ModelConfig(BaseModel):
    """Fine-grained execution parameters for model generation."""

    model: Optional[str] = None
    temperature: float = 0.2
    max_tokens: Optional[int] = 4096
    top_p: Optional[float] = None
    timeout_seconds: float = 60.0
    max_retries: int = 3
    stop_sequences: List[str] = Field(default_factory=list)
    stream: bool = False


class LLMResponse(BaseModel):
    """Standardized response from any model provider."""

    content: str
    provider: str
    model: str
    usage: TokenUsage
    cost_usd: float
    latency_ms: float
    finish_reason: Optional[str] = "stop"
    fallback_used: bool = False
    original_provider: Optional[str] = None


class StructuredLLMResponse(BaseModel, Generic[T]):
    """Standardized structured response parsed and validated against a Pydantic schema."""

    data: T
    raw_content: str
    provider: str
    model: str
    usage: TokenUsage
    cost_usd: float
    latency_ms: float
    fallback_used: bool = False
    original_provider: Optional[str] = None


class ProviderHealthStatus(BaseModel):
    """Health check outcome for an LLM provider."""

    provider: str
    status: str  # "healthy", "degraded", "unavailable"
    latency_ms: Optional[float] = None
    available_models: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class BaseLLMProvider(ABC):
    """Abstract Base Class for all model provider adapters."""

    provider_name: str
    default_model: str

    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        config: Optional[ModelConfig] = None,
    ) -> LLMResponse:
        """Generates completion text from chat messages."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        messages: List[LLMMessage],
        response_model: Type[T],
        config: Optional[ModelConfig] = None,
    ) -> StructuredLLMResponse[T]:
        """Generates structured output strictly validated against a Pydantic schema."""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: List[LLMMessage],
        config: Optional[ModelConfig] = None,
    ) -> AsyncIterator[str]:
        """Streams completion tokens asynchronously."""
        pass

    @abstractmethod
    async def check_health(self) -> ProviderHealthStatus:
        """Pings the provider API to evaluate connectivity and latency."""
        pass

    @abstractmethod
    def calculate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        """Calculates exact dollar cost based on model token pricing."""
        pass
