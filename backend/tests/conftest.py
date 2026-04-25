"""Tests conftest — shared fixtures."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

pytest_plugins = ("pytest_asyncio.plugin",)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest_asyncio.fixture
async def async_client(monkeypatch):
    """HTTP client with a minimal mocked DB for route smoke tests."""
    from app.config import settings
    from app.dependencies import get_db
    from app.main import app

    monkeypatch.setattr(settings, "admin_username", "test")
    monkeypatch.setattr(settings, "admin_password", "test")

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalar.return_value = 0
    mock_result.scalar_one_or_none.return_value = None

    db = MagicMock()
    db.execute = AsyncMock(return_value=mock_result)

    async def mock_db():
        yield db

    app.dependency_overrides[get_db] = mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-API-Key": "sk-kaleidoscope"},
        ) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
