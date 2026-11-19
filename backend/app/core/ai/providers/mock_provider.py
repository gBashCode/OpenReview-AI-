"""Mock LLM Provider Adapter for Offline Testing and CI/CD Verification."""

import asyncio
import json
import time
from typing import Any, AsyncIterator, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

from app.core.ai.base import (
    BaseLLMProvider,
    LLMMessage,
    LLMResponse,
    ModelConfig,
    ProviderHealthStatus,
    StructuredLLMResponse,
    TokenUsage,
)
from app.core.ai.pricing import calculate_model_cost
from app.core.exceptions import AppException

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(BaseLLMProvider):
    """Deterministic mock provider that simulates LLM completions, structured JSON,
    streaming, timeouts, and rate limits without external network dependencies.
    """

    provider_name: str = "mock"
    default_model: str = "mock-model"

    def __init__(
        self,
        default_response: str = "Mock review evaluation completed successfully.",
        simulate_timeout: bool = False,
        simulate_rate_limit: bool = False,
        simulate_error: bool = False,
        structured_response_data: Optional[Dict[str, Any]] = None,
    ):
        self.default_response = default_response
        self.simulate_timeout = simulate_timeout
        self.simulate_rate_limit = simulate_rate_limit
        self.simulate_error = simulate_error
        self.structured_response_data = structured_response_data or {}
        self.call_count = 0

    async def generate(
        self,
        messages: List[LLMMessage],
        config: Optional[ModelConfig] = None,
    ) -> LLMResponse:
        self.call_count += 1
        start_time = time.perf_counter()

        if self.simulate_timeout:
            raise AppException("Mock provider simulated timeout after 60.0s", status_code=504)
        if self.simulate_rate_limit:
            raise AppException("Mock provider rate limit exceeded (429)", status_code=429)
        if self.simulate_error:
            raise AppException("Mock provider internal server error (500)", status_code=500)

        model = (config and config.model) or self.default_model
        latency_ms = round((time.perf_counter() - start_time) * 1000 + 5.0, 2)

        prompt_text = " ".join(m.content for m in messages)
        prompt_tokens = max(1, len(prompt_text) // 4)
        completion_tokens = max(1, len(self.default_response) // 4)
        usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )
        cost = self.calculate_cost(prompt_tokens, completion_tokens, model)

        return LLMResponse(
            content=self.default_response,
            provider=self.provider_name,
            model=model,
            usage=usage,
            cost_usd=cost,
            latency_ms=latency_ms,
            finish_reason="stop",
        )

    async def generate_structured(
        self,
        messages: List[LLMMessage],
        response_model: Type[T],
        config: Optional[ModelConfig] = None,
    ) -> StructuredLLMResponse[T]:
        self.call_count += 1
        start_time = time.perf_counter()

        if self.simulate_timeout:
            raise AppException("Mock provider simulated timeout", status_code=504)
        if self.simulate_rate_limit:
            raise AppException("Mock provider rate limit exceeded (429)", status_code=429)
        if self.simulate_error:
            raise AppException("Mock provider internal server error (500)", status_code=500)

        model = (config and config.model) or self.default_model

        # Build valid dummy data matching the Pydantic schema if not provided
        payload_dict = dict(self.structured_response_data)
        if not payload_dict:
            # Generate default values for schema fields
            for field_name, field_info in response_model.model_fields.items():
                annotation = field_info.annotation
                if annotation in (str, Optional[str]):
                    payload_dict[field_name] = f"Sample {field_name}"
                elif annotation in (int, Optional[int]):
                    payload_dict[field_name] = 10
                elif annotation in (float, Optional[float]):
                    payload_dict[field_name] = 95.0
                elif annotation in (bool, Optional[bool]):
                    payload_dict[field_name] = True
                elif getattr(annotation, "__origin__", None) in (list, List):
                    payload_dict[field_name] = []
                elif getattr(annotation, "__origin__", None) in (dict, Dict):
                    payload_dict[field_name] = {}
                else:
                    payload_dict[field_name] = None

        instance = response_model.model_validate(payload_dict)
        raw_json = instance.model_dump_json()

        latency_ms = round((time.perf_counter() - start_time) * 1000 + 8.0, 2)
        usage = TokenUsage(prompt_tokens=45, completion_tokens=55, total_tokens=100)
        cost = self.calculate_cost(45, 55, model)

        return StructuredLLMResponse[T](
            data=instance,
            raw_content=raw_json,
            provider=self.provider_name,
            model=model,
            usage=usage,
            cost_usd=cost,
            latency_ms=latency_ms,
        )

    async def generate_stream(
        self,
        messages: List[LLMMessage],
        config: Optional[ModelConfig] = None,
    ) -> AsyncIterator[str]:
        words = self.default_response.split(" ")
        for w in words:
            yield w + " "
            await asyncio.sleep(0.005)

    async def check_health(self) -> ProviderHealthStatus:
        if self.simulate_error or self.simulate_rate_limit:
            return ProviderHealthStatus(
                provider=self.provider_name,
                status="unavailable",
                error="Simulated health failure",
            )
        return ProviderHealthStatus(
            provider=self.provider_name,
            status="healthy",
            latency_ms=1.2,
            available_models=["mock-model", "mock-pro"],
        )

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        return calculate_model_cost(self.provider_name, model, prompt_tokens, completion_tokens)
