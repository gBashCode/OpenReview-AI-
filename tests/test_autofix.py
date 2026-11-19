"""Tests for Autofix patches, human decisions, and sandbox test execution."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_patch_approval_and_test_run(async_client: AsyncClient):
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
