from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from typing import Optional
import uuid
from core.database import Base

class OnboardingSummary(Base):
    __tablename__ = "onboarding_summary"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    current_work: Mapped[Optional[str]] = mapped_column(String(512))
    reason_for_interview: Mapped[Optional[str]] = mapped_column(String(512))
    where_in_interview_process: Mapped[Optional[str]] = mapped_column(String(512))
    target_company: Mapped[Optional[str]] = mapped_column(String(512))
    onboarding_done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    conversation_history: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=None)
    questions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=None)
    summary: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    user: Mapped["User"] = relationship("User", back_populates="onboarding_summary", uselist=False)