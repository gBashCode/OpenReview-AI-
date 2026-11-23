"""Unit tests for AutoScaleX Workload Classifier Engine."""

import pytest
from app.analyzer.workload_classifier import (
    WorkloadClassifier,
    WorkloadTier,
    workload_classifier,
)


def test_classify_trivial_single_line_change():
    """Single file, minor bugfix should route to FAST queue with minimum compute footprint."""
    score = workload_classifier.classify(
        changed_files_count=1,
        additions=4,
        deletions=2,
        file_paths=["src/utils/calculator.py"],
        raw_diff="""
diff --git a/src/utils/calculator.py b/src/utils/calculator.py
--- a/src/utils/calculator.py
+++ b/src/utils/calculator.py
@@ -10,2 +10,4 @@
+    if b == 0:
+        return 0
""",
    )

    assert score.tier == WorkloadTier.FAST
    assert score.complexity_score <= 18.0
    assert score.scaling_weight == 0.25
    assert score.recommended_agent_count == 3
    assert score.timeout_seconds == 15
    assert score.metrics.has_database_migration is False
    assert score.metrics.has_security_sensitive_files is False


def test_classify_standard_feature_pull_request():
    """Typical feature PR with 6 files and moderate line changes routes to STANDARD."""
    score = workload_classifier.classify(
        changed_files_count=6,
        additions=140,
        deletions=30,
        file_paths=[
            "frontend/src/pages/Dashboard.tsx",
            "frontend/src/components/MetricCard.tsx",
            "backend/app/api/v1/endpoints/analytics.py",
            "backend/app/analytics/schemas.py",
            "tests/test_analytics.py",
            "README.md",
        ],
    )

    assert score.tier == WorkloadTier.STANDARD
    assert 18.0 < score.complexity_score <= 55.0
    assert score.scaling_weight == 1.0
    assert score.recommended_agent_count == 5
    assert score.timeout_seconds == 45


def test_classify_massive_architectural_pull_request():
    """Huge 25-file PR with large diff routes to HEAVY queue with max worker allocation."""
    score = workload_classifier.classify(
        changed_files_count=26,
        additions=950,
        deletions=320,
        file_paths=[f"services/module_{i}.py" for i in range(26)],
    )

    assert score.tier == WorkloadTier.HEAVY
    assert score.complexity_score > 55.0
    assert score.scaling_weight == 3.0
    assert score.recommended_agent_count == 8
    assert score.timeout_seconds == 90
    assert score.estimated_tokens > 8000


def test_classify_migration_file_elevates_to_heavy():
    """Any PR that modifies database schemas/migrations must elevate to HEAVY review."""
    score = workload_classifier.classify(
        changed_files_count=2,
        additions=25,
        deletions=0,
        file_paths=[
            "backend/alembic/versions/008_payment_schema.py",
            "backend/app/models/payment.py",
        ],
    )

    assert score.tier == WorkloadTier.HEAVY
    assert score.metrics.has_database_migration is True
    assert any("migration" in r.lower() for r in score.reasons)


def test_classify_security_sensitive_boundary():
    """Security sensitive files increase complexity factor and trigger extra scrutiny."""
    score = workload_classifier.classify(
        changed_files_count=2,
        additions=45,
        deletions=10,
        file_paths=[
            "backend/app/auth/password_reset.py",
            "backend/app/core/security_token.py",
        ],
    )

    assert score.metrics.has_security_sensitive_files is True
    assert any("security" in r.lower() for r in score.reasons)


def test_classify_empty_diff_bounds():
    """Zero changes are handled gracefully without division by zero or errors."""
    score = workload_classifier.classify(
        changed_files_count=0,
        additions=0,
        deletions=0,
    )

    assert score.complexity_score >= 1.0
    assert score.tier == WorkloadTier.FAST
    assert score.metrics.total_churn == 0
