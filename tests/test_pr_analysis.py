"""Tests for the Pull Request Analysis Engine, Diff Parsing, Impact Detection, and Risk Scoring."""

import pytest
from httpx import AsyncClient

from app.analyzer.diff_parser import UnifiedDiffParser
from app.analyzer.impact_detector import ImpactDetector
from app.analyzer.pr_analysis_engine import PRAnalysisEngine
from app.analyzer.risk_scorer import RiskScorer
from app.analyzer.schemas import ChangeCategory, ComplexityLevel, RiskLevel
from app.indexing.models import CodeSymbol


SAMPLE_AUTH_DIFF = """diff --git a/backend/app/auth/service.py b/backend/app/auth/service.py
index a1b2c3d..e4f5a6b 100644
--- a/backend/app/auth/service.py
+++ b/backend/app/auth/service.py
@@ -10,7 +10,12 @@ class AuthService:
     def login(self, username: str, password: str) -> str:
-        if not username:
-            return ""
+        if not username or not password:
+            raise ValueError("Credentials required")
+        # Verify token and authenticate user credentials
+        user = self.find_user(username)
+        token = self.create_jwt_token(user.id)
+        return token
"""

SAMPLE_MULTI_FILE_DIFF = """diff --git a/src/billing/checkout.py b/src/billing/checkout.py
new file mode 100644
index 0000000..1122334
--- /dev/null
+++ b/src/billing/checkout.py
@@ -0,0 +1,15 @@
+import stripe
+
+class CheckoutService:
+    def process_payment(self, amount_cents: int, credit_card_token: str):
+        if amount_cents <= 0:
+            raise ValueError("Invalid amount")
+        charge = stripe.Charge.create(amount=amount_cents, token=credit_card_token)
+        return charge.id
diff --git a/alembic/versions/004_payment_tables.py b/alembic/versions/004_payment_tables.py
new file mode 100644
index 0000000..5566778
--- /dev/null
+++ b/alembic/versions/004_payment_tables.py
@@ -0,0 +1,8 @@
+from alembic import op
+import sqlalchemy as sa
+
+def upgrade():
+    op.create_table("payments", sa.Column("id", sa.String(36), primary_key=True))
"""

SAMPLE_BUGFIX_DIFF = """diff --git a/src/math_utils.py b/src/math_utils.py
index 1111111..2222222 100644
--- a/src/math_utils.py
+++ b/src/math_utils.py
@@ -5,3 +5,4 @@ def divide(a: float, b: float) -> float:
+    if b == 0:
+        raise ZeroDivisionError("Cannot divide by zero")
     return a / b
diff --git a/tests/test_math.py b/tests/test_math.py
index 3333333..4444444 100644
--- a/tests/test_math.py
+++ b/tests/test_math.py
@@ -10,2 +10,5 @@ def test_divide():
+def test_divide_zero():
+    with pytest.raises(ZeroDivisionError):
+        divide(10, 0)
"""


# =============================================================================
# 1. UNIFIED GIT DIFF PARSING TESTS
# =============================================================================

def test_unified_diff_parser_single_file():
    parser = UnifiedDiffParser()
    files = parser.parse(SAMPLE_AUTH_DIFF)

    assert len(files) == 1
    file = files[0]
    assert file.new_path == "backend/app/auth/service.py"
    assert file.status == "modified"
    assert file.additions == 6
    assert file.deletions == 2

    # Check added lines
    added_lines_text = [text for _, text in file.added_lines]
    assert any("create_jwt_token" in t for t in added_lines_text)

    # Check line numbers
    added_line_numbers = [line for line, _ in file.added_lines]
    assert 11 in added_line_numbers
    assert 12 in added_line_numbers


def test_unified_diff_parser_multi_file_and_new_files():
    parser = UnifiedDiffParser()
    files = parser.parse(SAMPLE_MULTI_FILE_DIFF)

    assert len(files) == 2
    paths = {f.new_path: f for f in files}

    assert "src/billing/checkout.py" in paths
    assert paths["src/billing/checkout.py"].status == "added"
    assert paths["src/billing/checkout.py"].additions == 8

    assert "alembic/versions/004_payment_tables.py" in paths
    assert paths["alembic/versions/004_payment_tables.py"].status == "added"


# =============================================================================
# 2. MODIFIED FUNCTION IDENTIFICATION
# =============================================================================

def test_identify_modified_functions_with_symbols():
    detector = ImpactDetector()
    parser = UnifiedDiffParser()
    parsed_files = parser.parse(SAMPLE_AUTH_DIFF)

    # Mock indexed symbols for backend/app/auth/service.py
    fake_login_symbol = CodeSymbol(
        index_id="idx-1",
        name="login",
        kind="method",
        file_path="backend/app/auth/service.py",
        line_number=10,
        end_line_number=20,
        signature="def login(self, username: str, password: str) -> str",
    )
    fake_unrelated_symbol = CodeSymbol(
        index_id="idx-1",
        name="hash_password",
        kind="method",
        file_path="backend/app/auth/service.py",
        line_number=40,
        end_line_number=50,
        signature="def hash_password(self, password: str) -> str",
    )

    changed_funcs = detector.identify_modified_functions(
        parsed_files, repo_symbols=[fake_login_symbol, fake_unrelated_symbol]
    )

    assert len(changed_funcs) == 1
    assert changed_funcs[0].name == "login"
    assert changed_funcs[0].kind == "method"
    assert changed_funcs[0].file_path == "backend/app/auth/service.py"
    assert changed_funcs[0].line_number == 10


# =============================================================================
# 3. SENSITIVE CHANGES DETECTION
# =============================================================================

def test_detect_sensitive_changes_auth_and_payment():
    detector = ImpactDetector()
    parser = UnifiedDiffParser()

    # 1. Auth diff
    auth_files = parser.parse(SAMPLE_AUTH_DIFF)
    auth_risks = detector.detect_sensitive_changes(auth_files)
    risk_names = [r.name for r in auth_risks]
    assert any("Authentication" in name for name in risk_names)

    # 2. Payment & DB migration diff
    payment_files = parser.parse(SAMPLE_MULTI_FILE_DIFF)
    payment_risks = detector.detect_sensitive_changes(payment_files)
    p_names = [r.name for r in payment_risks]
    assert any("Payment" in name for name in p_names)
    assert any("Database Migrations" in name for name in p_names)


# =============================================================================
# 4. CHANGE CLASSIFICATION & AFFECTED TESTS
# =============================================================================

def test_change_classification():
    detector = ImpactDetector()
    parser = UnifiedDiffParser()

    # Bug fix
    bug_files = parser.parse(SAMPLE_BUGFIX_DIFF)
    categories = detector.classify_change_types(bug_files, pr_title="fix: divide by zero exception")
    assert ChangeCategory.BUG_FIX.value in categories
    assert ChangeCategory.TEST_MODIFICATION.value in categories

    # Security Sensitive
    auth_files = parser.parse(SAMPLE_AUTH_DIFF)
    sec_risks = detector.detect_sensitive_changes(auth_files)
    sec_categories = detector.classify_change_types(
        auth_files, pr_title="Update login token logic", sensitive_factors=sec_risks
    )
    assert ChangeCategory.SECURITY_SENSITIVE.value in sec_categories


def test_missing_test_coverage_detection():
    detector = ImpactDetector()
    parser = UnifiedDiffParser()

    # 1. Source changed without test files -> Missing test coverage
    auth_files = parser.parse(SAMPLE_AUTH_DIFF)
    _, missing1 = detector.detect_affected_tests(auth_files)
    assert missing1 is True

    # 2. Source changed WITH test files -> Not missing
    bug_files = parser.parse(SAMPLE_BUGFIX_DIFF)
    _, missing2 = detector.detect_affected_tests(bug_files)
    assert missing2 is False


# =============================================================================
# 5. COMPLEXITY & RISK SCORING
# =============================================================================

def test_complexity_and_risk_scoring():
    scorer = RiskScorer()
    parser = UnifiedDiffParser()
    detector = ImpactDetector()

    parsed_files = parser.parse(SAMPLE_MULTI_FILE_DIFF)
    changed_funcs = detector.identify_modified_functions(parsed_files)
    sensitive_factors = detector.detect_sensitive_changes(parsed_files)

    # Estimate complexity
    level, details = scorer.estimate_complexity(parsed_files, changed_funcs)
    assert level in (ComplexityLevel.LOW, ComplexityLevel.MEDIUM)
    assert details["total_churn"] > 0

    # Calculate risk score
    score, risk_level, all_factors = scorer.calculate_risk(
        complexity_level=level,
        sensitive_factors=sensitive_factors,
        missing_test_coverage=True,  # missing tests in payment logic!
        affected_modules_count=2,
        file_count=len(parsed_files),
    )

    # With Payment (+30) + DB migration (+20) + Missing tests (+20) + Base complexity (+10) = 80
    assert score >= 70.0
    assert risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
    assert any(f.name == "Missing Test Coverage" for f in all_factors)


# =============================================================================
# 6. END-TO-END PR ANALYSIS ENGINE
# =============================================================================

@pytest.mark.asyncio
async def test_pr_analysis_engine_end_to_end():
    engine = PRAnalysisEngine()
    result = await engine.analyze_pull_request(
        raw_diff=SAMPLE_MULTI_FILE_DIFF,
        pr_number=42,
        title="feat(billing): add stripe checkout and payment migrations",
        description="Introduces checkout processing and database tables.",
    )

    assert result.pr_number == 42
    assert result.total_files_changed == 2
    assert result.total_additions > 0
    assert result.risk_score >= 60.0
    assert result.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)

    # Verify recommended agents
    agent_names = {a.agent_name: a for a in result.recommended_review_agents}
    assert "Security Sentinel" in agent_names
    assert agent_names["Security Sentinel"].priority == "MANDATORY"
    assert "Performance Optimizer" in agent_names
    assert "Test Coverage Verifier" in agent_names

    # Verify review plan
    assert "phases" in result.review_execution_plan
    assert len(result.review_execution_plan["phases"]) >= 3
    assert len(result.review_execution_plan["priority_files"]) >= 1


# =============================================================================
# 7. ANALYZER REST APIS
# =============================================================================

@pytest.mark.asyncio
async def test_analyzer_rest_api_diff_endpoint(async_client: AsyncClient):
    payload = {
        "raw_diff": SAMPLE_AUTH_DIFF,
        "title": "fix: update token generation logic",
        "description": "Patches login credential verification.",
    }

    res = await async_client.post("/api/v1/analyzer/diff", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["pr_number"] == 1
    assert data["total_files_changed"] == 1
    assert len(data["changed_files"]) == 1
    assert data["changed_files"][0]["file_path"] == "backend/app/auth/service.py"
    assert ChangeCategory.SECURITY_SENSITIVE.value in data["change_categories"]
    assert any("Authentication" in f["name"] for f in data["risk_factors"])


@pytest.mark.asyncio
async def test_pull_request_analyze_endpoint(async_client: AsyncClient):
    # 1. Register repo
    repo_res = await async_client.post(
        "/api/v1/repositories",
        json={
            "github_repo_id": 554433,
            "owner": "deepmind",
            "name": "analyzer-test-repo",
            "default_branch": "main",
        },
    )
    repo_id = repo_res.json()["id"]

    # 2. Register PR
    pr_res = await async_client.post(
        "/api/v1/pull-requests",
        json={
            "repository_id": repo_id,
            "pr_number": 105,
            "title": "feat: add user authentication",
            "description": "Implements login verification.",
            "head_branch": "feature/auth",
            "base_branch": "main",
            "head_sha": "a" * 40,
            "base_sha": "b" * 40,
            "author_username": "octocat",
            "state": "open",
        },
    )
    assert pr_res.status_code == 201
    pr_id = pr_res.json()["id"]

    # 3. Analyze PR endpoint with custom diff
    analyze_res = await async_client.post(
        f"/api/v1/pull-requests/{pr_id}/analyze",
        json={"raw_diff": SAMPLE_AUTH_DIFF},
    )
    assert analyze_res.status_code == 200
    analysis = analyze_res.json()
    assert analysis["pr_number"] == 105
    assert len(analysis["changed_files"]) == 1
    assert analysis["risk_score"] > 0
    assert len(analysis["recommended_review_agents"]) >= 3
