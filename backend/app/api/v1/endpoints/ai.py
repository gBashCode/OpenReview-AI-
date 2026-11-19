"""AI Model Infrastructure and Provider Health API Endpoints."""

from typing import Any, Dict, List
from fastapi import APIRouter
from app.core.ai.base import ProviderHealthStatus
from app.core.ai.gateway import model_gateway
from app.core.ai.pricing import MODEL_PRICING
from app.core.ai.prompt_manager import prompt_manager
from app.core.config import get_settings

router = APIRouter(prefix="/ai", tags=["AI Model Infrastructure"])
settings = get_settings()


@router.get("/health", response_model=Dict[str, ProviderHealthStatus], summary="Check all AI provider health statuses")
async def check_ai_health() -> Dict[str, ProviderHealthStatus]:
    """Pings all registered AI providers to evaluate latency and connectivity."""
    return await model_gateway.check_all_providers()


@router.get("/models", summary="List supported models and pricing catalog")
async def list_models() -> Dict[str, Any]:
    """Returns available model providers, context lengths, and dollar pricing per 1M tokens."""
    return {
        "default_provider": settings.DEFAULT_LLM_PROVIDER,
        "default_model": settings.DEFAULT_MODEL,
        "fallback_provider": settings.LLM_FALLBACK_PROVIDER,
        "fallback_model": settings.LLM_FALLBACK_MODEL,
        "max_context_length": settings.LLM_MAX_CONTEXT_LENGTH,
        "pricing_per_million_tokens_usd": {
            model: {"prompt_price": p[0], "completion_price": p[1]}
            for model, p in MODEL_PRICING.items()
        },
    }


@router.get("/prompts", summary="List registered prompt templates")
async def list_prompts() -> List[Dict[str, Any]]:
    """Returns all registered agent prompt templates and their required variable parameters."""
    return [
        {
            "name": tmpl.name,
            "description": tmpl.description,
            "version": tmpl.version,
            "required_variables": tmpl.required_variables,
        }
        for tmpl in prompt_manager._templates.values()
    ]


@router.get("/usage", summary="Get cumulative AI token usage and estimated cost")
async def get_usage() -> Dict[str, Any]:
    """Returns cumulative token budget accounting for the active process."""
    return {
        "token_budget": model_gateway.token_budget,
        "total_tokens_consumed": model_gateway.total_tokens_consumed,
        "total_cost_usd": round(model_gateway.total_cost_accumulated_usd, 6),
        "budget_remaining": max(0, model_gateway.token_budget - model_gateway.total_tokens_consumed),
    }
