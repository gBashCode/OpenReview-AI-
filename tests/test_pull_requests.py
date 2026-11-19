"""Tests for pull request registration, retrieval, and status tracking."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_pull_request_lifecycle(async_client: AsyncClient):
    # Register repository first
    repo_res = await async_client.post(
        "/api/v1/repositories",
        json={
            "github_repo_id": 883311,
            "owner": "fastapi",
            "name": "fastapi-demo",
            "default_branch": "main",
        },
    )
    assert repo_res.status_code == 201
    repo_id = repo_res.json()["id"]

    # Register PR
    pr_payload = {
        "repository_id": repo_id,
        "pr_number": 42,
        "title": "fix: resolve SQL injection vulnerability in search query",
        "head_branch": "fix/search-sanitization",
        "base_branch": "main",
        "head_sha": "1111222233334444555566667777888899990000",
        "base_sha": "0000999988887777666655554444333322221111",
        "author_username": "sec-dev",
    }
    pr_res = await async_client.post("/api/v1/pull-requests", json=pr_payload)
    assert pr_res.status_code == 201
    pr_data = pr_res.json()
    assert pr_data["pr_number"] == 42
    assert pr_data["title"] == "fix: resolve SQL injection vulnerability in search query"
    pr_id = pr_data["id"]

    # Get by ID
    get_res = await async_client.get(f"/api/v1/pull-requests/{pr_id}")
    assert get_res.status_code == 200
    assert get_res.json()["author_username"] == "sec-dev"

    # List PRs filtered by repo
    list_res = await async_client.get(f"/api/v1/pull-requests?repository_id={repo_id}")
    assert list_res.status_code == 200
    prs = list_res.json()
    assert len(prs) == 1
    assert prs[0]["id"] == pr_id
