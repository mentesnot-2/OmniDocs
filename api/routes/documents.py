"""Documents routes (upload, query)"""

from api.utils.logging_config import logger
from api.utils.log_pii import redact_filename_for_log
from pathlib import Path
from typing import List
from pydantic import BaseModel
from config import (
    TOP_K,
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_MB,
)
from api.rate_limiter import limiter
from api.services.usage_limits import (
    enforce_upload_limit,
    enforce_storage_limit,
    enforce_query_limit,
    get_plan_limits,
    get_plan_storage_limit_bytes,
)
from api.services.storage_backend import get_storage_backend
from api.services.ingestion_file import FileTooLargeError, write_upload_to_temp_file
from api.services.file_validation import validate_uploaded_file_content



class QueryRequest(BaseModel):
    question:str
    top_k:int  | None = None
    message_history:List[dict] | None = None # List of messages in the conversation
    session_id:int | None = None # ID of the chat session to use

class MessagePair(BaseModel):
    question:str
    answer:str


from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Request
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import get_current_user , require_csrf
from api.models import User, UsageEvent
from ingestion import ingest_document
from chunking import chunk_document
from vectorstore import ChromaVectorStore
from api.services.runtime_services import (
    get_answer_generator,
    get_embedding_generator,
    get_retriever,
)
router = APIRouter(prefix="/documents",tags=["documents"])

def _track_usage_event(db: Session, user_id: int, event_type: str) -> None:
    """Best-effort usage tracking; never blocks core request flow."""
    try:
        db.add(UsageEvent(user_id=user_id, event_type=event_type))
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning(f"Failed to record usage event '{event_type}' for user {user_id}: {exc}")


@router.get("")
@router.get("/")
def get_documents(
    db:Session = Depends(get_db),
    current_user:User = Depends(get_current_user),
):
    """List all documents uploaded by by the current user."""
    # upload_dir = UPLOAD_DIR / str(current_user.id)
    # if not upload_dir.exists():
    #     return {"documents":[]}
    # files = []
    # for f in upload_dir.iterdir():
    #     if f.is_file():
    #         files.append({
    #             "filename":f.name,
    #             "uploaded_at":f.stat().st_mtime, # unix timestamp
    #         })

    #         # Sort by uploaded_at descending (newest first)
    # files.sort(key=lambda x : x["uploaded_at"], reverse=True)
    # return {"documents":files}
    storage = get_storage_backend()
    return {"documents":storage.list_files(current_user.id)}
@router.delete("/{filename}")
def delete_document(
    filename:str,
    _csrf: None = Depends(require_csrf),
    db:Session = Depends(get_db),
    current_user: User=Depends(get_current_user),

):
    """Delete a document and its chunks from the vector store."""
    import urllib.parse
    filename = urllib.parse.unquote(filename)

    safe_filename = Path(filename).name
    if safe_filename != filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid filename: {filename}",
        )
    # # Security: ensure path stays within user's folder
    # uploads_dir = (UPLOAD_DIR / str(current_user.id)).resolve()
    # file_path = (uploads_dir / filename).resolve()

    # if file_path.parent != uploads_dir:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Invalid filename.",

    #     )
    # if not file_path.exists():
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="File not found.",
    #     )
    storage = get_storage_backend()
    if not storage.file_exists(current_user.id, safe_filename):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {filename} not found.",
        )
    # Delete from vectore store
    store = ChromaVectorStore(user_id=str(current_user.id))
    store.delete_by_source(safe_filename)

    storage.delete_file(current_user.id, safe_filename)

    return {
        "message": "Document deleted successfully.",
        "filename": safe_filename,
    }
@router.post("/upload")
@limiter.limit("10/minute")
async def upload(
    request: Request,
    file: UploadFile = File(...),
    _csrf: None = Depends(require_csrf),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload document and index it for the current user."""
    original_filename = (file.filename or "").strip()
    if not original_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required.",
        )
    safe_filename = Path(original_filename).name
    if safe_filename != original_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename.",
        )
    file_log = redact_filename_for_log(safe_filename)

    ext = Path(safe_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        logger.error(f"File {file_log} has an invalid extension. Allowed extensions are {ALLOWED_EXTENSIONS}.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File {safe_filename} has an invalid extension. Allowed extensions are {ALLOWED_EXTENSIONS}.",
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
    indexing_completed = False
    temp_upload_path: Path | None = None

    try:
        try:
            temp_upload_path, total_bytes = await write_upload_to_temp_file(
                file,
                safe_filename,
                max_bytes=max_bytes,
            )
        except FileTooLargeError:
            logger.error(f"Document {file_log} is too large. Maximum size is {MAX_FILE_SIZE_MB} MB.")
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Document is too large. Maximum size is {MAX_FILE_SIZE_MB} MB.",
            )

        
        
        content = temp_upload_path.read_bytes()
        validate_uploaded_file_content(safe_filename, content)
        enforce_storage_limit(current_user, total_bytes)
        size_mb = total_bytes / (1024 * 1024)
        logger.info(f"Document {file_log} uploaded successfully. Size: {size_mb:.2f} MB.")

        with temp_upload_path.open("rb") as upload_stream:
            storage.save_fileobj(current_user.id, safe_filename, upload_stream)
        storage_saved = True

        local_path = storage.get_local_path(current_user.id, safe_filename)
        ingest_path = local_path if local_path is not None else temp_upload_path

        try:
            parsed = ingest_document(ingest_path)
            logger.info(f"Document {file_log} parsed successfully.")
        except Exception:
            logger.exception("Failed to parse document %s", file_log)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to parse document.",
            )

        if not parsed.content.strip():
            logger.error(f"Document {file_log} is empty or contains no text.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document is empty or contains no text.",
            )
        
        chunks = chunk_document(parsed)
        if not chunks:
            logger.error(f"No chunks produced from document {file_log}.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No chunks produced from document.",
            )
        texts = [c.text for c in chunks]
        gen = get_embedding_generator()
        embeddings = gen.embed_batch(texts)

        store = ChromaVectorStore(user_id=str(current_user.id))
        # Delete old chunks for re-upload (same filename)
        store.delete_by_source(safe_filename)
        metadatas = [
            {
                "source_file": c.source_file,
                "chunk_index": c.chunk_index,
                "user_id": str(current_user.id),
                **{k: str(v) for k,v in c.metadata.items()}
            }
            for c in chunks
        ]
        store.add_chunks(texts, embeddings, metadatas)
        _track_usage_event(db, current_user.id, "upload")
        indexing_completed = True
    finally:
        await file.close()
        if temp_upload_path is not None and temp_upload_path.exists():
            temp_upload_path.unlink(missing_ok=True)
        if storage_saved and not indexing_completed:
            try:
                storage.delete_file(current_user.id, safe_filename)
            except Exception as cleanup_exc:
                logger.warning(
                    f"Failed to clean up stored file {file_log} after upload failure: {cleanup_exc}"
                )

   

    return {
        "message": "Document uploaded and indexed successfully.",
        "file_name": safe_filename,
        "chunk_indexed": len(chunks),
    }


@router.post("/query")
@limiter.limit("30/minute")
def query(
    request: Request,
    body: QueryRequest,
    _csrf: None = Depends(require_csrf),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Answer a question based only on the current user's documents."""
    question = body.question.strip()
    if not question:
        logger.error("Question cannot be empty.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty.",
        )
    MAX_QUESTION_LEN = 2000
    if len(question) > MAX_QUESTION_LEN:
        logger.error(f"Question is too long. Maximum length is {MAX_QUESTION_LEN} characters.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Question is too long. Maximum length is {MAX_QUESTION_LEN} characters.",
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
            "answer":"I cannot answer because no relevant documents were found for this user.",
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
        "answer":response.answer,
        "sources":source_files,
        "refused":response.refused
    }


# Add quota endpoint
# add Get /documents/storage returning { used_bytes, limit_bytes, used_percent }
@router.get("/storage")
def get_storage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the storage usage for the current user."""
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