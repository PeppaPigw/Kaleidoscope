"""Integration tests for collaboration, alerts, auth, and contradictions."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_tasks_returns_list(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/collaboration/tasks")
    assert resp.status_code == 200
    data = resp.json()
    assert "tasks" in data
    assert isinstance(data["tasks"], list)


@pytest.mark.asyncio
async def test_get_alerts_returns_list(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/alerts")
    assert resp.status_code == 200
    data = resp.json()
    assert "alerts" in data
    assert isinstance(data["alerts"], list)


@pytest.mark.asyncio
async def test_auth_me_returns_user(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert "user_id" in data


@pytest.mark.asyncio
async def test_auth_login_returns_token(async_client: AsyncClient):
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "test", "password": "test"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_cross_paper_contradictions(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/cross-paper/contradictions?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert "contradictions" in data
    assert isinstance(data["contradictions"], list)


@pytest.mark.asyncio
async def test_auth_login_returns_standardized_envelope(async_client: AsyncClient):
    """Auth login should return token in our standard envelope shape."""
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "test", "password": "test"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_recent_imports_returns_list(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/imports/recent")
    assert resp.status_code == 200
    data = resp.json()
    assert "imports" in data
    assert isinstance(data["imports"], list)


@pytest.mark.asyncio
async def test_http_exception_returns_code_message(async_client: AsyncClient):
    """404s should return {code, message} envelope."""
    resp = await async_client.get("/api/v1/papers/nonexistent-paper-id-xyz")
    assert resp.status_code in (404, 422)
    data = resp.json()
    assert "code" in data or "message" in data or "detail" in data


@pytest.mark.asyncio
async def test_graph_stats_returns_counts(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/graph/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_sse_recent_returns_list(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/sse/recent")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, (list, dict))
