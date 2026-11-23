"""Unit tests for AutoScaleX Telemetry & Sliding-Window LLM Token Governor."""

import time
import pytest
from app.core.ai.base import LLMMessage, MessageRole, ModelConfig
from app.core.ai.gateway import ModelGateway, TokenGovernor
from app.core.ai.providers.mock_provider import MockLLMProvider
from app.core.metrics import PrometheusMetricsRegistry


def test_prometheus_telemetry_autoscale_metrics():
    """Verify Prometheus registry serializes AutoScaleX queue, worker, and governor metrics."""
    reg = PrometheusMetricsRegistry()
    reg.set_queue_depth("fast", 3)
    reg.set_queue_depth("standard", 7)
    reg.set_queue_depth("heavy", 2)
    reg.set_workload_backlog_score(42.5)
    reg.set_active_workers("fast", 2)
    reg.set_active_workers("standard", 5)
    reg.set_active_workers("heavy", 3)
    reg.record_token_throttle()
    reg.record_token_throttle()
    reg.set_token_burn_rate(85000)

    text = reg.generate_metrics_text()

    assert 'openreview_queue_depth{tier="fast"} 3' in text
    assert 'openreview_queue_depth{tier="standard"} 7' in text
    assert 'openreview_queue_depth{tier="heavy"} 2' in text
    assert 'openreview_workload_backlog_score 42.50' in text
    assert 'openreview_active_workers{tier="fast"} 2' in text
    assert 'openreview_active_workers{tier="standard"} 5' in text
    assert 'openreview_active_workers{tier="heavy"} 3' in text
    assert 'openreview_token_governor_throttle_events_total 2' in text
    assert 'openreview_llm_token_burn_rate_rpm 85000' in text


@pytest.mark.asyncio
async def test_token_governor_permit_and_sliding_window():
    """Verify governor allows normal traffic but throttles when nearing quota threshold."""
    # 10,000 TPM quota with 85% threshold = 8,500 token limit
    governor = TokenGovernor(quota_per_minute=10000, throttle_threshold=0.85, window_seconds=60.0)

    # Initial permit should have 0 delay
    delay1 = await governor.acquire_permit(estimated_tokens=2000)
    assert delay1 == 0.0

    # Record 8,000 tokens
    governor.record_usage(8000)
    assert governor.get_current_burn_rate() == 8000

    # Next permit with 1,000 tokens brings total to 9,000 (> 8,500 threshold) -> should throttle
    delay2 = await governor.acquire_permit(estimated_tokens=1000)
    assert delay2 > 0.0

    # Verify sliding window pruning
    old_time = time.time() - 70.0
    governor._history = [(old_time, 8000)]
    assert governor.get_current_burn_rate() == 0

    # After pruning old history, permit should have 0 delay again
    delay3 = await governor.acquire_permit(estimated_tokens=2000)
    assert delay3 == 0.0


@pytest.mark.asyncio
async def test_model_gateway_governor_integration():
    """Verify ModelGateway calls governor and handles throttling smoothly."""
    gateway = ModelGateway(
        primary_provider="mock",
        fallback_provider="mock",
        token_budget=10000,
    )
    mock_prov = MockLLMProvider(default_response="Audit complete.")
    gateway.register_provider("mock", mock_prov)

    messages = [
        LLMMessage(role=MessageRole.USER, content="Review this small change.")
    ]
    cfg = ModelConfig(model="mock-model", max_tokens=100)

    # Preload governor to trigger throttling
    gateway.governor.quota_per_minute = 1000
    gateway.governor.record_usage(900)

    # Request should execute cleanly despite throttling delay
    res = await gateway.generate(messages=messages, config=cfg)
    assert res.content == "Audit complete."
    assert gateway.governor.get_current_burn_rate() >= 900
