"""Document model - file storage with AI-extracted metadata."""
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional
import uuid

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Integer, Float

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin, JSONB, UUID

if TYPE_CHECKING:
    from .account import Account
    from .entity import Entity


class DocumentStatus(str, Enum):
    """Status of document processing."""
    UPLOADED = "uploaded"       # Just uploaded, not processed
    PROCESSING = "processing"   # OCR/AI extraction in progress
    PROCESSED = "processed"     # Successfully extracted data
    FAILED = "failed"          # Extraction failed
    NEEDS_REVIEW = "needs_review"  # Low confidence, needs human review


class DocumentType(Base, UUIDMixin, TimestampMixin):
    """
    Document type lookup table - populated from YAML config.

    Examples: Certificate of Insurance, Vehicle Registration, Lease Agreement, etc.
    """

    __tablename__ = "document_types"

    # Type identifier (from YAML)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # MIME types accepted for this document type
    accepted_mime_types: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: ["application/pdf", "image/png", "image/jpeg"],
    )

    # AI extraction configuration (from YAML)
    extraction_prompt: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="LLM prompt template for extracting data from this document type"
    )

    # Expected fields to extract
    extraction_schema: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="JSON Schema defining expected extracted fields"
    )

    # Validation rules for extracted data
    validation_rules: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # Which niche this type belongs to
    niche_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="document_type",
    )

    def __repr__(self) -> str:
        return f"<DocumentType(code='{self.code}', name='{self.name}')>"


class Document(Base, UUIDMixin, TimestampMixin):
    """
    Document model - stores uploaded files and AI-extracted data.

    Documents are linked to entities and can satisfy requirements.
    The extracted_data field contains structured JSON from the AI extraction pipeline.
    """

    __tablename__ = "documents"

    # Account relationship (multi-tenant)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Entity this document belongs to
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Type relationship
    document_type_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_types.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # File information
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)

    # Storage location (S3/GCS path)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_bucket: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Processing status
    status: Mapped[str] = mapped_column(
        String(20),
        default=DocumentStatus.UPLOADED.value,
        nullable=False,
        index=True,
    )

    # OCR/extraction results
    raw_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Raw text extracted via OCR"
    )
    extracted_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Structured data extracted by LLM"
    )

    # Extraction confidence scores
    extraction_confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Overall confidence score 0-1"
    )
    field_confidences: Mapped[dict[str, float]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Per-field confidence scores"
    )

    # Processing metadata
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # User who uploaded
    uploaded_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Metadata and tags
    document_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",  # Keep column name for DB compatibility
        JSONB,
        nullable=False,
        default=dict,
    )
    tags: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="documents")
    entity: Mapped[Optional["Entity"]] = relationship("Entity", back_populates="documents")
    document_type: Mapped[Optional["DocumentType"]] = relationship(
        "DocumentType",
        back_populates="documents",
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.status}')>"
