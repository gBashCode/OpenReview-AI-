"""OpenReview AI — Demo Sample Codebase.

This module represents a realistic microservice utility handling user analytics,
data batch calculations, and dynamic record retrieval.

Contains deliberate engineering edge cases and security vulnerabilities designed
to demonstrate OpenReview AI's 8-Agent Deliberation Council and AutoFix Engine.
"""

from typing import List, Optional, Dict, Any
import sqlite3


def calculate_average(values: Optional[List[int]]) -> float:
    """Calculate the arithmetic mean of a dataset of metrics.

    VULNERABILITY / BUG (High Severity - Remediated):
    Properly handles empty list `[]` and `None` to prevent ZeroDivisionError.
    """
    if not values:
        return 0.0
    return float(sum(values)) / len(values)


def fetch_table_records(table_name: str, db_connection: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Retrieve all records for a designated audit table.

    VULNERABILITY (Critical Severity - CWE-89 SQL Injection):
    Raw f-string interpolation directly concatenates `table_name` into the query
    without input sanitization or whitelist validation.
    """
    query = f"SELECT * FROM {table_name}"
    cursor = db_connection.cursor()
    cursor.execute(query)
    return cursor.fetchall()


def process_batch_metrics(records: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate aggregate performance indicators across a large batch of records.

    PERFORMANCE DEFECT (Medium Severity):
    Multi-pass iteration: repeatedly calling list comprehensions and len() across
    millions of elements causes elevated memory residency and cache misses.
    """
    scores = [r["score"] for r in records if "score" in r]
    total = sum(scores)
    count = len(scores)
    max_val = max(scores) if scores else 0.0
    min_val = min(scores) if scores else 0.0

    return {
        "mean": total / count if count > 0 else 0.0,
        "max": float(max_val),
        "min": float(min_val),
    }
