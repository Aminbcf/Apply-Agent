from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class JobApplication(Base):
    __tablename__ = "job_applications"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    status: Mapped[str] = mapped_column(String, default="draft")  # draft, submitted, interview, archived

    # Company/Job Info
    company_name: Mapped[str] = mapped_column(String)
    job_title: Mapped[str] = mapped_column(String)
    job_description: Mapped[str] = mapped_column(String)

    # Extracted Info
    match_score: Mapped[float] = mapped_column(Float, nullable=True)
    extracted_requirements: Mapped[dict] = mapped_column(JSON, default=dict)

    # Workflow: pending → interview → accepted → rejected | ghosted
    workflow_status: Mapped[str] = mapped_column(String, default="pending")

    # True after the user clicks "Confirm & Generate PDF"
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Generated markdown text (editable by user before PDF compilation)
    cv_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_letter_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # LaTeX source generated from the markdown text
    cv_latex: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_letter_latex: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Filesystem paths to compiled PDFs (relative to latex_output_dir)
    cv_pdf_path: Mapped[str | None] = mapped_column(String, nullable=True)
    cover_letter_pdf_path: Mapped[str | None] = mapped_column(String, nullable=True)

    # True while generation or pdflatex is running in the background
    processing: Mapped[bool] = mapped_column(Boolean, default=False)

    # Per-dimension match scores: { job_match, skill_match, education_match,
    #                               experience_match, objective_match }  (all 0–100)
    dimension_scores: Mapped[dict] = mapped_column(JSON, default=dict)


