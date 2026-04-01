"""Regression tests for experiment route precedence."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_static_experiment_routes_are_not_shadowed(async_client: AsyncClient):
    methods = await async_client.get("/api/v1/experiments/methods")
    datasets = await async_client.get("/api/v1/experiments/datasets")

    assert methods.status_code == 200
    assert methods.json() == []
    assert datasets.status_code == 200
    assert datasets.json() == []
