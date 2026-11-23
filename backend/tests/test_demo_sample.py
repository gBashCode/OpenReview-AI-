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


def test_fetch_table_records_whitelist():
    """Verify whitelist protection prevents SQL injection."""
    import sqlite3
    from backend.app.demo_sample import fetch_table_records
    conn = sqlite3.connect(":memory:")
    with pytest.raises(ValueError):
        fetch_table_records("users; DROP TABLE users;--", conn)
