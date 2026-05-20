from typing import Annotated, Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_db
from models.user_profile import UserProfile

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileSchema(BaseModel):
    """Pydantic schema for User Profile."""

    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    experience: Optional[List[Any]] = []
    education: Optional[List[Any]] = []
    projects: Optional[List[Any]] = []
    skills: Optional[Dict[str, Any]] = {}
    certifications: Optional[List[Any]] = []
    languages: Optional[List[Any]] = []
    achievements: Optional[List[Any]] = []
    career_goals: Optional[str] = None


@router.get("/")
async def get_profile(db: Annotated[AsyncSession, Depends(get_db)]) -> ProfileSchema:
    """Retrieve the persistent user profile from the database."""
    result = await db.execute(select(UserProfile))
    profile = result.scalars().first()
    if not profile:
        # Return a blank default profile so the frontend form loads correctly
        return ProfileSchema()
    return ProfileSchema(
        full_name=profile.full_name,
        email=profile.email,
        phone=profile.phone,
        location=profile.location,
        experience=profile.experience or [],
        education=profile.education or [],
        projects=profile.projects or [],
        skills=profile.skills or {},
        certifications=profile.certifications or [],
        languages=profile.languages or [],
        achievements=profile.achievements or [],
        career_goals=profile.career_goals,
    )


@router.post("/")
async def save_profile(
    profile_data: ProfileSchema,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ProfileSchema:
    """Save or update the persistent user profile in the database."""
    result = await db.execute(select(UserProfile))
    profile = result.scalars().first()

    if not profile:
        profile = UserProfile(
            full_name=profile_data.full_name,
            email=profile_data.email,
            phone=profile_data.phone,
            location=profile_data.location,
            experience=profile_data.experience,
            education=profile_data.education,
            projects=profile_data.projects,
            skills=profile_data.skills,
            certifications=profile_data.certifications,
            languages=profile_data.languages,
            achievements=profile_data.achievements,
            career_goals=profile_data.career_goals,
        )
        db.add(profile)
    else:
        profile.full_name = profile_data.full_name
        profile.email = profile_data.email
        profile.phone = profile_data.phone
        profile.location = profile_data.location
        profile.experience = profile_data.experience
        profile.education = profile_data.education
        profile.projects = profile_data.projects
        profile.skills = profile_data.skills
        profile.certifications = profile_data.certifications
        profile.languages = profile_data.languages
        profile.achievements = profile_data.achievements
        profile.career_goals = profile_data.career_goals

    await db.commit()
    await db.refresh(profile)

    return ProfileSchema(
        full_name=profile.full_name,
        email=profile.email,
        phone=profile.phone,
        location=profile.location,
        experience=profile.experience or [],
        education=profile.education or [],
        projects=profile.projects or [],
        skills=profile.skills or {},
        certifications=profile.certifications or [],
        languages=profile.languages or [],
        achievements=profile.achievements or [],
        career_goals=profile.career_goals,
    )
