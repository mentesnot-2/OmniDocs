"""Usage event model for per-user analytics."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from api.database import Base


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    event_type = Column(String(50), index=True, nullable=False)  # upload | query
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
