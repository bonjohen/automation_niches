"""Document management endpoints."""
from datetime import datetime
from typing import Any, Optional
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.settings import get_settings
from app.models.document import Document, DocumentType, DocumentStatus
from app.models.user import User
from app.api.endpoints.auth import get_current_active_user

router = APIRouter()
settings = get_settings()


# Pydantic schemas
class DocumentTypeResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    description: Optional[str]
    accepted_mime_types: list[str]
    extraction_schema: dict[str, Any]

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    entity_id: Optional[uuid.UUID]
    document_type_id: Optional[uuid.UUID]
    filename: str
    original_filename: str
    mime_type: str
    file_size: int
    status: str
    extracted_data: dict[str, Any]
    extraction_confidence: Optional[float]
    processing_error: Optional[str]
    processed_at: Optional[datetime]
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int


class DocumentUpdate(BaseModel):
    entity_id: Optional[uuid.UUID] = None
    document_type_id: Optional[uuid.UUID] = None
    extracted_data: Optional[dict[str, Any]] = None
    tags: Optional[list[str]] = None


# Endpoints
@router.get("/types", response_model=list[DocumentTypeResponse])
async def list_document_types(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all available document types."""
    types = db.query(DocumentType).all()
    return types


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    entity_id: Optional[uuid.UUID] = None,
    document_type_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List documents with filtering and pagination."""
    query = db.query(Document).filter(Document.account_id == current_user.account_id)

    # Apply filters
    if entity_id:
        query = query.filter(Document.entity_id == entity_id)
    if document_type_id:
        query = query.filter(Document.document_type_id == document_type_id)
    if status:
        query = query.filter(Document.status == status)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Document.filename.ilike(search_filter),
                Document.original_filename.ilike(search_filter),
            )
        )

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    documents = query.order_by(Document.created_at.desc()).offset(offset).limit(page_size).all()

    return DocumentListResponse(
        items=documents,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    entity_id: Optional[uuid.UUID] = Form(None),
    document_type_id: Optional[uuid.UUID] = Form(None),
    tags: Optional[str] = Form(None),  # JSON string
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Upload a new document."""
    import json
    import os

    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"

    # For now, store locally (will be replaced with S3/GCS)
    storage_path = f"documents/{current_user.account_id}/{unique_filename}"

    # Create storage directory if needed
    os.makedirs(os.path.dirname(os.path.join(settings.local_storage_path, storage_path)), exist_ok=True)

    # Save file locally
    file_path = os.path.join(settings.local_storage_path, storage_path)
    with open(file_path, "wb") as f:
        f.write(content)

    # Parse tags if provided
    parsed_tags = []
    if tags:
        try:
            parsed_tags = json.loads(tags)
        except json.JSONDecodeError:
            parsed_tags = [t.strip() for t in tags.split(",") if t.strip()]

    # Create document record
    document = Document(
        account_id=current_user.account_id,
        entity_id=entity_id,
        document_type_id=document_type_id,
        filename=unique_filename,
        original_filename=file.filename,
        mime_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        storage_path=storage_path,
        status=DocumentStatus.UPLOADED.value,
        uploaded_by_id=current_user.id,
        tags=parsed_tags,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # TODO: Trigger async processing (OCR + AI extraction)

    return document


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a specific document by ID."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.account_id == current_user.account_id,
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: uuid.UUID,
    doc_data: DocumentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update document metadata or extracted data."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.account_id == current_user.account_id,
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Update fields
    update_data = doc_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(document, field, value)

    db.commit()
    db.refresh(document)

    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a document."""
    import os

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.account_id == current_user.account_id,
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Delete file from storage
    file_path = os.path.join(settings.local_storage_path, document.storage_path)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(document)
    db.commit()


class ProcessingResultResponse(BaseModel):
    success: bool
    document_id: uuid.UUID
    extracted_data: dict[str, Any]
    confidence: float
    needs_review: bool
    errors: list[str]
    linked_requirement_id: Optional[uuid.UUID]


@router.post("/{document_id}/process", response_model=ProcessingResultResponse)
async def process_document_endpoint(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Trigger document processing (OCR + AI extraction)."""
    from app.ai.document_processor import process_document

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.account_id == current_user.account_id,
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if document.status == DocumentStatus.PROCESSING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document is already being processed",
        )

    # Process the document through OCR + LLM pipeline
    result = process_document(db, document_id)

    return ProcessingResultResponse(
        success=result.success,
        document_id=result.document_id,
        extracted_data=result.extracted_data,
        confidence=result.confidence,
        needs_review=result.confidence < 0.8,
        errors=result.errors,
        linked_requirement_id=result.linked_requirement_id,
    )
