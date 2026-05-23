"""Pydantic schemas for the job‑match scenario (Phase 7+8)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

# Valid workflow statuses
WorkflowStatus = Literal["pending", "accepted", "rejected", "interview", "ghosted"]


class JobOfferIn(BaseModel):
    """Incoming payload for a job evaluation request."""

    title: str = Field(..., min_length=1, description="Job title")
    company: str = Field(..., min_length=1, description="Company name")
    description: str = Field(..., min_length=10, description="Full job description text")
    session_id: str = Field(..., description="Active RAG session identifier")


class DimensionScores(BaseModel):
    """Per-dimension match scores, each in the range 0–100."""

    job_match: float = Field(..., ge=0, le=100, description="Overall semantic similarity score")
    skill_match: float = Field(..., ge=0, le=100, description="Checklist skill overlap score")
    education_match: float = Field(..., ge=0, le=100, description="Education level + field alignment score")
    experience_match: float = Field(..., ge=0, le=100, description="Years and domain experience overlap score")
    objective_match: float = Field(..., ge=0, le=100, description="Career objective alignment score")


class JobEvaluationOut(BaseModel):
    """Response returned immediately after POSTing a job offer for evaluation."""

    job_id: UUID
    overall_score: float = Field(..., ge=0, le=100, description="Weighted aggregate of all dimension scores")
    dimension_scores: DimensionScores
    workflow_status: WorkflowStatus = "pending"
    processing: bool = Field(
        default=True,
        description="True while generation or pdflatex compilation is running",
    )
    cv_pdf_url: str | None = None
    cover_letter_pdf_url: str | None = None


class JobStatusOut(BaseModel):
    """Polling response for PDF generation progress."""

    job_id: UUID
    processing: bool
    cv_pdf_url: str | None = None
    cover_letter_pdf_url: str | None = None
    workflow_status: WorkflowStatus


class WorkflowStatusUpdate(BaseModel):
    """Payload for PATCH /jobs/{job_id}/status."""

    status: WorkflowStatus


class LatexUpdate(BaseModel):
    """Payload for PATCH /jobs/{job_id}/latex."""

    doc_type: Literal["cv", "cover"]
    latex_source: str = Field(..., min_length=1)


class JobConfirmIn(BaseModel):
    """Payload for POST /jobs/{job_id}/confirm — user confirms edited documents."""

    cv_text: str = Field(..., min_length=1, description="Final CV markdown text")
    cover_letter_text: str = Field(..., min_length=1, description="Final cover letter markdown text")


class JobDocumentUpdate(BaseModel):
    """Payload for PATCH /jobs/{job_id}/documents — auto-save edited text."""

    cv_text: str | None = None
    cover_letter_text: str | None = None


class JobApplicationListOut(BaseModel):
    """Brief representation of a job application for list views."""

    job_id: UUID
    company_name: str
    job_title: str
    match_score: float | None
    workflow_status: str
    created_at: str
    processing: bool
    confirmed: bool = False
    cv_text: str | None = None
    cover_letter_text: str | None = None
