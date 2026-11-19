"""Tests for repository management endpoints and business logic."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_list_repository(async_client: AsyncClient):
    payload = {
        "github_repo_id": 998877,
        "owner": "google-deepmind",
        "name": "openreview-ai",
        "default_branch": "main",
        "description": "Multi-agent code review platform",
        "is_active": True,
    }

    # Register
    create_res = await async_client.post("/api/v1/repositories", json=payload)
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["full_name"] == "google-deepmind/openreview-ai"
    assert created["id"] is not None

    repo_id = created["id"]

    # Retrieve by ID
    get_res = await async_client.get(f"/api/v1/repositories/{repo_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "openreview-ai"

    # Listing
    list_res = await async_client.get("/api/v1/repositories")
    assert list_res.status_code == 200
    repos = list_res.json()
    assert len(repos) >= 1
    assert any(r["id"] == repo_id for r in repos)

    # Conflict on duplicate registration
    dup_res = await async_client.post("/api/v1/repositories", json=payload)
    assert dup_res.status_code == 409
    assert dup_res.json()["error"]["code"] == "CONFLICT"
