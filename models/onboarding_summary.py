from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from typing import Optional
from core.database import Base
import uuid
class OnboardingSummary(Base):
    __tablename__ = "onboarding_summary"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    current_work: Mapped[Optional[str]] = mapped_column(String(512))
    reason_for_interview: Mapped[Optional[str]] = mapped_column(String(512))
    where_in_interview_process: Mapped[Optional[str]] = mapped_column(String(512))
    target_company: Mapped[Optional[str]] = mapped_column(String(512))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    user: Mapped["User"] = relationship("User", back_populates="onboarding_summary",uselist=False)

