"""Document metadata registry backed by SQLAlchemy."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from api.models import Document, DocumentVersion


def _version_storage_key(user_id: int, filename: str, version_number: int) -> str:
    return f"{user_id}/versions/{filename}/v{version_number}"


def register_pending_version(
    db: Session,
    *,
    user_id: int,
    filename: str,
    size_bytes: int,
    content: bytes,
) -> tuple[Document, DocumentVersion]:
    """Create or bump document version row before indexing completes."""
    content_hash = hashlib.sha256(content).hexdigest()
    document = (
        db.query(Document)
        .filter(Document.user_id == user_id, Document.filename == filename)
        .first()
    )
    if document is None:
        document = Document(user_id=user_id, filename=filename)
        db.add(document)
        db.flush()

    next_version = (
        db.query(DocumentVersion)
        .filter(DocumentVersion.document_id == document.id)
        .count()
        + 1
    )
    storage_key = _version_storage_key(user_id, filename, next_version)
    version = DocumentVersion(
        document_id=document.id,
        version_number=next_version,
        storage_key=storage_key,
        size_bytes=size_bytes,
        content_hash=content_hash,
        status="processing",
    )
    db.add(version)
    db.flush()

    document.current_version_id = version.id
    document.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(document)
    db.refresh(version)
    return document, version


def mark_version_ready(db: Session, version_id: int) -> None:
    version = db.query(DocumentVersion).filter(DocumentVersion.id == version_id).one()
    version.status = "ready"
    db.commit()


def mark_version_failed(db: Session, version_id: int, error_message: str) -> None:
    version = db.query(DocumentVersion).filter(DocumentVersion.id == version_id).one()
    version.status = "failed"
    db.commit()
    _ = error_message


def list_documents(db: Session, user_id: int) -> list[dict[str, Any]]:
    documents = (
        db.query(Document)
        .filter(Document.user_id == user_id)
        .order_by(Document.updated_at.desc())
        .all()
    )
    results: list[dict[str, Any]] = []
    for doc in documents:
        version = None
        if doc.current_version_id:
            version = (
                db.query(DocumentVersion)
                .filter(DocumentVersion.id == doc.current_version_id)
                .first()
            )
        uploaded_at = (
            version.created_at.timestamp()
            if version and version.created_at
            else doc.created_at.timestamp()
        )
        results.append(
            {
                "filename": doc.filename,
                "uploaded_at": uploaded_at,
                "version": version.version_number if version else 0,
                "size_bytes": version.size_bytes if version else 0,
                "status": version.status if version else "unknown",
            }
        )
    return results


def get_versions(db: Session, user_id: int, filename: str) -> list[dict[str, Any]]:
    document = (
        db.query(Document)
        .filter(Document.user_id == user_id, Document.filename == filename)
        .first()
    )
    if document is None:
        return []
    versions = (
        db.query(DocumentVersion)
        .filter(DocumentVersion.document_id == document.id)
        .order_by(DocumentVersion.version_number.desc())
        .all()
    )
    return [
        {
            "version": v.version_number,
            "size_bytes": v.size_bytes,
            "status": v.status,
            "content_hash": v.content_hash,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "is_current": v.id == document.current_version_id,
        }
        for v in versions
    ]


def delete_document_record(db: Session, user_id: int, filename: str) -> bool:
    document = (
        db.query(Document)
        .filter(Document.user_id == user_id, Document.filename == filename)
        .first()
    )
    if document is None:
        return False
    db.query(DocumentVersion).filter(DocumentVersion.document_id == document.id).delete()
    db.delete(document)
    db.commit()
    return True
