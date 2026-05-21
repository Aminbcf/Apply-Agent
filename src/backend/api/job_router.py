"""FastAPI router for the job-match scenario (Phase 7).

Endpoints
---------
POST   /jobs/evaluate            Evaluate a job offer (returns score immediately)
GET    /jobs/{job_id}/status     Poll PDF generation progress
GET    /jobs/{job_id}/download   Stream CV / cover letter PDF or LaTeX source
PATCH  /jobs/{job_id}/status     Update workflow status (accept/reject/pending)
PATCH  /jobs/{job_id}/latex      Save user-edited LaTeX source
POST   /jobs/{job_id}/regenerate Re-render PDF from stored LaTeX (background)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from AI.llm.job_match_service import JobMatchService
from database import get_db
from models.job_application import JobApplication
from schemas.job_schemas import (
    JobEvaluationOut,
    JobOfferIn,
    JobStatusOut,
    LatexUpdate,
    WorkflowStatusUpdate,
)

router = APIRouter(prefix="/jobs", tags=["jobs"])
logger = logging.getLogger(__name__)

DbDep = Annotated[AsyncSession, Depends(get_db)]


# ── Helper ────────────────────────────────────────────────────

async def _get_job_or_404(job_id: str, db: AsyncSession) -> JobApplication:
    """Fetch a JobApplication by string UUID, raising 404 if absent or invalid."""
    try:
        job_uuid = UUID(job_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    result = await db.execute(
        select(JobApplication).where(JobApplication.id == job_uuid)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


def _make_service(db: AsyncSession) -> JobMatchService:
    return JobMatchService(db=db)


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/evaluate", status_code=202)
async def evaluate_job(
    payload: JobOfferIn,
    background_tasks: BackgroundTasks,
    db: DbDep,
) -> JobEvaluationOut:
    """Evaluate a job offer against the candidate's CV/cover-letter context.

    Returns immediately with dimension scores and an overall match percentage.
    PDF generation is kicked off as a background task; poll
    ``GET /jobs/{job_id}/status`` until ``processing`` is ``false``.
    """
    service = _make_service(db)

    result = await service.evaluate_job(
        title=payload.title,
        company=payload.company,
        description=payload.description,
        session_id=payload.session_id,
    )

    # Enqueue PDF generation without blocking the response
    background_tasks.add_task(service.generate_documents, str(result.job_id))

    logger.info(
        "Job %s queued for PDF generation (score=%.1f%%)",
        result.job_id,
        result.overall_score,
    )
    return result


@router.get("/{job_id}/status", responses={404: {"description": "Not found"}})
async def get_job_status(job_id: str, db: DbDep) -> JobStatusOut:
    """Poll the processing state and PDF availability of a job evaluation."""
    job = await _get_job_or_404(job_id, db)

    def _pdf_url(path: str | None, file_type: str) -> str | None:
        if not path:
            return None
        return f"/jobs/{job_id}/download?file_type={file_type}"

    return JobStatusOut(
        job_id=job.id,
        processing=job.processing,
        cv_pdf_url=_pdf_url(job.cv_pdf_path, "cv"),
        cover_letter_pdf_url=_pdf_url(job.cover_letter_pdf_path, "cover"),
        workflow_status=job.workflow_status,
    )


@router.get("/{job_id}/download", responses={404: {"description": "Not found"}})
async def download_file(
    job_id: str,
    file_type: Annotated[
        Literal["cv", "cover", "cv_latex", "cover_latex"],
        Query(description="cv | cover | cv_latex | cover_latex"),
    ],
    db: DbDep,
):
    """Download a compiled PDF or raw LaTeX source for a job application.

    - ``cv`` / ``cover``           → PDF file (``application/pdf``)
    - ``cv_latex`` / ``cover_latex`` → LaTeX source (``text/plain``)
    """
    job = await _get_job_or_404(job_id, db)

    if file_type == "cv":
        if not job.cv_pdf_path or not Path(job.cv_pdf_path).exists():
            raise HTTPException(status_code=404, detail="CV PDF not yet generated")
        return FileResponse(job.cv_pdf_path, media_type="application/pdf", filename="cv.pdf")

    if file_type == "cover":
        if not job.cover_letter_pdf_path or not Path(job.cover_letter_pdf_path).exists():
            raise HTTPException(status_code=404, detail="Cover letter PDF not yet generated")
        return FileResponse(
            job.cover_letter_pdf_path,
            media_type="application/pdf",
            filename="cover_letter.pdf",
        )

    if file_type == "cv_latex":
        if not job.cv_latex:
            raise HTTPException(status_code=404, detail="CV LaTeX source not available")
        return {"latex": job.cv_latex}

    # cover_latex
    if not job.cover_letter_latex:
        raise HTTPException(status_code=404, detail="Cover letter LaTeX source not available")
    return {"latex": job.cover_letter_latex}


@router.patch("/{job_id}/status", responses={404: {"description": "Not found"}})
async def update_workflow_status(
    job_id: str,
    payload: WorkflowStatusUpdate,
    session_id: Annotated[str | None, Query()] = None,
    db: DbDep = None,
) -> dict:
    """Update the workflow status of a job application.

    On ``rejected``, pass ``?session_id=<id>`` to clear the RAG history cache.
    """
    service = _make_service(db)
    job = await service.update_workflow_status(
        job_id=job_id,
        status=payload.status,
        session_id=session_id,
    )
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return {"job_id": str(job.id), "workflow_status": job.workflow_status}


@router.patch("/{job_id}/latex", responses={404: {"description": "Not found"}})
async def update_latex(
    job_id: str,
    payload: LatexUpdate,
    db: DbDep,
) -> dict:
    """Save user-edited LaTeX source without triggering a re-render.

    Call ``POST /jobs/{job_id}/regenerate`` afterwards to compile the new PDF.
    """
    service = _make_service(db)
    job = await service.update_latex(
        job_id=job_id,
        doc_type=payload.doc_type,
        latex_source=payload.latex_source,
    )
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return {"job_id": str(job.id), "doc_type": payload.doc_type, "saved": True}


@router.post("/{job_id}/regenerate", status_code=202, responses={404: {"description": "Not found"}})
async def regenerate_pdf(
    job_id: str,
    doc_type: Annotated[Literal["cv", "cover"], Body(embed=True)],
    background_tasks: BackgroundTasks,
    db: DbDep,
) -> dict:
    """Re-compile a PDF from the currently stored LaTeX source.

    Useful after the user edits the LaTeX source in the frontend editor.
    Returns 202 immediately; poll ``GET /jobs/{job_id}/status`` for completion.
    """
    # Verify job exists before enqueueing
    job = await _get_job_or_404(job_id, db)

    service = _make_service(db)
    background_tasks.add_task(service.regenerate_pdf, str(job.id), doc_type)

    logger.info("Re-render queued for job %s", str(job.id))
    return {"job_id": str(job.id), "doc_type": doc_type, "queued": True}
