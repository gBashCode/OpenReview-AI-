"""OpenAI Model Provider Adapter."""

import json
import time
from typing import Any, AsyncIterator, Dict, List, Optional, Type, TypeVar
import httpx
from pydantic import BaseModel

from app.core.ai.base import (
    BaseLLMProvider,
    LLMMessage,
    LLMResponse,
    MessageRole,
    ModelConfig,
    ProviderHealthStatus,
    StructuredLLMResponse,
    TokenUsage,
)
from app.core.ai.pricing import calculate_model_cost
from app.core.config import get_settings
from app.core.exceptions import AppException, AuthenticationError
from app.core.logging import get_logger

logger = get_logger("openreview.ai.openai")
settings = get_settings()

T = TypeVar("T", bound=BaseModel)

OPENAI_API_BASE = "https://api.openai.com/v1"


class OpenAIProvider(BaseLLMProvider):
    """Adapter for OpenAI models (GPT-4o, GPT-4o-mini, o1, o3-mini)."""

    provider_name: str = "openai"
    default_model: str = "gpt-4o-mini"

    def __init__(self, api_key: Optional[str] = None, http_client: Optional[httpx.AsyncClient] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self._client = http_client

    def _get_headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise AuthenticationError("OPENAI_API_KEY is not configured in application settings.")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _convert_messages(self, messages: List[LLMMessage]) -> List[Dict[str, str]]:
        formatted = []
        for m in messages:
            msg_dict = {"role": m.role.value, "content": m.content}
            if m.name:
                msg_dict["name"] = m.name
            formatted.append(msg_dict)
        return formatted

    async def generate(
        self,
        messages: List[LLMMessage],
        config: Optional[ModelConfig] = None,
    ) -> LLMResponse:
        model = (config and config.model) or self.default_model
        temperature = (config and config.temperature) if config else 0.2
        max_tokens = (config and config.max_tokens) if config else 4096
        timeout = (config and config.timeout_seconds) if config else 60.0

        payload: Dict[str, Any] = {
            "model": model,
            "messages": self._convert_messages(messages),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if config and config.stop_sequences:
            payload["stop"] = config.stop_sequences

        start_time = time.perf_counter()
        client = self._client or httpx.AsyncClient(timeout=timeout)
        close_client = self._client is None

        try:
            res = await client.post(
                f"{OPENAI_API_BASE}/chat/completions",
                headers=self._get_headers(),
                json=payload,
            )

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self._handle_status_errors(res)

            data = res.json()
            choice = data["choices"][0]
            content = choice["message"]["content"] or ""
            finish_reason = choice.get("finish_reason", "stop")

            usage_data = data.get("usage", {})
            prompt_tokens = usage_data.get("prompt_tokens", 0)
            completion_tokens = usage_data.get("completion_tokens", 0)
            total_tokens = usage_data.get("total_tokens", prompt_tokens + completion_tokens)

            usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )
            cost = self.calculate_cost(prompt_tokens, completion_tokens, model)

            return LLMResponse(
                content=content,
                provider=self.provider_name,
                model=model,
                usage=usage,
                cost_usd=cost,
                latency_ms=latency_ms,
                finish_reason=finish_reason,
            )
        finally:
            if close_client:
                await client.aclose()

    async def generate_structured(
        self,
        messages: List[LLMMessage],
        response_model: Type[T],
        config: Optional[ModelConfig] = None,
    ) -> StructuredLLMResponse[T]:
        """Generates completion and guarantees strict schema validation against response_model."""
        model = (config and config.model) or self.default_model
        timeout = (config and config.timeout_seconds) if config else 60.0

        schema = response_model.model_json_schema()
        payload: Dict[str, Any] = {
            "model": model,
            "messages": self._convert_messages(messages),
            "temperature": (config and config.temperature) if config else 0.1,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__,
                    "strict": True,
                    "schema": schema,
                },
            },
        }

        start_time = time.perf_counter()
        client = self._client or httpx.AsyncClient(timeout=timeout)
        close_client = self._client is None

        try:
            res = await client.post(
                f"{OPENAI_API_BASE}/chat/completions",
                headers=self._get_headers(),
                json=payload,
            )

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self._handle_status_errors(res)

            data = res.json()
            raw_text = data["choices"][0]["message"]["content"] or ""

            # Validate with Pydantic
            try:
                parsed_instance = response_model.model_validate_json(raw_text)
            except Exception as val_err:
                logger.error(f"Pydantic schema validation failed: {val_err}\nRaw output: {raw_text}")
                raise AppException(
                    f"Model output failed validation against {response_model.__name__}: {str(val_err)}",
                    status_code=502,
                )

            usage_data = data.get("usage", {})
            prompt_tokens = usage_data.get("prompt_tokens", 0)
            completion_tokens = usage_data.get("completion_tokens", 0)
            total_tokens = usage_data.get("total_tokens", prompt_tokens + completion_tokens)

            usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )
            cost = self.calculate_cost(prompt_tokens, completion_tokens, model)

            return StructuredLLMResponse[T](
                data=parsed_instance,
                raw_content=raw_text,
                provider=self.provider_name,
                model=model,
                usage=usage,
                cost_usd=cost,
                latency_ms=latency_ms,
            )
        finally:
            if close_client:
                await client.aclose()

    async def generate_stream(
        self,
        messages: List[LLMMessage],
        config: Optional[ModelConfig] = None,
    ) -> AsyncIterator[str]:
        model = (config and config.model) or self.default_model
        payload = {
            "model": model,
            "messages": self._convert_messages(messages),
            "stream": True,
        }

        client = self._client or httpx.AsyncClient(timeout=60.0)
        close_client = self._client is None

        try:
            async with client.stream(
                "POST",
                f"{OPENAI_API_BASE}/chat/completions",
                headers=self._get_headers(),
                json=payload,
            ) as response:
                self._handle_status_errors(response)
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        token_str = line[6:].strip()
                        if token_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(token_str)
                            delta = chunk["choices"][0].get("delta", {}).get("content", "")
                            if delta:
                                yield delta
                        except Exception:
                            continue
        finally:
            if close_client:
                await client.aclose()

    async def check_health(self) -> ProviderHealthStatus:
        if not self.api_key:
            return ProviderHealthStatus(
                provider=self.provider_name,
                status="unavailable",
                error="OPENAI_API_KEY is not configured.",
            )

        start = time.perf_counter()
        client = self._client or httpx.AsyncClient(timeout=10.0)
        close_client = self._client is None
        try:
            res = await client.get(f"{OPENAI_API_BASE}/models", headers=self._get_headers())
            latency = round((time.perf_counter() - start) * 1000, 2)
            if res.status_code == 200:
                data = res.json()
                model_ids = [m["id"] for m in data.get("data", []) if "gpt" in m["id"]][:5]
                return ProviderHealthStatus(
                    provider=self.provider_name,
                    status="healthy",
                    latency_ms=latency,
                    available_models=model_ids,
                )
            return ProviderHealthStatus(
                provider=self.provider_name,
                status="degraded" if res.status_code in (429, 503) else "unavailable",
                latency_ms=latency,
                error=f"HTTP {res.status_code}: {res.text}",
            )
        except Exception as exc:
            return ProviderHealthStatus(
                provider=self.provider_name,
                status="unavailable",
                error=str(exc),
            )
        finally:
            if close_client:
                await client.aclose()

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        return calculate_model_cost(self.provider_name, model, prompt_tokens, completion_tokens)

    def _handle_status_errors(self, response: httpx.Response):
        if response.status_code == 401:
            raise AuthenticationError(f"OpenAI Authentication Failed: {response.text}")
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "unknown")
            raise AppException(f"OpenAI Rate Limit Exceeded. Retry-After: {retry_after}", status_code=429)
        elif response.status_code >= 500:
            raise AppException(f"OpenAI Service Error [{response.status_code}]: {response.text}", status_code=502)
        elif response.status_code != 200:
            raise AppException(f"OpenAI API Error [{response.status_code}]: {response.text}", status_code=response.status_code)
