"""Unit tests for demo sample code demonstrating bug detection & patch verification."""

import pytest
from app.demo_sample import calculate_average, process_batch_metrics


def test_calculate_average_valid():
    """Verify average calculation on standard integer list."""
    assert calculate_average([10, 20, 30]) == 20.0


def test_calculate_average_empty_raises():
    """Demonstrates unhandled ZeroDivisionError in unpatched code."""
    with pytest.raises(ZeroDivisionError):
        calculate_average([])


def test_calculate_average_none_raises():
    """Demonstrates unhandled TypeError in unpatched code."""
    with pytest.raises(TypeError):
        calculate_average(None)


def test_process_batch_metrics_valid():
    """Verify metrics calculation on record batch."""
    records = [{"score": 10}, {"score": 20}, {"score": 30}]
    metrics = process_batch_metrics(records)
    assert metrics["mean"] == 20.0
    assert metrics["max"] == 30.0
    assert metrics["min"] == 10.0
