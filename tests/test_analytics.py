"""Tests for Enterprise Audit Logging and Analytics Statistics."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_analytics_and_audit_logging(async_client: AsyncClient, auth_headers: dict):
    # Fetch org
    org_res = await async_client.get("/api/v1/organizations", headers=auth_headers)
    org_id = org_res.json()[0]["id"]

    # Register repo
    repo_res = await async_client.post(
        "/api/v1/repositories",
        json={
            "github_repo_id": 445566,
            "owner": "analytics-corp",
            "name": "metrics-engine",
            "organization_id": org_id,
        },
        headers=auth_headers,
    )
    assert repo_res.status_code == 201

    # Check stats
    stats_res = await async_client.get(
        f"/api/v1/analytics/stats?organization_id={org_id}",
        headers=auth_headers,
    )
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "active_repositories" in stats
    assert stats["active_repositories"] >= 1
    assert "avg_quality_score" in stats

    # List audit logs
    audit_res = await async_client.get(
        f"/api/v1/analytics/audit-logs?organization_id={org_id}",
        headers=auth_headers,
    )
    assert audit_res.status_code == 200
    assert isinstance(audit_res.json(), list)
