from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas.profile import ProfileSchema
from services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])

profile_service = ProfileService()


@router.get("/")
async def get_profile(db: Annotated[AsyncSession, Depends(get_db)]) -> ProfileSchema:
    """Retrieve the persistent user profile from the database."""
    profile = await profile_service.get_profile(db)
    return profile_service.to_schema(profile)


@router.post("/")
async def save_profile(
    profile_data: ProfileSchema,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ProfileSchema:
    """Save or update the persistent user profile in the database."""
    return await profile_service.upsert_profile(db, profile_data)

