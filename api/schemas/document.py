"""Pydantic schemas for document APIs."""

from pydantic import BaseModel


class DocumentListItem(BaseModel):
    filename: str
    uploaded_at: float
    version: int
    size_bytes: int
    status: str


class DocumentVersionItem(BaseModel):
    version: int
    size_bytes: int
    status: str
    content_hash: str | None
    created_at: str | None
    is_current: bool


class IngestionJobStatus(BaseModel):
    id: int
    status: str
    error_message: str | None
    document_version_id: int
    created_at: str | None
    started_at: str | None
    finished_at: str | None
