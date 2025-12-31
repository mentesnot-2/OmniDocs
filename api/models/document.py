"""Document metadata and version history."""

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from api.database import Base


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("user_id", "filename", name="uq_documents_user_filename"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(512), nullable=False)
    current_version_id = Column(
        Integer,
        ForeignKey("document_versions.id", use_alter=True),
        nullable=True,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    versions = relationship(
        "DocumentVersion",
        back_populates="document",
        foreign_keys="DocumentVersion.document_id",
        cascade="all, delete-orphan",
    )


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    storage_key = Column(String(1024), nullable=False)
    size_bytes = Column(Integer, nullable=False, server_default="0")
    content_hash = Column(String(64), nullable=True)
    status = Column(String(32), nullable=False, server_default="processing")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    document = relationship(
        "Document",
        back_populates="versions",
        foreign_keys=[document_id],
    )
    ingestion_jobs = relationship("IngestionJob", back_populates="document_version")
