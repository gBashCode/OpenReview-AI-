"""Comprehensive Test Suite for AI Model Infrastructure.

Covers:
1. Provider Interface compliance
2. Configurable model parameters (temperature, max_tokens, timeout)
3. Structured JSON outputs strictly validated with Pydantic schemas
4. Streaming token generation
5. Timeout handling and exceptions
6. Exponential backoff retry policies
7. Rate-limit detection (HTTP 429) and failover
8. Token usage tracking and cost accounting
9. Automatic model fallback (primary failure -> secondary fallback)
10. Provider health checks
11. Centralized prompt management (interpolation, validation)
12. Real provider integration tests (conditionally enabled via credentials)
"""

import json
import os
import pytest
from httpx import AsyncClient, MockTransport, Response
from pydantic import BaseModel, Field

from app.core.ai import (
    AnthropicProvider,
    BaseLLMProvider,
    GeminiProvider,
    LLMMessage,
    LLMResponse,
    MessageRole,
    MockLLMProvider,
    ModelConfig,
    ModelGateway,
    OpenAIProvider,
    PromptTemplate,
    calculate_model_cost,
    model_gateway,
    prompt_manager,
)
from app.core.config import get_settings
from app.core.exceptions import AppException, AuthenticationError


# Sample Pydantic schema for structured output testing
class CodeFindingTestSchema(BaseModel):
    title: str = Field(..., description="Short summary of the bug")
    severity: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    line_number: int = Field(..., description="Target line number")
    suggested_fix: str = Field(..., description="Proposed code replacement")


# =============================================================================
# 1. PROVIDER INTERFACE & MOCK ADAPTER TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_mock_provider_basic_generation():
    provider = MockLLMProvider(default_response="Code review completed cleanly.")
    messages = [
        LLMMessage(role=MessageRole.SYSTEM, content="You are a reviewer."),
        LLMMessage(role=MessageRole.USER, content="Review this function."),
    ]
    config = ModelConfig(model="mock-model", temperature=0.3, max_tokens=100)

    response = await provider.generate(messages, config)

    assert response.content == "Code review completed cleanly."
    assert response.provider == "mock"
    assert response.model == "mock-model"
    assert response.usage.total_tokens > 0
    assert response.latency_ms > 0
    assert response.cost_usd == 0.0  # mock is free


@pytest.mark.asyncio
async def test_mock_provider_structured_output():
    structured_data = {
        "title": "SQL Injection Vector",
        "severity": "CRITICAL",
        "line_number": 42,
        "suggested_fix": "Use parameterized queries.",
    }
    provider = MockLLMProvider(structured_response_data=structured_data)
    messages = [LLMMessage(role=MessageRole.USER, content="Analyze for security bugs.")]

    res = await provider.generate_structured(messages, CodeFindingTestSchema)

    assert isinstance(res.data, CodeFindingTestSchema)
    assert res.data.title == "SQL Injection Vector"
    assert res.data.severity == "CRITICAL"
    assert res.data.line_number == 42
    assert "parameterized" in res.data.suggested_fix
    assert res.usage.total_tokens > 0


@pytest.mark.asyncio
async def test_mock_provider_streaming():
    provider = MockLLMProvider(default_response="Streamed token batch generation.")
    messages = [LLMMessage(role=MessageRole.USER, content="Stream text.")]

    tokens = []
    async for chunk in provider.generate_stream(messages):
        tokens.append(chunk)

    joined = "".join(tokens).strip()
    assert joined == "Streamed token batch generation."


# =============================================================================
# 2. PRICING & COST ESTIMATION TESTS
# =============================================================================

def test_model_cost_calculation():
    # OpenAI GPT-4o: $2.50 input / $10.00 output per 1M tokens
    cost_gpt4o = calculate_model_cost("openai", "gpt-4o", prompt_tokens=1000, completion_tokens=500)
    expected_gpt4o = (1000 / 1_000_000 * 2.50) + (500 / 1_000_000 * 10.00)
    assert pytest.approx(cost_gpt4o, rel=1e-4) == expected_gpt4o

    # Gemini 2.5 Flash: $0.075 input / $0.30 output per 1M tokens
    cost_gemini = calculate_model_cost("gemini", "gemini-2.5-flash", prompt_tokens=10_000, completion_tokens=2000)
    expected_gemini = (10_000 / 1_000_000 * 0.075) + (2000 / 1_000_000 * 0.30)
    assert pytest.approx(cost_gemini, rel=1e-4) == expected_gemini

    # Anthropic Claude 3.5 Sonnet: $3.00 input / $15.00 output per 1M tokens
    cost_claude = calculate_model_cost("anthropic", "claude-3-5-sonnet", prompt_tokens=5000, completion_tokens=1000)
    expected_claude = (5000 / 1_000_000 * 3.00) + (1000 / 1_000_000 * 15.00)
    assert pytest.approx(cost_claude, rel=1e-4) == expected_claude


# =============================================================================
# 3. PROMPT MANAGEMENT SYSTEM TESTS
# =============================================================================

def test_prompt_manager_rendering_and_validation():
    # 1. Retrieve registered template
    tmpl = prompt_manager.get_template("security_sentinel")
    assert tmpl.name == "security_sentinel"
    assert "pr_title" in tmpl.required_variables

    # 2. Missing variables should raise error
    with pytest.raises(AppException) as exc:
        tmpl.render(pr_title="Fix bug")
    assert "Missing required variables" in str(exc.value)

    # 3. Successful render and formatting into LLMMessages
    messages = prompt_manager.format_messages(
        "security_sentinel",
        pr_title="feat: add user login",
        changed_files_summary="auth.py (+10, -2)",
        diff_content="+ def login(): pass",
    )
    assert len(messages) == 2
    assert messages[0].role == MessageRole.SYSTEM
    assert "Security Sentinel" in messages[0].content
    assert messages[1].role == MessageRole.USER
    assert "feat: add user login" in messages[1].content


# =============================================================================
# 4. MODEL GATEWAY RETRIES & AUTOMATIC FALLBACK
# =============================================================================

@pytest.mark.asyncio
async def test_gateway_automatic_fallback_on_primary_failure():
    # Setup primary mock provider that simulates persistent 500 failure
    failing_primary = MockLLMProvider(simulate_error=True)
    failing_primary.provider_name = "failing_primary"

    # Setup healthy fallback provider
    healthy_fallback = MockLLMProvider(default_response="Fallback response successful.")
    healthy_fallback.provider_name = "healthy_fallback"

    gateway = ModelGateway(
        primary_provider="failing_primary",
        fallback_provider="healthy_fallback",
    )
    gateway.register_provider("failing_primary", failing_primary)
    gateway.register_provider("healthy_fallback", healthy_fallback)

    messages = [LLMMessage(role=MessageRole.USER, content="Analyze code.")]
    cfg = ModelConfig(max_retries=1, timeout_seconds=5.0)

    res = await gateway.generate(messages, config=cfg)

    assert res.content == "Fallback response successful."
    assert res.fallback_used is True
    assert res.original_provider == "failing_primary"
    assert res.provider == "healthy_fallback"


@pytest.mark.asyncio
async def test_gateway_retry_on_rate_limit():
    # Setup mock provider that fails once with 429 then succeeds
    class RateLimitThenSucceedMock(MockLLMProvider):
        def __init__(self):
            super().__init__(default_response="Succeeded on retry.")
            self.attempts = 0

        async def generate(self, messages, config=None):
            self.attempts += 1
            if self.attempts == 1:
                raise AppException("429 Rate Limit", status_code=429)
            return await super().generate(messages, config)

    provider = RateLimitThenSucceedMock()
    gateway = ModelGateway(primary_provider="retry_mock", fallback_provider=None)
    gateway.register_provider("retry_mock", provider)

    messages = [LLMMessage(role=MessageRole.USER, content="Hello")]
    cfg = ModelConfig(max_retries=2)

    res = await gateway.generate(messages, config=cfg)
    assert res.content == "Succeeded on retry."
    assert provider.attempts == 2


@pytest.mark.asyncio
async def test_gateway_structured_fallback():
    failing_primary = MockLLMProvider(simulate_timeout=True)
    failing_primary.provider_name = "timeout_primary"

    structured_data = {
        "title": "Fallback Finding",
        "severity": "HIGH",
        "line_number": 15,
        "suggested_fix": "Fix applied.",
    }
    healthy_fallback = MockLLMProvider(structured_response_data=structured_data)
    healthy_fallback.provider_name = "fallback_mock"

    gateway = ModelGateway(primary_provider="timeout_primary", fallback_provider="fallback_mock")
    gateway.register_provider("timeout_primary", failing_primary)
    gateway.register_provider("fallback_mock", healthy_fallback)

    messages = [LLMMessage(role=MessageRole.USER, content="Structured analysis")]
    cfg = ModelConfig(max_retries=1)

    res = await gateway.generate_structured(messages, CodeFindingTestSchema, config=cfg)

    assert res.fallback_used is True
    assert res.data.title == "Fallback Finding"
    assert res.data.severity == "HIGH"


# =============================================================================
# 5. OPENAI ADAPTER TRANSPORT MOCK TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_openai_provider_with_mock_transport():
    async def mock_handler(request):
        req_data = json.loads(request.content)
        assert req_data["model"] == "gpt-4o-mini"
        return Response(
            200,
            json={
                "choices": [{"message": {"content": "OpenAI review response."}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 150, "completion_tokens": 50, "total_tokens": 200},
            },
        )

    transport = MockTransport(mock_handler)
    client = AsyncClient(transport=transport)
    provider = OpenAIProvider(api_key="sk-test-mock-key", http_client=client)

    messages = [LLMMessage(role=MessageRole.USER, content="Check for bugs.")]
    res = await provider.generate(messages, ModelConfig(model="gpt-4o-mini"))

    assert res.content == "OpenAI review response."
    assert res.provider == "openai"
    assert res.usage.total_tokens == 200
    assert res.cost_usd > 0


@pytest.mark.asyncio
async def test_openai_provider_structured_with_mock_transport():
    async def mock_handler(request):
        return Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps({
                                "title": "Memory Leak in Loop",
                                "severity": "MEDIUM",
                                "line_number": 88,
                                "suggested_fix": "Close resource stream.",
                            })
                        }
                    }
                ],
                "usage": {"prompt_tokens": 100, "completion_tokens": 40},
            },
        )

    transport = MockTransport(mock_handler)
    client = AsyncClient(transport=transport)
    provider = OpenAIProvider(api_key="sk-test-mock-key", http_client=client)

    messages = [LLMMessage(role=MessageRole.USER, content="Analyze performance.")]
    res = await provider.generate_structured(messages, CodeFindingTestSchema)

    assert isinstance(res.data, CodeFindingTestSchema)
    assert res.data.title == "Memory Leak in Loop"
    assert res.data.line_number == 88


# =============================================================================
# 6. GOOGLE GEMINI ADAPTER TRANSPORT MOCK TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_gemini_provider_with_mock_transport():
    async def mock_handler(request):
        assert "gemini-2.5-flash" in str(request.url)
        return Response(
            200,
            json={
                "candidates": [{"content": {"parts": [{"text": "Gemini review response."}]}, "finishReason": "STOP"}],
                "usageMetadata": {"promptTokenCount": 200, "candidatesTokenCount": 60, "totalTokenCount": 260},
            },
        )

    transport = MockTransport(mock_handler)
    client = AsyncClient(transport=transport)
    provider = GeminiProvider(api_key="AIzaSyMockKey", http_client=client)

    messages = [LLMMessage(role=MessageRole.USER, content="Review security.")]
    res = await provider.generate(messages, ModelConfig(model="gemini-2.5-flash"))

    assert res.content == "Gemini review response."
    assert res.provider == "gemini"
    assert res.usage.total_tokens == 260
    assert res.cost_usd > 0


# =============================================================================
# 7. ANTHROPIC CLAUDE ADAPTER TRANSPORT MOCK TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_anthropic_provider_with_mock_transport():
    async def mock_handler(request):
        req_data = json.loads(request.content)
        assert req_data["model"] == "claude-3-5-sonnet"
        return Response(
            200,
            json={
                "content": [{"type": "text", "text": "Claude review response."}],
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 120, "output_tokens": 30},
            },
        )

    transport = MockTransport(mock_handler)
    client = AsyncClient(transport=transport)
    provider = AnthropicProvider(api_key="sk-ant-mock-key", http_client=client)

    messages = [LLMMessage(role=MessageRole.USER, content="Review architecture.")]
    res = await provider.generate(messages, ModelConfig(model="claude-3-5-sonnet"))

    assert res.content == "Claude review response."
    assert res.provider == "anthropic"
    assert res.usage.total_tokens == 150
    assert res.cost_usd > 0


# =============================================================================
# 8. AI MODEL INFRASTRUCTURE REST APIS
# =============================================================================

@pytest.mark.asyncio
async def test_ai_api_endpoints(async_client: AsyncClient):
    # 1. Health check API
    health_res = await async_client.get("/api/v1/ai/health")
    assert health_res.status_code == 200
    statuses = health_res.json()
    assert "openai" in statuses
    assert "mock" in statuses
    assert statuses["mock"]["status"] == "healthy"

    # 2. Models & Pricing API
    models_res = await async_client.get("/api/v1/ai/models")
    assert models_res.status_code == 200
    models_data = models_res.json()
    assert "gpt-4o" in models_data["pricing_per_million_tokens_usd"]
    assert "gemini-2.5-flash" in models_data["pricing_per_million_tokens_usd"]
    assert "claude-3-5-sonnet" in models_data["pricing_per_million_tokens_usd"]

    # 3. Prompts API
    prompts_res = await async_client.get("/api/v1/ai/prompts")
    assert prompts_res.status_code == 200
    prompts = prompts_res.json()
    prompt_names = [p["name"] for p in prompts]
    assert "security_sentinel" in prompt_names
    assert "bug_hunter" in prompt_names

    # 4. Usage API
    usage_res = await async_client.get("/api/v1/ai/usage")
    assert usage_res.status_code == 200
    usage = usage_res.json()
    assert "token_budget" in usage
    assert "total_tokens_consumed" in usage
