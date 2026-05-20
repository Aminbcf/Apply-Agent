from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas.profile import OnboardingStatusSchema, ProfileSchema
from services.profile_service import ProfileService

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

profile_service = ProfileService()


@router.get("/status")
async def get_onboarding_status(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> OnboardingStatusSchema:
    """Dynamically compute onboarding status based on database UserProfile state."""
    profile = await profile_service.get_profile(db)
    if not profile:
        return OnboardingStatusSchema(status="pending", steps_completed=0)

    steps = 0
    if profile.full_name and profile.email:
        steps += 1
    if (profile.experience and len(profile.experience) > 0) or (profile.skills and len(profile.skills) > 0):
        steps += 1
    if profile.career_goals:
        steps += 1

    return OnboardingStatusSchema(status="completed" if steps >= 3 else "pending", steps_completed=steps)


@router.post("/cv", response_model=ProfileSchema)
async def upload_cv(
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
) -> ProfileSchema:
    """Upload a CV (PDF/DOCX/TXT), parse it, and merge results into the profile."""
    try:
        return await profile_service.apply_cv_upload(db, file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

