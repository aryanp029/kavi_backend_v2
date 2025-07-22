from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey, Text 
from sqlalchemy.dialects.postgresql import UUID
from core.database import Base 
from datetime import datetime, timezone
from typing import Optional 
import uuid

class Resume(Base):
    __tablename__ = 'resume'  
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, unique=True)
    resume_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    
    user: Mapped["User"] = relationship("User", back_populates="resume_upload", uselist=False)