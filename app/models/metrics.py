"""Metrics models for daily and weekly aggregated data."""

from sqlalchemy import Column, String, Integer, Date, DateTime, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class DailyMetric(Base):
    """Daily metrics for campaigns."""

    __tablename__ = "daily_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(Date, nullable=False, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    spend = Column(Numeric(12, 2), default=0)
    conversions = Column(Integer, default=0)
    revenue = Column(Numeric(12, 2), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    campaign = relationship("Campaign", backref="daily_metrics")

    # Unique constraint
    __table_args__ = (UniqueConstraint("date", "campaign_id", "source", name="uq_daily_metrics"),)

    def __repr__(self):
        return f"<DailyMetric(date={self.date}, campaign_id={self.campaign_id}, revenue={self.revenue})>"


class WeeklyMetric(Base):
    """Weekly aggregated metrics for campaigns."""

    __tablename__ = "weekly_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    week_start = Column(Date, nullable=False, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)
    impressions = Column(Integer)
    clicks = Column(Integer)
    spend = Column(Numeric(12, 2))
    conversions = Column(Integer)
    revenue = Column(Numeric(12, 2))
    roas = Column(Numeric(10, 4))  # revenue / spend
    ctr = Column(Numeric(10, 4))  # clicks / impressions
    cpc = Column(Numeric(10, 4))  # spend / clicks
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    campaign = relationship("Campaign", backref="weekly_metrics")

    # Unique constraint
    __table_args__ = (UniqueConstraint("week_start", "campaign_id", "source", name="uq_weekly_metrics"),)

    def __repr__(self):
        return f"<WeeklyMetric(week_start={self.week_start}, campaign_id={self.campaign_id}, roas={self.roas})>"

