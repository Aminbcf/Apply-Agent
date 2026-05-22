"""Runtime LLM settings API.

Endpoints
---------
GET  /settings/llm          Return current LLM configuration (API key is redacted).
POST /settings/llm          Update provider / key / model and hot-swap the adapter.
GET  /settings/llm/test     Send a test prompt and return latency.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

import model_registry
from config import settings
from AI.llm.llm_interface import get_llm_adapter


router = APIRouter(prefix="/settings", tags=["settings"])
logger = logging.getLogger(__name__)


# ── Schemas ───────────────────────────────────────────────────────────────────


class LlmSettingsOut(BaseModel):
    """Current LLM configuration returned to the frontend."""

    provider: str
    external_api_base_url: str
    external_api_model: str
    has_api_key: bool          # True when a key is configured (value never returned)
    llm_quantize_4bit: bool
    llm_max_new_tokens: int
    llm_use_torch_compile: bool
    active_adapter: str        # Class name of the loaded adapter


class LlmSettingsIn(BaseModel):
    """Payload for updating LLM settings at runtime."""

    provider: str = Field(..., description='"local" or "external"')
    external_api_base_url: Optional[str] = None
    external_api_key: Optional[str] = Field(
        default=None,
        description="API key for the external provider. Send an empty string to clear.",
    )
    external_api_model: Optional[str] = None
    llm_quantize_4bit: Optional[bool] = None
    llm_max_new_tokens: Optional[int] = None


class LlmTestOut(BaseModel):
    """Result of the /settings/llm/test probe."""

    ok: bool
    latency_ms: float
    model_used: str
    provider: str
    error: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/llm")
async def get_llm_settings() -> LlmSettingsOut:
    """Return current LLM configuration.

    The ``external_api_key`` is never included in the response — only
    ``has_api_key`` (bool) is returned so the frontend can show a lock icon.
    """
    return LlmSettingsOut(
        provider=settings.llm_provider,
        external_api_base_url=settings.external_api_base_url,
        external_api_model=settings.external_api_model,
        has_api_key=bool(settings.external_api_key),
        llm_quantize_4bit=settings.llm_quantize_4bit,
        llm_max_new_tokens=settings.llm_max_new_tokens,
        llm_use_torch_compile=settings.llm_use_torch_compile,
        active_adapter=model_registry.get_llm_provider(),
    )


@router.post("/llm")
async def update_llm_settings(payload: LlmSettingsIn) -> LlmSettingsOut:
    """Update LLM provider / key / model and hot-swap the adapter.

    This endpoint does NOT restart the server.  It constructs a new adapter
    from the supplied settings and calls :func:`~model_registry.swap_llm`.

    If ``provider == "external"`` and ``external_api_key`` is provided,
    the key is validated by sending a minimal test request before swapping.
    """
    current_settings = settings
    provider = payload.provider.lower()
    updates: dict = {"llm_provider": provider}

    if payload.external_api_base_url is not None:
        updates["external_api_base_url"] = payload.external_api_base_url
    if payload.external_api_key is not None:
        updates["external_api_key"] = payload.external_api_key
    if payload.external_api_model is not None:
        updates["external_api_model"] = payload.external_api_model
    if payload.llm_quantize_4bit is not None:
        updates["llm_quantize_4bit"] = payload.llm_quantize_4bit
    if payload.llm_max_new_tokens is not None:
        updates["llm_max_new_tokens"] = payload.llm_max_new_tokens

    # Apply updates to the Settings singleton (mutable via __dict__ on pydantic v2)
    for key, value in updates.items():
        object.__setattr__(current_settings, key, value)

    log_updates = updates.copy()
    if "external_api_key" in log_updates:
        log_updates["external_api_key"] = "***"
    logger.info("LLM settings updated: %s", log_updates)

    # Build the new adapter and hot-swap
    new_adapter = get_llm_adapter(current_settings)
    model_registry.swap_llm(new_adapter)

    return LlmSettingsOut(
        provider=current_settings.llm_provider,
        external_api_base_url=current_settings.external_api_base_url,
        external_api_model=current_settings.external_api_model,
        has_api_key=bool(current_settings.external_api_key),
        llm_quantize_4bit=current_settings.llm_quantize_4bit,
        llm_max_new_tokens=current_settings.llm_max_new_tokens,
        llm_use_torch_compile=current_settings.llm_use_torch_compile,
        active_adapter=model_registry.get_llm_provider(),
    )


@router.get("/llm/test")
async def test_llm_connection() -> LlmTestOut:
    """Send a minimal prompt to the active LLM and return latency.

    Used by the frontend "Test Connection" button to verify the current
    provider is reachable and the API key is valid.
    """
    test_prompt = "Reply with exactly: OK"
    t0 = time.perf_counter()

    try:
        llm = model_registry.get_llm()
        llm.generate(test_prompt)
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        model_used = (
            settings.external_api_model
            if settings.is_external_provider
            else "local/qwen"
        )
        return LlmTestOut(
            ok=True,
            latency_ms=latency_ms,
            model_used=model_used,
            provider=settings.llm_provider,
        )
    except Exception as exc:  # noqa: BLE001
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        logger.warning("LLM test failed: %s", exc)
        return LlmTestOut(
            ok=False,
            latency_ms=latency_ms,
            model_used="unknown",
            provider=settings.llm_provider,
            error=str(exc)[:300],
        )
