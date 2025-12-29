"""Background document ingestion job processing."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from api.database import SessionLocal
from api.models import DocumentVersion, IngestionJob, UsageEvent
from api.services.document_registry import mark_version_failed, mark_version_ready
from api.services.runtime_services import get_embedding_generator
from api.services.storage_backend import get_storage_backend
from api.utils.logging_config import logger
from chunking import chunk_document
from ingestion import ingest_document
from vectorstore import ChromaVectorStore


def create_ingestion_job(db: Session, *, user_id: int, document_version_id: int) -> IngestionJob:
    job = IngestionJob(
        user_id=user_id,
        document_version_id=document_version_id,
        status="queued",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job_for_user(db: Session, job_id: int, user_id: int) -> IngestionJob | None:
    return (
        db.query(IngestionJob)
        .filter(IngestionJob.id == job_id, IngestionJob.user_id == user_id)
        .first()
    )


def enqueue_ingestion_job(job_id: int) -> None:
    """Dispatch ingestion to Celery, or run inline when configured for tests."""
    if os.getenv("INGESTION_RUN_INLINE", "").lower() in ("1", "true", "yes"):
        process_ingestion_job(job_id)
        return
    from api.tasks.ingestion import process_ingestion_job_task

    process_ingestion_job_task.delay(job_id)


def process_ingestion_job(job_id: int) -> None:
    """Parse, chunk, embed, and index a stored document version."""
    db = SessionLocal()
    try:
        job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
        if job is None:
            return

        job.status = "processing"
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        version = (
            db.query(DocumentVersion)
            .filter(DocumentVersion.id == job.document_version_id)
            .first()
        )
        if version is None:
            job.status = "failed"
            job.error_message = "Document version not found"
            job.finished_at = datetime.now(timezone.utc)
            db.commit()
            return

        document = version.document
        user_id = job.user_id
        filename = document.filename
        storage = get_storage_backend()

        try:
            file_bytes = storage.get_bytes_by_key(version.storage_key)
            local_path = storage.get_local_path_by_key(version.storage_key)
            ingest_path = local_path if local_path is not None else _write_temp_bytes(file_bytes, filename)

            parsed = ingest_document(ingest_path)
            if not parsed.content.strip():
                raise ValueError("Document is empty or contains no text")

            chunks = chunk_document(parsed)
            if not chunks:
                raise ValueError("No chunks produced from document")

            texts = [c.text for c in chunks]
            gen = get_embedding_generator()
            embeddings = gen.embed_batch(texts)

            store = ChromaVectorStore(user_id=str(user_id))
            store.delete_by_source(filename)
            metadatas = [
                {
                    "source_file": c.source_file,
                    "chunk_index": c.chunk_index,
                    "user_id": str(user_id),
                    "document_id": str(document.id),
                    "version_number": str(version.version_number),
                    **{k: str(v) for k, v in c.metadata.items()},
                }
                for c in chunks
            ]
            store.add_chunks(texts, embeddings, metadatas)

            db.add(UsageEvent(user_id=user_id, event_type="upload"))
            mark_version_ready(db, version.id)
            job.status = "completed"
            job.error_message = None
            job.finished_at = datetime.now(timezone.utc)
            db.commit()
        except Exception as exc:
            logger.exception("Ingestion job %s failed", job_id)
            mark_version_failed(db, version.id, str(exc))
            job.status = "failed"
            job.error_message = str(exc)[:2000]
            job.finished_at = datetime.now(timezone.utc)
            db.commit()
            try:
                storage.delete_by_key(version.storage_key)
            except Exception:
                logger.warning("Failed to clean up storage after ingestion failure")
    finally:
        db.close()


def _write_temp_bytes(content: bytes, filename: str) -> Path:
    import tempfile

    suffix = Path(filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        return Path(tmp.name)
