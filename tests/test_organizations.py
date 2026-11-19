"""Organization and Member RBAC integration tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_and_create_organization(async_client: AsyncClient, auth_headers: dict):
    # Registration in auth_headers fixture created "Acme Engineering"
    list_res = await async_client.get("/api/v1/organizations", headers=auth_headers)
    assert list_res.status_code == 200
    orgs = list_res.json()
    assert len(orgs) >= 1
    assert orgs[0]["name"] == "Acme Engineering"

    # Create second organization
    create_payload = {
        "name": "Beta Research Corp",
        "slug": "beta-research",
        "plan": "enterprise",
    }
    create_res = await async_client.post("/api/v1/organizations", json=create_payload, headers=auth_headers)
    assert create_res.status_code == 201
    created_org = create_res.json()
    assert created_org["slug"] == "beta-research"
    assert created_org["plan"] == "enterprise"


@pytest.mark.asyncio
async def test_organization_member_management(async_client: AsyncClient, auth_headers: dict):
    # Get current org
    list_res = await async_client.get("/api/v1/organizations", headers=auth_headers)
    org_id = list_res.json()[0]["id"]

    # Register a new user to invite
    invitee_payload = {
        "email": "invitee@openreview.ai",
        "username": "invitee",
        "password": "Password123!",
    }
    invitee_res = await async_client.post("/api/v1/auth/register", json=invitee_payload)
    invitee_id = invitee_res.json()["user"]["id"]

    # Add member to organization
    add_res = await async_client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"user_id": invitee_id, "role": "reviewer"},
        headers=auth_headers,
    )
    assert add_res.status_code == 201
    member_data = add_res.json()
    assert member_data["user_id"] == invitee_id
    assert member_data["role"] == "reviewer"

    # List members
    members_res = await async_client.get(
        f"/api/v1/organizations/{org_id}/members",
        headers=auth_headers,
    )
    assert members_res.status_code == 200
    members = members_res.json()
    assert len(members) == 2

    # Update role to maintainer
    update_role_res = await async_client.patch(
        f"/api/v1/organizations/{org_id}/members/{invitee_id}",
        json={"role": "maintainer"},
        headers=auth_headers,
    )
    assert update_role_res.status_code == 200
    assert update_role_res.json()["role"] == "maintainer"

    # Remove member
    del_res = await async_client.delete(
        f"/api/v1/organizations/{org_id}/members/{invitee_id}",
        headers=auth_headers,
    )
    assert del_res.status_code == 204
