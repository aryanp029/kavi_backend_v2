from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Text, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from core.database import Base
import enum
from datetime import datetime, timezone
from typing import Optional
import uuid

class OAuthProviderEnum(enum.Enum):
    GOOGLE = "google"
    LINKEDIN = "linkedin"

class OAuthAccount(Base):
    __tablename__ = 'oauth_accounts'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    provider: Mapped[OAuthProviderEnum] = mapped_column(Enum(OAuthProviderEnum), nullable=False)
    provider_sub: Mapped[str] = mapped_column(String, nullable=False)
    provider_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provider_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    access_token_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refresh_token_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    scope: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)) 

    user: Mapped["User"] = relationship("User", back_populates="oauth_accounts")

    __table_args__ = (
        UniqueConstraint('provider', 'provider_sub', name='unique_provider_user'),
    )