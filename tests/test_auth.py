"""Authentication and Authorization integration tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_user_registration_success(async_client: AsyncClient):
    payload = {
        "email": "alice@example.com",
        "username": "alice",
        "full_name": "Alice Engineer",
        "password": "Password123!",
        "organization_name": "Alice Labs",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == "alice@example.com"
    assert data["user"]["username"] == "alice"
    assert "token" in data
    assert data["token"]["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_user_registration_duplicate_email(async_client: AsyncClient):
    payload = {
        "email": "dup@example.com",
        "username": "user1",
        "password": "Password123!",
    }
    res1 = await async_client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    payload2 = {
        "email": "dup@example.com",
        "username": "user2",
        "password": "Password123!",
    }
    res2 = await async_client.post("/api/v1/auth/register", json=payload2)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["error"]["message"]


@pytest.mark.asyncio
async def test_user_login_success(async_client: AsyncClient):
    reg = {
        "email": "bob@example.com",
        "username": "bob",
        "password": "SecurePassword99!",
    }
    await async_client.post("/api/v1/auth/register", json=reg)

    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "SecurePassword99!"},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "token" in data
    assert data["user"]["email"] == "bob@example.com"


@pytest.mark.asyncio
async def test_user_login_invalid_password(async_client: AsyncClient):
    reg = {
        "email": "carol@example.com",
        "username": "carol",
        "password": "CorrectPassword123!",
    }
    await async_client.post("/api/v1/auth/register", json=reg)

    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "carol@example.com", "password": "WrongPassword!"},
    )
    assert login_res.status_code == 401
    assert "Invalid email or password" in login_res.json()["error"]["message"]


@pytest.mark.asyncio
async def test_auth_me_unauthorized(async_client: AsyncClient):
    res = await async_client.get("/api/v1/auth/me")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_auth_me_authorized(async_client: AsyncClient, auth_headers: dict):
    res = await async_client.get("/api/v1/auth/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "developer@openreview.ai"
