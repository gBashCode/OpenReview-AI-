"""Unit tests for AutoScaleX Workload-Aware Queue Routing and Task Dispatching."""

from unittest.mock import MagicMock, patch
import pytest
from app.analyzer.workload_classifier import WorkloadTier
from app.core.config import get_settings
from app.tasks.review_tasks import (
    dispatch_review_task,
    get_queue_for_tier,
    get_timeout_for_tier,
)

settings = get_settings()


def test_queue_tier_mappings():
    """Verify tier strings map correctly to AutoScaleX priority queues."""
    assert get_queue_for_tier("fast") == settings.CELERY_QUEUE_FAST
    assert get_queue_for_tier(WorkloadTier.FAST.value) == settings.CELERY_QUEUE_FAST

    assert get_queue_for_tier("standard") == settings.CELERY_QUEUE_STANDARD
    assert get_queue_for_tier(WorkloadTier.STANDARD.value) == settings.CELERY_QUEUE_STANDARD

    assert get_queue_for_tier("heavy") == settings.CELERY_QUEUE_HEAVY
    assert get_queue_for_tier(WorkloadTier.HEAVY.value) == settings.CELERY_QUEUE_HEAVY

    # Fallback default
    assert get_queue_for_tier("unknown_tier") == settings.CELERY_QUEUE_STANDARD
    assert get_queue_for_tier(None) == settings.CELERY_QUEUE_STANDARD


def test_tier_timeout_limits():
    """Verify SLA timeouts match workload scale."""
    assert get_timeout_for_tier("fast") == 20
    assert get_timeout_for_tier("standard") == 60
    assert get_timeout_for_tier("heavy") == 120
    assert get_timeout_for_tier("unknown") == 60


def test_dispatch_fallback_mode_when_celery_disabled():
    """Verify non-blocking fallback dispatch when Celery is disabled."""
    result = dispatch_review_task(
        review_id="rev-test-123",
        tier="fast",
        execute_in_process=False,
    )
    assert result["dispatched"] is True
    assert result["mode"] == "queued_pending"
    assert result["queue"] == settings.CELERY_QUEUE_FAST
    assert result["tier"] == "fast"
    assert result["task_id"] is None


def test_dispatch_celery_routing_when_enabled(monkeypatch):
    """Verify dispatch_review_task routes to correct Celery queue and routing key."""
    monkeypatch.setattr(settings, "CELERY_ENABLED", True)

    mock_async_result = MagicMock()
    mock_async_result.id = "task-uuid-888"

    with patch("app.tasks.review_tasks.execute_autonomous_review.apply_async", return_value=mock_async_result) as mock_apply:
        result = dispatch_review_task(
            review_id="rev-heavy-999",
            tier="heavy",
            custom_diff="+ complex migration diff",
        )

        assert result["dispatched"] is True
        assert result["mode"] == "celery"
        assert result["task_id"] == "task-uuid-888"
        assert result["queue"] == settings.CELERY_QUEUE_HEAVY
        assert result["tier"] == "heavy"

        # Verify apply_async kwargs
        mock_apply.assert_called_once()
        _, kwargs = mock_apply.call_args
        assert kwargs["queue"] == settings.CELERY_QUEUE_HEAVY
        assert kwargs["routing_key"] == settings.CELERY_QUEUE_HEAVY
        assert kwargs["kwargs"]["workload_tier"] == "heavy"
        assert kwargs["time_limit"] == 130
        assert kwargs["soft_time_limit"] == 120


def test_dispatch_broker_failure_resilience(monkeypatch):
    """Verify graceful fallback if broker throws a connection error."""
    monkeypatch.setattr(settings, "CELERY_ENABLED", True)

    with patch("app.tasks.review_tasks.execute_autonomous_review.apply_async", side_effect=ConnectionError("Broker unreachable")):
        result = dispatch_review_task(
            review_id="rev-err-456",
            tier="standard",
            execute_in_process=False,
        )

        assert result["dispatched"] is True
        assert result["mode"] == "queued_pending"
        assert result["queue"] == settings.CELERY_QUEUE_STANDARD
        assert result["tier"] == "standard"
