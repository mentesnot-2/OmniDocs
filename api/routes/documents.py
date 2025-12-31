"""Documents routes (upload, query)"""

import urllib.parse
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, require_csrf
from api.database import get_db
from api.models import User, UsageEvent
from api.rate_limiter import limiter
from api.schemas.document import IngestionJobStatus
from api.services.document_registry import (
    delete_document_record,
    get_versions,
    list_documents,
    register_pending_version,
)
from api.services.file_validation import validate_uploaded_file_content
from api.services.ingestion_file import FileTooLargeError, write_upload_to_temp_file
from api.services.ingestion_jobs import create_ingestion_job, get_job_for_user, process_ingestion_job
from api.services.runtime_services import get_answer_generator, get_retriever
from api.services.storage_backend import get_storage_backend
from api.services.usage_limits import (
    enforce_query_limit,
    enforce_storage_limit,
    enforce_upload_limit,
    get_plan_limits,
    get_plan_storage_limit_bytes,
)
from api.utils.log_pii import redact_filename_for_log
from api.utils.logging_config import logger
from chunking import chunk_document
from config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB, TOP_K
from ingestion import ingest_document
from vectorstore import ChromaVectorStore

router = APIRouter(prefix="/documents", tags=["documents"])


class QueryRequest(BaseModel):
    question: str
    top_k: int | None = None
    message_history: list[dict] | None = None
    session_id: int | None = None


def _track_usage_event(db: Session, user_id: int, event_type: str) -> None:
    try:
        db.add(UsageEvent(user_id=user_id, event_type=event_type))
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning(f"Failed to record usage event '{event_type}' for user {user_id}: {exc}")


def _safe_filename(filename: str) -> str:
    decoded = urllib.parse.unquote(filename)
    safe = Path(decoded).name
    if safe != decoded:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid filename: {filename}",
        )
    return safe


@router.get("")
@router.get("/")
def get_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List documents with version metadata for the current user."""
    items = list_documents(db, current_user.id)
    if items:
        return {"documents": items}
    storage = get_storage_backend()
    legacy = storage.list_files(current_user.id)
    return {
        "documents": [
            {
                "filename": f["filename"],
                "uploaded_at": f["uploaded_at"],
                "version": 1,
                "size_bytes": 0,
                "status": "ready",
            }
            for f in legacy
        ]
    }


@router.get("/storage")
def get_storage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    storage = get_storage_backend()
    used_bytes = storage.get_usage_bytes(current_user.id)
    plan = get_plan_limits(current_user)
    limit_bytes = get_plan_storage_limit_bytes(current_user)
    return {
        "used_bytes": used_bytes,
        "limit_bytes": limit_bytes,
        "used_percent": round((used_bytes / limit_bytes * 100.0) if limit_bytes else 0.0, 2),
        "plan_id": plan.plan_id,
        "plan_name": plan.name,
    }


@router.get("/{filename}/versions")
def list_document_versions(
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    safe_filename = _safe_filename(filename)
    versions = get_versions(db, current_user.id, safe_filename)
    if not versions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return {"filename": safe_filename, "versions": versions}


@router.get("/jobs/{job_id}")
def get_ingestion_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = get_job_for_user(db, job_id, current_user.id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return IngestionJobStatus(
        id=job.id,
        status=job.status,
        error_message=job.error_message,
        document_version_id=job.document_version_id,
        created_at=job.created_at.isoformat() if job.created_at else None,
        started_at=job.started_at.isoformat() if job.started_at else None,
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
    )


@router.delete("/{filename}")
def delete_document(
    filename: str,
    _csrf: None = Depends(require_csrf),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    safe_filename = _safe_filename(filename)
    storage = get_storage_backend()
    if not storage.file_exists(current_user.id, safe_filename):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {safe_filename} not found.",
        )
    store = ChromaVectorStore(user_id=str(current_user.id))
    store.delete_by_source(safe_filename)
    storage.delete_file(current_user.id, safe_filename)
    delete_document_record(db, current_user.id, safe_filename)
    return {"message": "Document deleted successfully.", "filename": safe_filename}


@router.post("/upload")
@limiter.limit("10/minute")
async def upload(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    _csrf: None = Depends(require_csrf),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload document and queue background indexing."""
    original_filename = (file.filename or "").strip()
    if not original_filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required.")

    safe_filename = Path(original_filename).name
    if safe_filename != original_filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename.")

    file_log = redact_filename_for_log(safe_filename)
    ext = Path(safe_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File {safe_filename} has an invalid extension.",
        )

    enforce_upload_limit(db, current_user)
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > max_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Document is too large. Maximum size is {MAX_FILE_SIZE_MB} MB.",
                )
        except ValueError:
            logger.warning(f"Invalid content-length header for upload: {content_length}")

    storage = get_storage_backend()
    storage_saved = False
    temp_upload_path: Path | None = None

    try:
        try:
            temp_upload_path, total_bytes = await write_upload_to_temp_file(
                file,
                safe_filename,
                max_bytes=max_bytes,
            )
        except FileTooLargeError:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Document is too large. Maximum size is {MAX_FILE_SIZE_MB} MB.",
            )

        content = temp_upload_path.read_bytes()
        validate_uploaded_file_content(safe_filename, content)
        enforce_storage_limit(current_user, total_bytes)
        logger.info(f"Document {file_log} uploaded. Size: {total_bytes / (1024 * 1024):.2f} MB.")

        with temp_upload_path.open("rb") as upload_stream:
            storage.save_fileobj(current_user.id, safe_filename, upload_stream)
        storage_saved = True

        _, version = register_pending_version(
            db,
            user_id=current_user.id,
            filename=safe_filename,
            size_bytes=total_bytes,
            content=content,
        )
        job = create_ingestion_job(
            db,
            user_id=current_user.id,
            document_version_id=version.id,
        )
        background_tasks.add_task(process_ingestion_job, job.id)

        return {
            "message": "Document uploaded; indexing started.",
            "file_name": safe_filename,
            "version": version.version_number,
            "job_id": job.id,
            "status": job.status,
        }
    except HTTPException:
        if storage_saved:
            try:
                storage.delete_file(current_user.id, safe_filename)
            except Exception as cleanup_exc:
                logger.warning(f"Cleanup failed for {file_log}: {cleanup_exc}")
        raise
    finally:
        await file.close()
        if temp_upload_path is not None and temp_upload_path.exists():
            temp_upload_path.unlink(missing_ok=True)


@router.post("/query")
@limiter.limit("30/minute")
def query(
    request: Request,
    body: QueryRequest,
    _csrf: None = Depends(require_csrf),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question cannot be empty.")
    max_question_len = 2000
    if len(question) > max_question_len:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Question is too long. Maximum length is {max_question_len} characters.",
        )

    enforce_query_limit(db, current_user)
    retriever = get_retriever()
    result = retriever.retrieve_with_context(
        question,
        top_k=body.top_k or TOP_K,
        user_id=str(current_user.id),
    )
    _track_usage_event(db, current_user.id, "query")

    if result["num_results"] == 0:
        return {
            "answer": "I cannot answer because no relevant documents were found for this user.",
            "sources": [],
        }

    gen = get_answer_generator()
    source_files = list({r.source_file for r in result["chunks"]})
    response = gen.generate(
        query=result["query"],
        context_text=result["context_text"],
        source_files=source_files,
        message_history=body.message_history,
    )
    return {
        "answer": response.answer,
        "sources": source_files,
        "refused": response.refused,
    }
