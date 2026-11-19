"""Tests for pull request reviews and multi-agent simulation."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_review_simulation_workflow(async_client: AsyncClient):
    # 1. Create a repository
    repo_res = await async_client.post(
        "/api/v1/repositories",
        json={
            "github_repo_id": 12345,
            "owner": "test-org",
            "name": "sample-service",
            "default_branch": "main",
        },
    )
    assert repo_res.status_code == 201
    repo_id = repo_res.json()["id"]

    # 2. Create a pull request
    pr_res = await async_client.post(
        "/api/v1/pull-requests",
        json={
            "repository_id": repo_id,
            "pr_number": 1,
            "title": "feat: critical payments feature",
            "head_branch": "feature/payments",
            "base_branch": "main",
            "head_sha": "abc1234567890abcdef1234567890abcdef12345",
            "base_sha": "def1234567890abcdef1234567890abcdef12345",
            "author_username": "developer1",
        },
    )
    assert pr_res.status_code == 201
    pr_id = pr_res.json()["id"]

    # 3. Trigger a review
    review_res = await async_client.post(
        "/api/v1/reviews",
        json={
            "pull_request_id": pr_id,
            "commit_sha": "abc1234567890abcdef1234567890abcdef12345",
        },
    )
    assert review_res.status_code == 201
    review_id = review_res.json()["id"]
    assert review_res.json()["status"] == "pending"

    # 4. Run AI pass simulation
    sim_res = await async_client.post(f"/api/v1/reviews/{review_id}/simulate-ai-pass")
    assert sim_res.status_code == 200
    completed_review = sim_res.json()
    assert completed_review["status"] == "completed"
    assert completed_review["score"] is not None
    assert completed_review["findings_count"] > 0
    assert len(completed_review["comments"]) > 0
