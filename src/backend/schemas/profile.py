from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProfileSchema(BaseModel):
    """Pydantic schema for the persistent user profile."""

    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None

    experience: list[Any] = Field(default_factory=list)
    education: list[Any] = Field(default_factory=list)
    projects: list[Any] = Field(default_factory=list)
    skills: dict[str, Any] = Field(default_factory=dict)
    certifications: list[Any] = Field(default_factory=list)
    languages: list[Any] = Field(default_factory=list)
    achievements: list[Any] = Field(default_factory=list)

    career_goals: str | None = None


class OnboardingStatusSchema(BaseModel):
    """Pydantic schema for Onboarding Status."""

    status: str  # "pending" or "completed"
    steps_completed: int
