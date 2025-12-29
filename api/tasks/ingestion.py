"""Celery tasks for document ingestion."""

from api.celery_app import celery_app
from api.services.ingestion_jobs import process_ingestion_job


@celery_app.task(name="ingestion.process_job", bind=True, max_retries=2)
def process_ingestion_job_task(self, job_id: int) -> None:
    try:
        process_ingestion_job(job_id)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)
