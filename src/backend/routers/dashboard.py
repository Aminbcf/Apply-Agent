from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_db
from models.job_application import JobApplication

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)) -> dict[str, int]:
    """Get dynamic dashboard statistics from the database."""
    # Count active (non-archived) job applications
    result = await db.execute(
        select(func.count())
        .select_from(JobApplication)
        .where(JobApplication.status != "archived")
    )
    active_count = result.scalar() or 0

    return {
        "active_applications": active_count,
        "generated_documents": active_count,  # 1-to-1 mock for scaffold
        "interview_sessions": 0,
    }
