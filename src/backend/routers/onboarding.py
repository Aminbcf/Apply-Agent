from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_db
from models.user_profile import UserProfile

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


class OnboardingStatusSchema(BaseModel):
    """Pydantic schema for Onboarding Status."""

    status: str  # "pending" or "completed"
    steps_completed: int


@router.get("/status", response_model=OnboardingStatusSchema)
async def get_onboarding_status(
    db: AsyncSession = Depends(get_db)
) -> OnboardingStatusSchema:
    """Dynamically compute onboarding status based on database UserProfile state."""
    result = await db.execute(select(UserProfile))
    profile = result.scalars().first()

    if not profile:
        return OnboardingStatusSchema(status="pending", steps_completed=0)

    steps = 0
    # Step 1: Basic Info (Name & Email)
    if profile.full_name and profile.email:
        steps += 1
    # Step 2: Experience or Skills
    if profile.experience or profile.skills:
        steps += 1
    # Step 3: Career Goals
    if profile.career_goals:
        steps += 1

    status = "completed" if steps >= 3 else "pending"
    return OnboardingStatusSchema(status=status, steps_completed=steps)
