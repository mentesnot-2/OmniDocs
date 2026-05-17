"""Persist processed Stripe webhook event IDs for idempotent delivery handling."""

from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func

from api.database import Base


class StripeProcessedEvent(Base):
    """One row per Stripe `evt_*` successfully handled; replays short-circuit on unique `id`."""

    __tablename__ = "stripe_processed_events"

    id = Column(String(255), primary_key=True)
    event_type = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
