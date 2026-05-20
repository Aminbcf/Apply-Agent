from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class UserProfileVersion(Base):
    __tablename__ = "user_profile_versions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user_profile_id: Mapped[UUID] = mapped_column(index=True)
    snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
