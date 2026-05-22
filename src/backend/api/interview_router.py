"""FastAPI router for the Interview Prep page.

Endpoints
---------
GET   /interviews              List all job applications with interview status
GET   /interviews/{job_id}     Get full details of an interview application
"""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.job_application import JobApplication
from schemas.job_schemas import JobApplicationListOut

router = APIRouter(prefix="/interviews", tags=["interviews"])
logger = logging.getLogger(__name__)

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=list[JobApplicationListOut])
async def list_interviews(db: DbDep):
    """Retrieve all job applications with workflow_status == 'interview'."""
    result = await db.execute(
        select(JobApplication)
        .where(JobApplication.workflow_status == "interview")
        .order_by(JobApplication.updated_at.desc())
    )
    jobs = result.scalars().all()
    return [
        JobApplicationListOut(
            job_id=job.id,
            company_name=job.company_name,
            job_title=job.job_title,
            match_score=job.match_score,
            workflow_status=job.workflow_status,
            created_at=job.created_at.isoformat(),
            processing=job.processing,
            confirmed=job.confirmed,
            cv_text=job.cv_text,
            cover_letter_text=job.cover_letter_text,
        )
        for job in jobs
    ]


@router.get("/{job_id}")
async def get_interview_detail(job_id: str, db: DbDep):
    """Get full details of an interview application including documents."""
    try:
        job_uuid = UUID(job_id)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=404, detail=f"Interview {job_id} not found")

    result = await db.execute(
        select(JobApplication).where(
            JobApplication.id == job_uuid,
            JobApplication.workflow_status == "interview",
        )
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail=f"Interview {job_id} not found")

    return {
        "job_id": str(job.id),
        "company_name": job.company_name,
        "job_title": job.job_title,
        "job_description": job.job_description,
        "match_score": job.match_score,
        "dimension_scores": job.dimension_scores,
        "workflow_status": job.workflow_status,
        "confirmed": job.confirmed,
        "cv_text": job.cv_text,
        "cover_letter_text": job.cover_letter_text,
        "cv_pdf_url": f"/jobs/{job_id}/download?file_type=cv" if job.cv_pdf_path else None,
        "cover_letter_pdf_url": f"/jobs/{job_id}/download?file_type=cover" if job.cover_letter_pdf_path else None,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
    }
