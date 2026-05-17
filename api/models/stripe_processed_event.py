from sqlalchemy import Column, DateTime,String
from sqlalchemy.sql import func

from api.database import Base


class StripeProcessEvent(Base):
    __tablename__ = "stripe_processed_events"

    # Stripe evt_xxx; unique => at most one row per delivery

    id = Column(String(255),primary_key=True)

    event_type = Column(String(255),nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(),nullable=False)