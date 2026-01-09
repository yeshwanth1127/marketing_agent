"""Campaign model."""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Campaign(Base):
    """Campaign model representing marketing campaigns from various sources."""

    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(500), nullable=False)
    source = Column(String(50), nullable=False, index=True)  # 'meta_ads', 'ga4', etc.
    status = Column(String(50))  # 'active', 'paused', 'archived'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Campaign(id={self.id}, name='{self.name}', source='{self.source}')>"



