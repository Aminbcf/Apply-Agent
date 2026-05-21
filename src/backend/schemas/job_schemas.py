"""Pydantic schemas for the job‑match scenario (Phase 7)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


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
    workflow_status: Literal["pending", "accepted", "rejected"] = "pending"
    processing: bool = Field(
        default=True,
        description="True while pdflatex compilation is running in the background",
    )
    cv_pdf_url: str | None = None
    cover_letter_pdf_url: str | None = None


class JobStatusOut(BaseModel):
    """Polling response for PDF generation progress."""

    job_id: UUID
    processing: bool
    cv_pdf_url: str | None = None
    cover_letter_pdf_url: str | None = None
    workflow_status: Literal["pending", "accepted", "rejected"]


class WorkflowStatusUpdate(BaseModel):
    """Payload for PATCH /jobs/{job_id}/status."""

    status: Literal["pending", "accepted", "rejected"]


class LatexUpdate(BaseModel):
    """Payload for PATCH /jobs/{job_id}/latex."""

    doc_type: Literal["cv", "cover"]
    latex_source: str = Field(..., min_length=1)
