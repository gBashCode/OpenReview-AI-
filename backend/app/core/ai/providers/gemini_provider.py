"""Google Gemini Model Provider Adapter."""

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

logger = get_logger("openreview.ai.gemini")
settings = get_settings()

T = TypeVar("T", bound=BaseModel)

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(BaseLLMProvider):
    """Adapter for Google Gemini models (Gemini 2.5 Flash, Gemini 2.5 Pro, Gemini 1.5 Pro)."""

    provider_name: str = "gemini"
    default_model: str = "gemini-2.5-flash"

    def __init__(self, api_key: Optional[str] = None, http_client: Optional[httpx.AsyncClient] = None):
        self.api_key = api_key or settings.GOOGLE_API_KEY
        self._client = http_client

    def _get_headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise AuthenticationError("GOOGLE_API_KEY is not configured in application settings.")
        return {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def _format_gemini_payload(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
        structured_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        system_parts = []
        contents = []

        for m in messages:
            if m.role == MessageRole.SYSTEM:
                system_parts.append({"text": m.content})
            else:
                role = "user" if m.role == MessageRole.USER else "model"
                contents.append({"role": role, "parts": [{"text": m.content}]})

        # Ensure at least one user content exists
        if not contents:
            contents.append({"role": "user", "parts": [{"text": "Hello"}]})

        gen_config: Dict[str, Any] = {
            "temperature": temperature,
            "maxOutputTokens": max_output_tokens,
        }

        if structured_schema:
            gen_config["responseMimeType"] = "application/json"
            # Optional: pass schema definition if supported
            gen_config["responseSchema"] = structured_schema

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": gen_config,
        }

        if system_parts:
            payload["systemInstruction"] = {"parts": system_parts}

        return payload

    async def generate(
        self,
        messages: List[LLMMessage],
        config: Optional[ModelConfig] = None,
    ) -> LLMResponse:
        model = (config and config.model) or self.default_model
        temperature = (config and config.temperature) if config else 0.2
        max_tokens = (config and config.max_tokens) if config else 4096
        timeout = (config and config.timeout_seconds) if config else 60.0

        payload = self._format_gemini_payload(
            messages=messages,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        start_time = time.perf_counter()
        client = self._client or httpx.AsyncClient(timeout=timeout)
        close_client = self._client is None

        try:
            url = f"{GEMINI_API_BASE}/{model}:generateContent"
            res = await client.post(url, headers=self._get_headers(), json=payload)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self._handle_status_errors(res)

            data = res.json()
            candidates = data.get("candidates", [])
            content = ""
            finish_reason = "stop"

            if candidates:
                cand = candidates[0]
                parts = cand.get("content", {}).get("parts", [])
                content = "".join(p.get("text", "") for p in parts)
                finish_reason = cand.get("finishReason", "stop")

            usage_meta = data.get("usageMetadata", {})
            prompt_tokens = usage_meta.get("promptTokenCount", 0)
            completion_tokens = usage_meta.get("candidatesTokenCount", 0)
            total_tokens = usage_meta.get("totalTokenCount", prompt_tokens + completion_tokens)

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

        schema = response_model.model_json_schema()
        payload = self._format_gemini_payload(
            messages=messages,
            temperature=(config and config.temperature) if config else 0.1,
            structured_schema=schema,
        )

        start_time = time.perf_counter()
        client = self._client or httpx.AsyncClient(timeout=timeout)
        close_client = self._client is None

        try:
            url = f"{GEMINI_API_BASE}/{model}:generateContent"
            res = await client.post(url, headers=self._get_headers(), json=payload)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self._handle_status_errors(res)

            data = res.json()
            candidates = data.get("candidates", [])
            raw_text = ""
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                raw_text = "".join(p.get("text", "") for p in parts)

            # Validate against Pydantic model
            try:
                parsed_instance = response_model.model_validate_json(raw_text)
            except Exception as val_err:
                logger.error(f"Gemini output failed validation: {val_err}\nRaw text: {raw_text}")
                raise AppException(
                    f"Gemini output failed schema validation for {response_model.__name__}: {str(val_err)}",
                    status_code=502,
                )

            usage_meta = data.get("usageMetadata", {})
            prompt_tokens = usage_meta.get("promptTokenCount", 0)
            completion_tokens = usage_meta.get("candidatesTokenCount", 0)
            total_tokens = usage_meta.get("totalTokenCount", prompt_tokens + completion_tokens)

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
        payload = self._format_gemini_payload(messages)

        client = self._client or httpx.AsyncClient(timeout=60.0)
        close_client = self._client is None

        try:
            url = f"{GEMINI_API_BASE}/{model}:streamGenerateContent?alt=sse"
            async with client.stream("POST", url, headers=self._get_headers(), json=payload) as response:
                self._handle_status_errors(response)
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        try:
                            chunk = json.loads(data_str)
                            cands = chunk.get("candidates", [])
                            if cands:
                                for part in cands[0].get("content", {}).get("parts", []):
                                    text = part.get("text", "")
                                    if text:
                                        yield text
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
                error="GOOGLE_API_KEY is not configured.",
            )

        start = time.perf_counter()
        client = self._client or httpx.AsyncClient(timeout=10.0)
        close_client = self._client is None
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}"
            res = await client.get(url)
            latency = round((time.perf_counter() - start) * 1000, 2)
            if res.status_code == 200:
                data = res.json()
                models = [m["name"].split("/")[-1] for m in data.get("models", []) if "gemini" in m["name"]][:5]
                return ProviderHealthStatus(
                    provider=self.provider_name,
                    status="healthy",
                    latency_ms=latency,
                    available_models=models,
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
        if response.status_code in (401, 403):
            raise AuthenticationError(f"Gemini Authentication Failed: {response.text}")
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "unknown")
            raise AppException(f"Gemini Rate Limit Exceeded. Retry-After: {retry_after}", status_code=429)
        elif response.status_code >= 500:
            raise AppException(f"Gemini Service Error [{response.status_code}]: {response.text}", status_code=502)
        elif response.status_code != 200:
            raise AppException(f"Gemini API Error [{response.status_code}]: {response.text}", status_code=response.status_code)
