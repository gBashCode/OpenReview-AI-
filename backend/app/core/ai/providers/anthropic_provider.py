"""Anthropic Claude Model Provider Adapter."""

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

logger = get_logger("openreview.ai.anthropic")
settings = get_settings()

T = TypeVar("T", bound=BaseModel)

ANTHROPIC_API_BASE = "https://api.anthropic.com/v1"
ANTHROPIC_API_VERSION = "2023-06-01"


class AnthropicProvider(BaseLLMProvider):
    """Adapter for Anthropic models (Claude 3.7 Sonnet, Claude 3.5 Sonnet, Claude 3.5 Haiku)."""

    provider_name: str = "anthropic"
    default_model: str = "claude-3-5-sonnet"

    def __init__(self, api_key: Optional[str] = None, http_client: Optional[httpx.AsyncClient] = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self._client = http_client

    def _get_headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise AuthenticationError("ANTHROPIC_API_KEY is not configured in application settings.")
        return {
            "x-api-key": self.api_key,
            "anthropic-version": ANTHROPIC_API_VERSION,
            "Content-Type": "application/json",
        }

    def _format_messages(self, messages: List[LLMMessage]) -> Tuple[str, List[Dict[str, str]]]:
        system_prompts: List[str] = []
        chat_messages: List[Dict[str, str]] = []

        for m in messages:
            if m.role == MessageRole.SYSTEM:
                system_prompts.append(m.content)
            else:
                role = "assistant" if m.role == MessageRole.ASSISTANT else "user"
                chat_messages.append({"role": role, "content": m.content})

        if not chat_messages:
            chat_messages.append({"role": "user", "content": "Hello"})

        return "\n\n".join(system_prompts), chat_messages

    async def generate(
        self,
        messages: List[LLMMessage],
        config: Optional[ModelConfig] = None,
    ) -> LLMResponse:
        model = (config and config.model) or self.default_model
        temperature = (config and config.temperature) if config else 0.2
        max_tokens = (config and config.max_tokens) if config else 4096
        timeout = (config and config.timeout_seconds) if config else 60.0

        system_prompt, chat_msgs = self._format_messages(messages)
        payload: Dict[str, Any] = {
            "model": model,
            "messages": chat_msgs,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_prompt:
            payload["system"] = system_prompt
        if config and config.stop_sequences:
            payload["stop_sequences"] = config.stop_sequences

        start_time = time.perf_counter()
        client = self._client or httpx.AsyncClient(timeout=timeout)
        close_client = self._client is None

        try:
            res = await client.post(
                f"{ANTHROPIC_API_BASE}/messages",
                headers=self._get_headers(),
                json=payload,
            )

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self._handle_status_errors(res)

            data = res.json()
            content_blocks = data.get("content", [])
            content = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
            finish_reason = data.get("stop_reason", "stop")

            usage_data = data.get("usage", {})
            prompt_tokens = usage_data.get("input_tokens", 0)
            completion_tokens = usage_data.get("output_tokens", 0)
            total_tokens = prompt_tokens + completion_tokens

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
        model = (config and config.model) or self.default_model
        timeout = (config and config.timeout_seconds) if config else 60.0

        system_prompt, chat_msgs = self._format_messages(messages)
        schema = response_model.model_json_schema()

        # Enforce structured output via Anthropic Tool Use
        tool_name = f"record_{response_model.__name__.lower()}"
        payload: Dict[str, Any] = {
            "model": model,
            "messages": chat_msgs,
            "max_tokens": (config and config.max_tokens) if config else 4096,
            "temperature": (config and config.temperature) if config else 0.1,
            "tools": [
                {
                    "name": tool_name,
                    "description": f"Output structured information conforming to {response_model.__name__}",
                    "input_schema": schema,
                }
            ],
            "tool_choice": {"type": "tool", "name": tool_name},
        }
        if system_prompt:
            payload["system"] = system_prompt

        start_time = time.perf_counter()
        client = self._client or httpx.AsyncClient(timeout=timeout)
        close_client = self._client is None

        try:
            res = await client.post(
                f"{ANTHROPIC_API_BASE}/messages",
                headers=self._get_headers(),
                json=payload,
            )

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self._handle_status_errors(res)

            data = res.json()
            content_blocks = data.get("content", [])
            tool_input = None

            for block in content_blocks:
                if block.get("type") == "tool_use" and block.get("name") == tool_name:
                    tool_input = block.get("input", {})
                    break

            if tool_input is None:
                # Fallback: check if text block contains JSON
                for block in content_blocks:
                    if block.get("type") == "text":
                        text = block.get("text", "")
                        try:
                            tool_input = json.loads(text)
                            break
                        except Exception:
                            pass

            if tool_input is None:
                raise AppException(f"Anthropic response did not contain structured tool call output: {res.text}", status_code=502)

            raw_json = json.dumps(tool_input)
            try:
                parsed_instance = response_model.model_validate(tool_input)
            except Exception as val_err:
                logger.error(f"Anthropic schema validation failed: {val_err}\nInput: {tool_input}")
                raise AppException(
                    f"Anthropic output failed schema validation for {response_model.__name__}: {str(val_err)}",
                    status_code=502,
                )

            usage_data = data.get("usage", {})
            prompt_tokens = usage_data.get("input_tokens", 0)
            completion_tokens = usage_data.get("output_tokens", 0)
            total_tokens = prompt_tokens + completion_tokens

            usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )
            cost = self.calculate_cost(prompt_tokens, completion_tokens, model)

            return StructuredLLMResponse[T](
                data=parsed_instance,
                raw_content=raw_json,
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
        system_prompt, chat_msgs = self._format_messages(messages)
        payload: Dict[str, Any] = {
            "model": model,
            "messages": chat_msgs,
            "max_tokens": (config and config.max_tokens) if config else 4096,
            "stream": True,
        }
        if system_prompt:
            payload["system"] = system_prompt

        client = self._client or httpx.AsyncClient(timeout=60.0)
        close_client = self._client is None

        try:
            async with client.stream(
                "POST",
                f"{ANTHROPIC_API_BASE}/messages",
                headers=self._get_headers(),
                json=payload,
            ) as response:
                self._handle_status_errors(response)
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        try:
                            event = json.loads(data_str)
                            if event.get("type") == "content_block_delta":
                                delta = event.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    yield delta.get("text", "")
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
                error="ANTHROPIC_API_KEY is not configured.",
            )

        start = time.perf_counter()
        client = self._client or httpx.AsyncClient(timeout=10.0)
        close_client = self._client is None
        try:
            # Light ping with max_tokens=1
            payload = {
                "model": "claude-3-5-haiku",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "ping"}],
            }
            res = await client.post(f"{ANTHROPIC_API_BASE}/messages", headers=self._get_headers(), json=payload)
            latency = round((time.perf_counter() - start) * 1000, 2)
            if res.status_code == 200:
                return ProviderHealthStatus(
                    provider=self.provider_name,
                    status="healthy",
                    latency_ms=latency,
                    available_models=["claude-3-7-sonnet", "claude-3-5-sonnet", "claude-3-5-haiku"],
                )
            return ProviderHealthStatus(
                provider=self.provider_name,
                status="degraded" if res.status_code == 429 else "unavailable",
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
            raise AuthenticationError(f"Anthropic Authentication Failed: {response.text}")
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "unknown")
            raise AppException(f"Anthropic Rate Limit Exceeded. Retry-After: {retry_after}", status_code=429)
        elif response.status_code >= 500:
            raise AppException(f"Anthropic Service Error [{response.status_code}]: {response.text}", status_code=502)
        elif response.status_code != 200:
            raise AppException(f"Anthropic API Error [{response.status_code}]: {response.text}", status_code=response.status_code)
