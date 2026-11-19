"""Central Model Gateway with Resilient Retries, Token Budgeting, and Provider Fallback."""

import asyncio
import random
import time
from typing import Any, AsyncIterator, Dict, List, Optional, Type, TypeVar
import httpx
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
from app.core.ai.providers.anthropic_provider import AnthropicProvider
from app.core.ai.providers.gemini_provider import GeminiProvider
from app.core.ai.providers.mock_provider import MockLLMProvider
from app.core.ai.providers.openai_provider import OpenAIProvider
from app.core.config import get_settings
from app.core.exceptions import AppException, AuthenticationError
from app.core.logging import get_logger

logger = get_logger("openreview.ai.gateway")
settings = get_settings()

T = TypeVar("T", bound=BaseModel)


class ModelGateway:
    """Enterprise multi-provider AI model gateway with automatic retry policies,
    rate-limit backoff, token budgeting, and multi-model fallback failover.
    """

    def __init__(
        self,
        primary_provider: Optional[str] = None,
        fallback_provider: Optional[str] = None,
        token_budget: Optional[int] = None,
    ):
        self.primary_name = (primary_provider or settings.DEFAULT_LLM_PROVIDER).lower()
        self.fallback_name = (fallback_provider or settings.LLM_FALLBACK_PROVIDER or "").lower()
        self.token_budget = token_budget or settings.LLM_TOKEN_BUDGET

        # Cumulative accounting
        self.total_tokens_consumed = 0
        self.total_cost_accumulated_usd = 0.0

        # Provider registry
        self._providers: Dict[str, BaseLLMProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """Initializes provider adapters."""
        self._providers["openai"] = OpenAIProvider()
        self._providers["gemini"] = GeminiProvider()
        self._providers["anthropic"] = AnthropicProvider()
        self._providers["mock"] = MockLLMProvider()

    def register_provider(self, name: str, provider: BaseLLMProvider):
        """Allows injecting custom or mocked providers (crucial for unit tests)."""
        self._providers[name.lower()] = provider

    def get_provider(self, name: str) -> BaseLLMProvider:
        prov = self._providers.get(name.lower())
        if not prov:
            raise AppException(f"LLM Provider '{name}' is not registered in ModelGateway.", status_code=400)
        return prov

    async def generate(
        self,
        messages: List[LLMMessage],
        provider: Optional[str] = None,
        config: Optional[ModelConfig] = None,
    ) -> LLMResponse:
        """Executes text generation with exponential backoff retries and fallback failover."""
        target_provider_name = (provider or self.primary_name).lower()
        cfg = config or ModelConfig(
            temperature=settings.LLM_TEMPERATURE,
            timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
            max_retries=settings.LLM_RETRY_COUNT,
        )

        try:
            response = await self._execute_with_retry(
                provider_name=target_provider_name,
                messages=messages,
                config=cfg,
                is_structured=False,
            )
            self._record_usage(response.usage.total_tokens, response.cost_usd)
            return response
        except Exception as primary_exc:
            # Check if fallback provider is configured and distinct
            if self.fallback_name and self.fallback_name != target_provider_name and self.fallback_name in self._providers:
                logger.warning(
                    f"Primary provider '{target_provider_name}' failed ({primary_exc}). "
                    f"Attempting failover to fallback provider '{self.fallback_name}'..."
                )
                fallback_cfg = ModelConfig(
                    model=settings.LLM_FALLBACK_MODEL,
                    temperature=cfg.temperature,
                    timeout_seconds=cfg.timeout_seconds,
                    max_retries=cfg.max_retries,
                )
                try:
                    fallback_response = await self._execute_with_retry(
                        provider_name=self.fallback_name,
                        messages=messages,
                        config=fallback_cfg,
                        is_structured=False,
                    )
                    fallback_response.fallback_used = True
                    fallback_response.original_provider = target_provider_name
                    self._record_usage(fallback_response.usage.total_tokens, fallback_response.cost_usd)
                    return fallback_response
                except Exception as fb_exc:
                    logger.error(f"Fallback provider '{self.fallback_name}' also failed: {fb_exc}")
                    raise AppException(
                        f"All model providers failed. Primary ({target_provider_name}): {primary_exc} | Fallback ({self.fallback_name}): {fb_exc}",
                        status_code=502,
                    )
            raise primary_exc

    async def generate_structured(
        self,
        messages: List[LLMMessage],
        response_model: Type[T],
        provider: Optional[str] = None,
        config: Optional[ModelConfig] = None,
    ) -> StructuredLLMResponse[T]:
        """Executes structured generation with strict Pydantic validation and fallback."""
        target_provider_name = (provider or self.primary_name).lower()
        cfg = config or ModelConfig(
            temperature=settings.LLM_TEMPERATURE,
            timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
            max_retries=settings.LLM_RETRY_COUNT,
        )

        try:
            response = await self._execute_with_retry(
                provider_name=target_provider_name,
                messages=messages,
                config=cfg,
                is_structured=True,
                response_model=response_model,
            )
            self._record_usage(response.usage.total_tokens, response.cost_usd)
            return response
        except Exception as primary_exc:
            if self.fallback_name and self.fallback_name != target_provider_name and self.fallback_name in self._providers:
                logger.warning(
                    f"Primary provider '{target_provider_name}' structured call failed ({primary_exc}). "
                    f"Failing over to '{self.fallback_name}'..."
                )
                fallback_cfg = ModelConfig(
                    model=settings.LLM_FALLBACK_MODEL,
                    temperature=cfg.temperature,
                    timeout_seconds=cfg.timeout_seconds,
                    max_retries=cfg.max_retries,
                )
                try:
                    fb_res = await self._execute_with_retry(
                        provider_name=self.fallback_name,
                        messages=messages,
                        config=fallback_cfg,
                        is_structured=True,
                        response_model=response_model,
                    )
                    fb_res.fallback_used = True
                    fb_res.original_provider = target_provider_name
                    self._record_usage(fb_res.usage.total_tokens, fb_res.cost_usd)
                    return fb_res
                except Exception as fb_exc:
                    raise AppException(
                        f"Structured generation failed across providers. Primary: {primary_exc} | Fallback: {fb_exc}",
                        status_code=502,
                    )
            raise primary_exc

    async def generate_stream(
        self,
        messages: List[LLMMessage],
        provider: Optional[str] = None,
        config: Optional[ModelConfig] = None,
    ) -> AsyncIterator[str]:
        """Streams completion tokens from the specified provider."""
        prov_name = (provider or self.primary_name).lower()
        prov = self.get_provider(prov_name)
        async for chunk in prov.generate_stream(messages, config):
            yield chunk

    async def check_all_providers(self) -> Dict[str, ProviderHealthStatus]:
        """Executes health checks in parallel across all registered providers."""
        results: Dict[str, ProviderHealthStatus] = {}
        for name, prov in self._providers.items():
            results[name] = await prov.check_health()
        return results

    async def check_provider(self, name: str) -> ProviderHealthStatus:
        prov = self.get_provider(name)
        return await prov.check_health()

    async def _execute_with_retry(
        self,
        provider_name: str,
        messages: List[LLMMessage],
        config: ModelConfig,
        is_structured: bool = False,
        response_model: Optional[Type[T]] = None,
    ) -> Any:
        """Executes model call with exponential backoff jittered retry policies."""
        prov = self.get_provider(provider_name)
        max_retries = config.max_retries
        attempt = 0

        while True:
            try:
                if is_structured and response_model:
                    return await prov.generate_structured(messages, response_model, config)
                else:
                    return await prov.generate(messages, config)
            except Exception as exc:
                attempt += 1
                is_auth_error = isinstance(exc, AuthenticationError) or getattr(exc, "status_code", 0) == 401
                is_client_error = getattr(exc, "status_code", 0) in (400, 422)

                # Do not retry fatal client errors or authentication failures
                if is_auth_error or is_client_error or attempt > max_retries:
                    raise exc

                # Calculate exponential backoff with jitter
                delay = (0.5 * (2 ** (attempt - 1))) + random.uniform(0.1, 0.4)
                logger.warning(
                    f"[{provider_name}] Generation attempt {attempt}/{max_retries} failed ({exc}). Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)

    def _record_usage(self, tokens: int, cost: float):
        """Tracks token consumption against configured budget."""
        self.total_tokens_consumed += tokens
        self.total_cost_accumulated_usd += cost
        if self.token_budget and self.total_tokens_consumed > self.token_budget:
            logger.warning(
                f"Token budget exceeded! Consumed {self.total_tokens_consumed}/{self.token_budget} tokens."
            )


# Global singleton ModelGateway instance
model_gateway = ModelGateway()
