"""AI Model Infrastructure Package for OpenReview AI."""

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
from app.core.ai.gateway import ModelGateway, model_gateway
from app.core.ai.pricing import calculate_model_cost
from app.core.ai.prompt_manager import PromptManager, PromptTemplate, prompt_manager
from app.core.ai.providers import (
    AnthropicProvider,
    GeminiProvider,
    MockLLMProvider,
    OpenAIProvider,
)

__all__ = [
    "BaseLLMProvider",
    "LLMMessage",
    "LLMResponse",
    "MessageRole",
    "ModelConfig",
    "TokenUsage",
    "StructuredLLMResponse",
    "ProviderHealthStatus",
    "ModelGateway",
    "model_gateway",
    "calculate_model_cost",
    "PromptManager",
    "PromptTemplate",
    "prompt_manager",
    "OpenAIProvider",
    "GeminiProvider",
    "AnthropicProvider",
    "MockLLMProvider",
]
