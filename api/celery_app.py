"""Celery application for durable background work."""

import os
from pathlib import Path

from celery import Celery
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

_broker = os.getenv("CELERY_BROKER_URL", os.getenv("RATE_LIMIT_STORAGE_URI", "redis://localhost:6379/0"))
_result_backend = os.getenv("CELERY_RESULT_BACKEND", _broker)

celery_app = Celery(
    "omnidocs",
    broker=_broker,
    backend=_result_backend,
    include=["api.tasks.ingestion"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
