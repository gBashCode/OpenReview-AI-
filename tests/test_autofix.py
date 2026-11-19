"""Comprehensive Tests for OpenReview AI AutoFix Engine.

Verifies:
1. Patch creation and sandbox test run tracking.
2. Complete 14-step AutoFix engine workflow (minimal patch, unified diff, applicability, formatting, linter, tests, sandbox, report, pending approval).
3. Patch preview endpoint with side-by-side original/proposed code and rollback diff.
4. Patch diagnostic report endpoint with test runs and linter status.
5. Explicit human approval workflow for committing patches to PR branches.
6. Explicit human approval workflow for creating remediation Pull Requests.
7. Rejection workflow with human explanation reason.
8. Rollback workflow using inverse rollback diff.
9. Sandbox zero-trust security isolation (secret scrubbing, whitelist environment, resource limits).
10. Sandbox failure explanations and trace extraction.
11. Patch applicability validation and malformed diff rejection.
"""

import os
import pytest
from httpx import AsyncClient

from app.autofix.engine import AutoFixEngine, PatchReport
from app.autofix.patcher import PatchApplier
from app.sandbox.runner import EphemeralSandboxRunner, SandboxConfig, SandboxExecutionResult
from app.sandbox.security import SandboxSecurityEnforcer
from app.verification.schemas import FindingSeverity, LineRange, VerificationStatus, VerifiedFinding


SAMPLE_SOURCE_CODE = """
def calculate_discount(price: float, discount_percent: float) -> float:
    # Potential division or calculation error
    discount_amount = price * (discount_percent / 100)
    final_price = price - discount_amount
    return round(final_price, 2)
""".strip()


@pytest.mark.asyncio
async def test_patch_approval_and_test_run(async_client: AsyncClient):
    """End-to-end integration: PR simulation -> finding -> patch -> sandbox test run -> approval."""
    # Setup repo -> PR -> Review
    repo_res = await async_client.post(
        "/api/v1/repositories",
        json={"github_repo_id": 776655, "owner": "autofix-org", "name": "patch-test"},
    )
    repo_id = repo_res.json()["id"]

    pr_res = await async_client.post(
        "/api/v1/pull-requests",
        json={
            "repository_id": repo_id,
            "pr_number": 7,
            "title": "fix: buffer overflow patch",
            "head_branch": "patch/buffer",
            "base_branch": "main",
            "head_sha": "a" * 40,
            "base_sha": "b" * 40,
            "author_username": "coder",
        },
    )
    pr_id = pr_res.json()["id"]

    rev_res = await async_client.post("/api/v1/reviews", json={"pull_request_id": pr_id})
    review_id = rev_res.json()["id"]

    # Trigger simulation to populate findings and patches
    sim_res = await async_client.post(f"/api/v1/reviews/{review_id}/simulate-ai-pass")
    assert sim_res.status_code == 200

    # Get findings
    findings_res = await async_client.get(f"/api/v1/reviews/{review_id}/findings")
    assert findings_res.status_code == 200
    findings = findings_res.json()
    assert len(findings) > 0
    first_finding = findings[0]
    finding_id = first_finding["id"]

    # List patches for finding
    patches_res = await async_client.get(f"/api/v1/findings/{finding_id}/patches")
    assert patches_res.status_code == 200
    patches = patches_res.json()
    assert len(patches) > 0
    patch = patches[0]
    patch_id = patch["id"]
    assert patch["status"] == "pending"

    # Verify sandbox test runs for this patch
    test_runs_res = await async_client.get(f"/api/v1/autofix/{patch_id}/test-runs")
    assert test_runs_res.status_code == 200
    test_runs = test_runs_res.json()
    assert len(test_runs) > 0
    assert test_runs[0]["status"] == "passed"
    assert test_runs[0]["passed_tests"] > 0

    # Human approves the patch
    decision_res = await async_client.post(
        f"/api/v1/autofix/{patch_id}/decision",
        json={"decision": "approve"},
    )
    assert decision_res.status_code == 200
    assert decision_res.json()["status"] == "approved"

    # Verify finding was automatically marked resolved
    updated_finding_res = await async_client.get(f"/api/v1/findings/{finding_id}")
    assert updated_finding_res.status_code == 200
    assert updated_finding_res.json()["is_resolved"] is True


@pytest.mark.asyncio
async def test_autofix_14_step_engine_workflow():
    """Validates the 14-step AutoFix pipeline: minimal patch, diff, format, lint, sandbox, report, approval."""
    engine = AutoFixEngine()

    finding = VerifiedFinding(
        id="f-autofix-101",
        title="Negative price unhandled in discount calculation",
        description="Negative price input results in invalid discount amounts.",
        file_path="app/pricing.py",
        line_range=LineRange(start_line=2, end_line=3),
        severity=FindingSeverity.MEDIUM,
        confidence=0.95,
        root_cause="Missing boundary check for negative price inputs.",
        impact="Erroneous invoice calculation.",
        source_evidence="discount_amount = price * (discount_percent / 100)",
        suggested_remediation="if price < 0: raise ValueError('Price cannot be negative')\n    discount_amount = price * (discount_percent / 100)",
        verification_status=VerificationStatus.CONFIRMED,
    )

    repo_files = {"app/pricing.py": SAMPLE_SOURCE_CODE}

    report: PatchReport = await engine.execute_autofix_workflow(
        finding=finding,
        repository_files=repo_files,
    )

    # 1. Minimal patch & diff validation
    assert report.finding_id == "f-autofix-101"
    assert report.unified_diff_valid is True
    assert report.patch_applicable is True
    assert "--- a/app/pricing.py" in report.diff_content
    assert "+++ b/app/pricing.py" in report.diff_content

    # 2. Formatter & Linter
    assert report.formatter_status in ("passed", "warning")
    assert report.linter_status == "passed"
    assert len(report.linter_errors) == 0

    # 3. Tests & Sandbox
    assert "def test_autofix_" in report.generated_test_code
    assert report.sandbox_result is not None
    assert report.sandbox_result.status == "passed"

    # 4. Rollback diff
    assert report.rollback_diff
    assert "--- a/app/pricing.py" in report.rollback_diff

    # 5. Safety: NEVER auto-merged! Must be pending approval
    assert report.approval_status == "pending_approval"


@pytest.mark.asyncio
async def test_autofix_preview_and_report_endpoints(async_client: AsyncClient):
    """Verifies /preview and /report endpoints providing side-by-side viewer data and telemetry."""
    # 1. Setup repository, PR, and review
    repo_res = await async_client.post(
        "/api/v1/repositories",
        json={"github_repo_id": 998877, "owner": "preview-org", "name": "preview-test"},
    )
    repo_id = repo_res.json()["id"]

    pr_res = await async_client.post(
        "/api/v1/pull-requests",
        json={
            "repository_id": repo_id,
            "pr_number": 12,
            "title": "fix: preview validation",
            "head_branch": "preview/branch",
            "base_branch": "main",
            "head_sha": "c" * 40,
            "base_sha": "d" * 40,
            "author_username": "tester",
        },
    )
    pr_id = pr_res.json()["id"]

    rev_res = await async_client.post("/api/v1/reviews", json={"pull_request_id": pr_id})
    review_id = rev_res.json()["id"]
    await async_client.post(f"/api/v1/reviews/{review_id}/simulate-ai-pass")

    findings = (await async_client.get(f"/api/v1/reviews/{review_id}/findings")).json()
    finding_id = findings[0]["id"]
    patches = (await async_client.get(f"/api/v1/findings/{finding_id}/patches")).json()
    patch_id = patches[0]["id"]

    # 2. Test /preview endpoint
    prev_res = await async_client.get(f"/api/v1/autofix/{patch_id}/preview")
    assert prev_res.status_code == 200
    prev_data = prev_res.json()
    assert prev_data["patch_id"] == patch_id
    assert "original_code" in prev_data
    assert "proposed_code" in prev_data
    assert "diff_content" in prev_data
    assert prev_data["status"] == "pending"

    # 3. Test /report endpoint
    report_res = await async_client.get(f"/api/v1/autofix/{patch_id}/report")
    assert report_res.status_code == 200
    report_data = report_res.json()
    assert report_data["patch_id"] == patch_id
    assert report_data["formatter_status"] == "passed"
    assert report_data["linter_status"] == "passed"
    assert report_data["sandbox_status"] == "passed"
    assert len(report_data["test_runs"]) > 0


@pytest.mark.asyncio
async def test_human_approval_creates_commit(async_client: AsyncClient):
    """Explicit human approval action creating a verified commit on PR branch."""
    repo_res = await async_client.post(
        "/api/v1/repositories",
        json={"github_repo_id": 887766, "owner": "commit-org", "name": "commit-test"},
    )
    repo_id = repo_res.json()["id"]

    pr_res = await async_client.post(
        "/api/v1/pull-requests",
        json={
            "repository_id": repo_id,
            "pr_number": 88,
            "title": "fix: commit approval",
            "head_branch": "fix/commit-branch",
            "base_branch": "main",
            "head_sha": "e" * 40,
            "base_sha": "f" * 40,
            "author_username": "reviewer",
        },
    )
    pr_id = pr_res.json()["id"]
    rev_res = await async_client.post("/api/v1/reviews", json={"pull_request_id": pr_id})
    review_id = rev_res.json()["id"]
    await async_client.post(f"/api/v1/reviews/{review_id}/simulate-ai-pass")

    findings = (await async_client.get(f"/api/v1/reviews/{review_id}/findings")).json()
    finding_id = findings[0]["id"]
    patches = (await async_client.get(f"/api/v1/findings/{finding_id}/patches")).json()
    patch_id = patches[0]["id"]

    # Explicit human commit approval
    commit_res = await async_client.post(
        f"/api/v1/autofix/{patch_id}/commit",
        json={"branch_name": "fix/commit-branch", "commit_message": "fix: apply verified autofix patch"},
    )
    assert commit_res.status_code == 200
    patch_committed = commit_res.json()
    assert patch_committed["status"] == "applied"
    assert patch_committed["commit_sha"] is not None
    assert len(patch_committed["commit_sha"]) == 40
    assert patch_committed["branch_name"] == "fix/commit-branch"

    # Finding resolved
    finding_res = await async_client.get(f"/api/v1/findings/{finding_id}")
    assert finding_res.json()["is_resolved"] is True


@pytest.mark.asyncio
async def test_human_approval_creates_pull_request(async_client: AsyncClient):
    """Explicit human approval action opening an automated remediation Pull Request."""
    repo_res = await async_client.post(
        "/api/v1/repositories",
        json={"github_repo_id": 554433, "owner": "pr-org", "name": "pr-test"},
    )
    repo_id = repo_res.json()["id"]

    pr_res = await async_client.post(
        "/api/v1/pull-requests",
        json={
            "repository_id": repo_id,
            "pr_number": 99,
            "title": "fix: pr approval",
            "head_branch": "main",
            "base_branch": "main",
            "head_sha": "1" * 40,
            "base_sha": "2" * 40,
            "author_username": "dev",
        },
    )
    pr_id = pr_res.json()["id"]
    rev_res = await async_client.post("/api/v1/reviews", json={"pull_request_id": pr_id})
    review_id = rev_res.json()["id"]
    await async_client.post(f"/api/v1/reviews/{review_id}/simulate-ai-pass")

    findings = (await async_client.get(f"/api/v1/reviews/{review_id}/findings")).json()
    finding_id = findings[0]["id"]
    patches = (await async_client.get(f"/api/v1/findings/{finding_id}/patches")).json()
    patch_id = patches[0]["id"]

    # Create Fix PR
    pr_create_res = await async_client.post(
        f"/api/v1/autofix/{patch_id}/create-pr",
        json={"title": "fix(autofix): remediation patch", "description": "Automated patch verified by sandbox"},
    )
    assert pr_create_res.status_code == 200
    pr_data = pr_create_res.json()
    assert pr_data["status"] == "applied"
    assert pr_data["branch_name"].startswith("autofix/patch-")
    assert "https://github.com" in pr_data["pr_url"]


@pytest.mark.asyncio
async def test_patch_rejection_and_rollback_workflows(async_client: AsyncClient):
    """Tests human rejection with reason, and patch rollback of an applied patch."""
    repo_res = await async_client.post(
        "/api/v1/repositories",
        json={"github_repo_id": 665544, "owner": "rollback-org", "name": "rollback-test"},
    )
    repo_id = repo_res.json()["id"]

    pr_res = await async_client.post(
        "/api/v1/pull-requests",
        json={
            "repository_id": repo_id,
            "pr_number": 44,
            "title": "fix: rollback test",
            "head_branch": "rollback/test",
            "base_branch": "main",
            "head_sha": "3" * 40,
            "base_sha": "4" * 40,
            "author_username": "tester",
        },
    )
    pr_id = pr_res.json()["id"]
    rev_res = await async_client.post("/api/v1/reviews", json={"pull_request_id": pr_id})
    review_id = rev_res.json()["id"]
    await async_client.post(f"/api/v1/reviews/{review_id}/simulate-ai-pass")

    findings = (await async_client.get(f"/api/v1/reviews/{review_id}/findings")).json()
    finding_id = findings[0]["id"]
    patches = (await async_client.get(f"/api/v1/findings/{finding_id}/patches")).json()
    patch_id = patches[0]["id"]

    # 1. Reject patch
    reject_res = await async_client.post(
        f"/api/v1/autofix/{patch_id}/decision",
        json={"decision": "reject", "rejection_reason": "Breaks internal API compatibility."},
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["status"] == "rejected"
    assert reject_res.json()["rejection_reason"] == "Breaks internal API compatibility."

    # Finding remains unresolved
    finding = (await async_client.get(f"/api/v1/findings/{finding_id}")).json()
    assert finding["is_resolved"] is False

    # 2. Re-approve and then Rollback
    await async_client.post(f"/api/v1/autofix/{patch_id}/decision", json={"decision": "approve"})
    assert (await async_client.get(f"/api/v1/findings/{finding_id}")).json()["is_resolved"] is True

    rollback_res = await async_client.post(
        f"/api/v1/autofix/{patch_id}/rollback",
        json={"reason": "Discovered regression in staging deployment."},
    )
    assert rollback_res.status_code == 200
    assert rollback_res.json()["status"] == "rolled_back"

    # Finding becomes unresolved again
    assert (await async_client.get(f"/api/v1/findings/{finding_id}")).json()["is_resolved"] is False


# -----------------------------------------------------------------------------
# Sandbox Security & Isolation Tests
# -----------------------------------------------------------------------------

def test_sandbox_security_isolation_and_secret_scrubbing():
    """Validates that SandboxSecurityEnforcer strictly strips all credentials and application secrets."""
    enforcer = SandboxSecurityEnforcer()

    dirty_env = {
        "OPENAI_API_KEY": "sk-secret-token-12345",
        "GITHUB_APP_PRIVATE_KEY": "-----BEGIN RSA PRIVATE KEY-----",
        "DATABASE_URL": "postgresql://postgres:secret@db:5432/openreview",
        "JWT_SECRET": "super_secret_jwt_key",
        "REDIS_URL": "redis://:redis_password@redis:6379",
        "PATH": "/usr/local/bin:/usr/bin",
        "PYTHONPATH": "/workspace",
        "CUSTOM_APP_CONFIG": "safe_public_setting",
    }

    clean_env = enforcer.sanitize_environment(custom_env=dirty_env)

    # 1. Verify all secrets are completely scrubbed
    assert "OPENAI_API_KEY" not in clean_env
    assert "GITHUB_APP_PRIVATE_KEY" not in clean_env
    assert "DATABASE_URL" not in clean_env
    assert "JWT_SECRET" not in clean_env
    assert "REDIS_URL" not in clean_env

    # 2. Verify safe variables and safety markers are present
    assert "PATH" in clean_env
    assert clean_env["CUSTOM_APP_CONFIG"] == "safe_public_setting"
    assert clean_env["OPENREVIEW_SANDBOX"] == "true"
    assert clean_env["SANDBOX_NETWORK_ISOLATED"] == "true"

    # 3. Resource quotas clamping
    bounds = enforcer.validate_resource_bounds(requested_cpu=10.0, requested_memory_mb=4096, requested_timeout_seconds=120)
    assert bounds["cpu_limit"] <= 1.0
    assert bounds["memory_limit_mb"] <= 512
    assert bounds["timeout_seconds"] <= 40

    # 4. Output truncation
    long_output = "A" * (2 * 1024 * 1024)  # 2MB
    truncated = enforcer.truncate_output(long_output)
    assert len(truncated) <= 1024 * 1024 + 200
    assert "Output truncated" in truncated


def test_sandbox_failure_explanation_extraction():
    """Validates that SandboxRunner extracts clear failure explanations from failing pytest tests."""
    runner = EphemeralSandboxRunner()

    failing_test_code = """import pytest

def test_deliberate_failure():
    expected_token = "correct_value"
    actual_token = "wrong_value"
    assert expected_token == actual_token, "Token validation mismatch error in sandbox"
"""

    result: SandboxExecutionResult = runner.run_test_suite(
        patched_files={"module.py": "def foo(): return 42\n"},
        test_code=failing_test_code,
        config=SandboxConfig(timeout_seconds=10),
    )

    assert result.status == "failed"
    assert result.exit_code != 0
    assert result.failed_tests >= 1
    assert result.failure_explanation is not None
    assert "test_deliberate_failure" in result.failure_explanation or "assert" in result.failure_explanation


def test_patch_applicability_and_diff_validation():
    """Tests unified diff parser, dry-run application, and rollback generation."""
    original = "line 1\nline 2\nline 3\n"
    proposed = "line 1\nline 2 modified\nline 3\n"

    diff = PatchApplier.compute_unified_diff(original, proposed, "test.py")
    is_valid, err = PatchApplier.validate_unified_diff(diff)
    assert is_valid is True
    assert err is None

    applies, patched, apply_err = PatchApplier.apply_diff(original, diff)
    assert applies is True
    assert patched == proposed
    assert apply_err is None

    # Rollback diff
    rollback = PatchApplier.generate_rollback_diff(original, proposed, "test.py")
    assert "--- a/test.py" in rollback
    rb_applies, rolled_back, _ = PatchApplier.apply_diff(proposed, rollback)
    assert rb_applies is True
    assert rolled_back == original

    # Malformed diff rejection
    bad_diff = "random text without unified diff headers"
    is_valid_bad, bad_err = PatchApplier.validate_unified_diff(bad_diff)
    assert is_valid_bad is False
    assert "Malformed diff" in bad_err
