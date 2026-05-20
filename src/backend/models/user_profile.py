from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Basic Info
    full_name: Mapped[str] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String, nullable=True)
    phone: Mapped[str] = mapped_column(String, nullable=True)
    location: Mapped[str] = mapped_column(String, nullable=True)
    
    # Structured Profile Data (JSON columns for flexibility in the scaffold)
    experience: Mapped[dict] = mapped_column(JSON, default=list)
    education: Mapped[dict] = mapped_column(JSON, default=list)
    projects: Mapped[dict] = mapped_column(JSON, default=list)
    skills: Mapped[dict] = mapped_column(JSON, default=dict)
    certifications: Mapped[dict] = mapped_column(JSON, default=list)
    languages: Mapped[dict] = mapped_column(JSON, default=list)
    achievements: Mapped[dict] = mapped_column(JSON, default=list)
    career_goals: Mapped[str] = mapped_column(String, nullable=True)
