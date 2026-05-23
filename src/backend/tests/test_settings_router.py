"""Tests for the settings API router (GET/POST/test endpoints).

All DB and model interactions are mocked so tests run in milliseconds.

The settings_router imports `settings` lazily inside function bodies via
`from config import settings`, so we patch `config.settings` directly.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture()
def anyio_backend():
    return "asyncio"


@pytest.fixture()
async def client():
    """FastAPI test client that skips lifespan model loading."""
    from fastapi import FastAPI
    from api.settings_router import router

    app = FastAPI()
    app.include_router(router)

    # Stub model_registry so no real model is needed
    import model_registry as mr
    mr._ready = True
    mr._llm = MagicMock()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="https://testserver"
    ) as c:
        yield c


def _mock_settings(
    provider="local",
    api_key="",
    quantize=True,
    max_tokens=1024,
    compile_=False,
):
    """Helper: build a settings mock with sensible defaults."""
    s = MagicMock()
    s.llm_provider = provider
    s.external_api_base_url = "https://openrouter.ai/api/v1"
    s.external_api_model = "openai/gpt-4o-mini"
    s.external_api_key = api_key
    s.external_api_timeout = 30
    s.llm_quantize_4bit = quantize
    s.llm_max_new_tokens = max_tokens
    s.llm_use_torch_compile = compile_
    s.is_external_provider = (provider == "external")
    return s


@pytest.mark.anyio
async def test_get_llm_settings_returns_structure(client):
    """GET /settings/llm returns the expected JSON shape."""
    with patch("config.settings", _mock_settings()), \
         patch("model_registry.get_llm_provider", return_value="MockAdapter"):
        resp = await client.get("/settings/llm")

    assert resp.status_code == 200
    data = resp.json()
    assert "provider" in data
    assert "has_api_key" in data
    assert data["has_api_key"] is False  # empty key


@pytest.mark.anyio
@pytest.mark.anyio
async def test_test_llm_connection_returns_ok(client):
    """GET /settings/llm/test returns ok=True when adapter generates successfully."""
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "OK"

    with patch("config.settings", _mock_settings()), \
         patch("model_registry.get_llm", return_value=mock_llm):
        resp = await client.get("/settings/llm/test")

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["latency_ms"] >= 0


@pytest.mark.anyio
async def test_test_llm_connection_returns_error_on_failure(client):
    """GET /settings/llm/test returns ok=False when adapter raises."""
    with patch("config.settings", _mock_settings(provider="external")), \
         patch("model_registry.get_llm", side_effect=RuntimeError("Connection refused")):
        resp = await client.get("/settings/llm/test")

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is False
    assert "error" in data
