"""Singleton model registry – eagerly loads all ML models at startup.

Loaded during the FastAPI ``lifespan`` event so the first user request
is fast.  Access pre-loaded instances via the getter functions::

    from model_registry import get_llm, get_embedder, get_domain_manager

    llm = get_llm()             # active LLMAdapter (local or external)
    emb = get_embedder()        # SentenceTransformerAdapter
    dom = get_domain_manager()  # DomainEmbeddingManager

Hot-swapping the LLM at runtime
--------------------------------
When the user changes the provider via ``POST /settings/llm``, call
:func:`swap_llm` with the new adapter instance.  All subsequent calls
to :func:`get_llm` will return the new adapter without restarting.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

# ── Module-level singletons ──────────────────────────────────
_llm: Optional[object] = None
_embedder: Optional[object] = None
_domain_manager: Optional[object] = None
_ready: bool = False


# ── Synchronous loaders (run in thread pool) ─────────────────


def _load_llm():
    """Load the active LLM adapter (local LoRA or external API)."""
    from AI.llm.llm_interface import get_llm_adapter  # noqa: PLC0415
    from config import settings  # noqa: PLC0415

    t0 = time.perf_counter()
    adapter = get_llm_adapter(settings)
    elapsed = time.perf_counter() - t0
    logger.info(
        "LLM adapter loaded in %.1fs (provider=%s)",
        elapsed,
        settings.llm_provider,
    )
    return adapter


def _load_embedder():
    """Load the SentenceTransformer embedding model."""
    from AI.llm.embedding_service import SentenceTransformerAdapter  # noqa: PLC0415

    t0 = time.perf_counter()
    adapter = SentenceTransformerAdapter()
    elapsed = time.perf_counter() - t0
    logger.info("SentenceTransformerAdapter loaded in %.1fs", elapsed)
    return adapter


def _load_domain_manager():
    """Load and pre-compute domain embeddings."""
    from AI.domain_embeddings import DomainEmbeddingManager  # noqa: PLC0415

    t0 = time.perf_counter()
    manager = DomainEmbeddingManager()
    elapsed = time.perf_counter() - t0
    logger.info("DomainEmbeddingManager loaded in %.1fs", elapsed)
    return manager


# ── Public API ────────────────────────────────────────────────


async def initialize() -> None:
    """Eagerly load all ML models in background threads.

    Called once during the FastAPI ``lifespan`` startup.  Each heavy
    load runs via :func:`asyncio.to_thread` so the event loop stays
    responsive.

    When ``LLM_PROVIDER=external``, the LLM "load" is nearly instant
    (just constructs an httpx client wrapper) — startup is fast even
    without a GPU.
    """
    global _llm, _embedder, _domain_manager, _ready  # noqa: PLW0603

    from config import settings  # noqa: PLC0415

    logger.info(
        "model_registry: starting model loading (provider=%s) …",
        settings.llm_provider,
    )
    t0 = time.perf_counter()

    # Always load embedder and domain manager (lightweight, needed for scoring)
    _embedder, _domain_manager = await asyncio.gather(
        asyncio.to_thread(_load_embedder),
        asyncio.to_thread(_load_domain_manager),
    )

    # Load the LLM adapter (may download / quantise the local model)
    _llm = await asyncio.to_thread(_load_llm)

    _ready = True
    elapsed = time.perf_counter() - t0
    logger.info("model_registry: all models ready in %.1fs", elapsed)


def get_llm():
    """Return the active LLM adapter, or raise if not yet loaded."""
    if _llm is None:
        raise RuntimeError(
            "LLM not loaded yet. "
            "Ensure model_registry.initialize() was awaited during lifespan."
        )
    return _llm


def swap_llm(new_adapter) -> None:
    """Hot-swap the active LLM adapter without restarting the server.

    Called by ``POST /settings/llm`` after the user changes provider settings.
    Thread-safe for read (GIL protects the simple assignment).

    Parameters
    ----------
    new_adapter:
        An initialised :class:`~AI.llm.llm_interface.LLMAdapter` subclass.
    """
    global _llm  # noqa: PLW0603
    old_provider = type(_llm).__name__ if _llm is not None else "None"
    _llm = new_adapter
    logger.info(
        "model_registry: LLM hot-swapped %s → %s",
        old_provider,
        type(new_adapter).__name__,
    )


def get_embedder():
    """Return the pre-loaded SentenceTransformerAdapter."""
    if _embedder is None:
        raise RuntimeError(
            "Embedding model not loaded yet. "
            "Ensure model_registry.initialize() was awaited during lifespan."
        )
    return _embedder


def get_domain_manager():
    """Return the pre-loaded DomainEmbeddingManager."""
    if _domain_manager is None:
        raise RuntimeError(
            "Domain manager not loaded yet. "
            "Ensure model_registry.initialize() was awaited during lifespan."
        )
    return _domain_manager


def get_llm_provider() -> str:
    """Return the name of the currently active provider class."""
    if _llm is None:
        return "none"
    return type(_llm).__name__


def is_external_provider() -> bool:
    """True when the active adapter is :class:`~AI.llm.llm_interface.ExternalApiAdapter`."""
    from AI.llm.llm_interface import ExternalApiAdapter  # noqa: PLC0415
    return isinstance(_llm, ExternalApiAdapter)


def is_ready() -> bool:
    """Return ``True`` if all models have been loaded."""
    return _ready
