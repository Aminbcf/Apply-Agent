from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class JobApplication(Base):
    __tablename__ = "job_applications"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    status: Mapped[str] = mapped_column(String, default="draft") # draft, submitted, interview, archived
    
    # Company/Job Info
    company_name: Mapped[str] = mapped_column(String)
    job_title: Mapped[str] = mapped_column(String)
    job_description: Mapped[str] = mapped_column(String)
    
    # Extracted Info
    match_score: Mapped[float] = mapped_column(Float, nullable=True)
    extracted_requirements: Mapped[dict] = mapped_column(JSON, default=dict)
