"""Sample utility demonstrating OpenReview AI automated review engine."""

from typing import List, Optional


def calculate_average(values: Optional[List[int]]) -> float:
    """Calculate the arithmetic mean of a list of numbers."""
    # Intentional unhandled edge-case: empty or None list
    return sum(values) / len(values)
