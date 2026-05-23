from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from schemas.profile import (
    OnboardingStatusSchema,
    ProfileSchema,
    OnboardingDebugSchema,
)
from services.profile_service import ProfileService

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

profile_service = ProfileService()


@router.get("/status")
async def get_onboarding_status(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> OnboardingStatusSchema:
    """Dynamically compute onboarding status from UserProfile state."""
    profile = await profile_service.get_profile(db)
    if not profile:
        return OnboardingStatusSchema(status="pending", steps_completed=0)

    steps = 0
    if profile.full_name and profile.email:
        steps += 1
    has_exp = profile.experience and len(profile.experience) > 0
    has_skills = profile.skills and len(profile.skills) > 0
    if has_exp or has_skills:
        steps += 1
    if profile.career_goals:
        steps += 1

    status_val = "completed" if steps >= 3 else "pending"
    return OnboardingStatusSchema(status=status_val, steps_completed=steps)


@router.post("/upload", response_model=ProfileSchema)
async def upload_cv(
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
) -> ProfileSchema:
    """Upload a CV, parse it, and merge results into the profile."""
    try:
        return await profile_service.apply_cv_upload(db, file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/debug", response_model=OnboardingDebugSchema)
async def get_onboarding_debug(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> OnboardingDebugSchema:
    """Retrieve raw CV details and compose context for LLM prompt."""
    if not settings.debug_mode:
        raise HTTPException(status_code=404, detail="Not Found")

    profile = await profile_service.get_profile(db)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="No profile found. Please complete onboarding first.",
        )

    # Construct the LLM context structure mimicking cover_letter_generator.py
    skills_list = []
    if profile.skills and isinstance(profile.skills, dict):
        skills_list = profile.skills.get("general", [])
    elif isinstance(profile.skills, list):
        skills_list = profile.skills

    evidence = []
    if profile.experience and isinstance(profile.experience, list):
        for i, exp in enumerate(profile.experience):
            if isinstance(exp, dict):
                summary = (
                    exp.get("description")
                    or exp.get("role")
                    or exp.get("summary")
                    or ""
                )
                source = (
                    exp.get("company")
                    or exp.get("organization")
                    or f"Experience {i + 1}"
                )
                evidence.append({
                    "id": f"exp_{i + 1}",
                    "summary": summary,
                    "metric": "",
                    "source_id": source,
                })

    llm_context = {
        "candidate": {
            "name": profile.full_name,
            "city": profile.location,
            "phone": profile.phone,
            "email": profile.email,
        },
        "skills": {
            "req_skills": skills_list,
            "pref_skills": [],
        },
        "evidence": evidence,
        "job": {
            "title": profile.career_goals or "Target Role",
            "company": "Target Company",
            "location": "Remote",
        },
        "constraints": {"max_paragraphs": 3},
    }

    return OnboardingDebugSchema(
        raw_cv_text=profile.raw_cv_text,
        parsed_cv_json=profile.parsed_cv_json,
        llm_context=llm_context,
    )
