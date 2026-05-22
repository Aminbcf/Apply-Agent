"""SSE streaming endpoint for real-time CV / cover-letter generation.

POST /jobs/generate-stream
    Accepts ``{ "job_id": "<uuid>" }`` and returns a ``text/event-stream``
    response with incremental tokens.

SSE Event Types
---------------
``cv_token``          Single token of the CV being generated
``cv_complete``       Full CV text (sent once generation finishes)
``cover_token``       Single token of the cover letter being generated
``cover_complete``    Full cover-letter text (sent once generation finishes)
``error``             An error occurred during generation
``done``              Generation finished; includes timing metadata
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from AI.llm.llm_interface import ExternalApiAdapter, build_rag_prompt
from AI.llm.batch_generator import generate_cv_sections, generate_cover_letter_stream
from AI.llm.cv_assembler import assemble_cv_latex
from AI.llm.rag_service import (
    retrieve_cv_context,
    retrieve_job_context,
    retrieve_few_shot_examples,
    retrieve_example_files,
)
from config import settings
from database import get_db
from models.job_application import JobApplication
import model_registry

router = APIRouter(prefix="/jobs", tags=["jobs-stream"])
logger = logging.getLogger(__name__)

DbDep = Annotated[AsyncSession, Depends(get_db)]


class GenerateStreamIn(BaseModel):
    """Request body for the streaming generation endpoint."""

    job_id: str = Field(..., description="UUID of the evaluated job")


async def _sse_generator(job_id: str, db: AsyncSession):
    """Async generator that yields SSE events for CV and cover letter tokens."""
    t_start = time.perf_counter()

    # Validate job ID
    try:
        job_uuid = UUID(job_id)
    except (ValueError, AttributeError):
        yield _sse_event("error", {"message": f"Invalid job ID: {job_id}"})
        return

    # Fetch job record
    result = await db.execute(
        select(JobApplication).where(JobApplication.id == job_uuid)
    )
    job = result.scalar_one_or_none()
    if job is None:
        yield _sse_event("error", {"message": f"Job {job_id} not found"})
        return

    llm = model_registry.get_llm()

    # ── Retrieve full RAG context ────────────────────────────────────────────
    try:
        cv_context = await retrieve_cv_context(db)
        job_context = await retrieve_job_context(db, job_id)
        few_shot = await retrieve_few_shot_examples(
            db,
            limit=settings.rag_few_shot_limit,
            max_chars=settings.rag_example_max_chars,
        )
        example_files = retrieve_example_files(max_chars=settings.rag_example_max_chars)
    except Exception as exc:  # noqa: BLE001
        logger.exception("RAG context retrieval failed for job %s", job_id)
        yield _sse_event("error", {"message": f"Context retrieval failed: {exc}"})
        return

    # ── Multiplex Generation ─────────────────────────────────────────────────
    cv_sections = {}
    cl_sections = {}
    cv_full = ""
    cl_full = ""

    queue = asyncio.Queue()

    async def worker(gen, prefix):
        try:
            async for event_type, payload in gen:
                await queue.put((event_type, payload, prefix))
        except Exception as exc:
            logger.exception("%s generation failed for job %s", prefix.upper(), job_id)
            await queue.put(("error", str(exc), prefix))
        finally:
            await queue.put(("worker_done", None, prefix))

    cv_gen = generate_cv_sections(llm, cv_context, job_context, few_shot, example_files)
    cl_gen = generate_cover_letter_stream(llm, cv_context, job_context, few_shot, example_files)

    task1 = asyncio.create_task(worker(cv_gen, "cv"))
    task2 = asyncio.create_task(worker(cl_gen, "cover"))

    finished_workers = 0
    while finished_workers < 2:
        event_type, payload, prefix = await queue.get()

        if event_type == "worker_done":
            finished_workers += 1
        elif event_type == "error":
            yield _sse_event("error", {"message": f"{prefix.upper()} generation failed: {payload}"})
        elif event_type == "final":
            if prefix == "cv":
                cv_sections = payload
                cv_full = assemble_cv_latex(cv_sections)
                yield _sse_event("cv_complete", {"text": cv_full})
            else:
                cl_full = payload
                yield _sse_event("cover_complete", {"text": cl_full})
        elif event_type == "token":
            if prefix == "cover":
                yield _sse_event("cover_token", {"token": payload})
        elif event_type == "start":
            if prefix == "cv":
                yield _sse_event("cv_section_start", {"section": payload})
        elif event_type == "done":
            if prefix == "cv":
                yield _sse_event("cv_section_done", {"section": payload, "ok": True})

    # Wait for tasks to cleanly exit
    await asyncio.gather(task1, task2, return_exceptions=True)


    # ── Persist generated text to DB ─────────────────────────────────────────
    try:
        result = await db.execute(
            select(JobApplication).where(JobApplication.id == job_uuid)
        )
        job = result.scalar_one_or_none()
        if job:
            job.cv_text = cv_full
            job.cover_letter_text = cl_full
            job.processing = False
            await db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to persist generated text for job %s: %s", job_id, exc)

    elapsed = round(time.perf_counter() - t_start, 2)
    yield _sse_event("done", {
        "job_id": job_id,
        "elapsed_seconds": elapsed,
        "provider": settings.llm_provider,
        "model": settings.external_api_model if settings.is_external_provider else "local/qwen",
    })


def _sse_event(event: str, data: dict) -> str:
    """Format a single SSE event string."""
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


@router.post("/generate-stream")
async def generate_stream(payload: GenerateStreamIn, db: DbDep):
    """Stream CV and cover letter generation tokens via Server-Sent Events.

    The response is ``text/event-stream``.  The frontend should use
    ``fetch()`` with ``ReadableStream`` or ``EventSource`` to consume it.
    """
    # Verify job exists before starting the stream
    try:
        job_uuid = UUID(payload.job_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=404, detail=f"Invalid job ID: {payload.job_id}")

    result = await db.execute(
        select(JobApplication).where(JobApplication.id == job_uuid)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {payload.job_id} not found")

    # Mark as processing
    job.processing = True
    await db.commit()

    return StreamingResponse(
        _sse_generator(payload.job_id, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
