"""Tests for repository management endpoints, tenant isolation, and semantic indexing."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_list_repository(async_client: AsyncClient, auth_headers: dict):
    payload = {
        "github_repo_id": 998877,
        "owner": "google-deepmind",
        "name": "openreview-ai",
        "default_branch": "main",
        "description": "Multi-agent code review platform",
        "is_active": True,
    }

    # Register
    create_res = await async_client.post("/api/v1/repositories", json=payload, headers=auth_headers)
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["full_name"] == "google-deepmind/openreview-ai"
    assert created["id"] is not None

    repo_id = created["id"]

    # Retrieve by ID
    get_res = await async_client.get(f"/api/v1/repositories/{repo_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "openreview-ai"

    # Listing
    list_res = await async_client.get("/api/v1/repositories", headers=auth_headers)
    assert list_res.status_code == 200
    repos = list_res.json()
    assert len(repos) >= 1
    assert any(r["id"] == repo_id for r in repos)

    # Conflict on duplicate registration
    dup_res = await async_client.post("/api/v1/repositories", json=payload, headers=auth_headers)
    assert dup_res.status_code == 409
    assert dup_res.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_repository_semantic_indexing(async_client: AsyncClient):
    # Register repo
    payload = {
        "github_repo_id": 112233,
        "owner": "octocat",
        "name": "vector-search-repo",
        "default_branch": "main",
    }
    repo_res = await async_client.post("/api/v1/repositories", json=payload)
    assert repo_res.status_code == 201
    repo_id = repo_res.json()["id"]

    # Trigger semantic code indexing
    idx_payload = {
        "commit_sha": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        "branch": "main",
    }
    idx_res = await async_client.post(f"/api/v1/repositories/{repo_id}/indexes", json=idx_payload)
    assert idx_res.status_code == 201
    idx_data = idx_res.json()
    assert idx_data["repository_id"] == repo_id
    assert idx_data["total_chunks"] > 0
    assert idx_data["total_symbols"] > 0

    # List indexes
    list_idx_res = await async_client.get(f"/api/v1/repositories/{repo_id}/indexes")
    assert list_idx_res.status_code == 200
    assert len(list_idx_res.json()) >= 1
