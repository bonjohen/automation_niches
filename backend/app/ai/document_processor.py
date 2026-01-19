"""Document processing pipeline - OCR + LLM extraction."""
import os
from datetime import datetime
from typing import Any, Optional
import uuid

from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.document import Document, DocumentType, DocumentStatus
from app.models.requirement import Requirement, RequirementStatus
from app.ai.ocr import get_ocr_processor
from app.ai.extractor import get_llm_extractor, ExtractionResult

settings = get_settings()


class DocumentProcessingResult:
    """Result of document processing."""

    def __init__(
        self,
        success: bool,
        document_id: uuid.UUID,
        raw_text: str = "",
        extracted_data: dict[str, Any] = None,
        confidence: float = 0.0,
        field_confidences: dict[str, float] = None,
        errors: list[str] = None,
        linked_requirement_id: Optional[uuid.UUID] = None,
    ):
        self.success = success
        self.document_id = document_id
        self.raw_text = raw_text
        self.extracted_data = extracted_data or {}
        self.confidence = confidence
        self.field_confidences = field_confidences or {}
        self.errors = errors or []
        self.linked_requirement_id = linked_requirement_id


class DocumentProcessor:
    """Processes documents through OCR and LLM extraction pipeline."""

    def __init__(self, db: Session):
        self.db = db
        self.ocr = get_ocr_processor()
        self.extractor = get_llm_extractor()

    def process_document(self, document_id: uuid.UUID) -> DocumentProcessingResult:
        """
        Process a document through the full extraction pipeline.

        1. Load document from database
        2. Extract text via OCR
        3. Extract structured data via LLM
        4. Update document record
        5. Optionally link to requirements and update their due dates
        """
        # Load document
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return DocumentProcessingResult(
                success=False,
                document_id=document_id,
                errors=["Document not found"],
            )

        # Update status to processing
        document.status = DocumentStatus.PROCESSING.value
        self.db.commit()

        try:
            # Step 1: OCR text extraction
            raw_text = self._extract_text(document)

            # Step 2: Get document type configuration
            doc_type = self._get_document_type(document)

            # Step 3: LLM extraction
            extraction_result = self._extract_data(raw_text, doc_type)

            # Step 4: Update document record
            self._update_document(document, raw_text, extraction_result)

            # Step 5: Link to requirements if applicable
            linked_req_id = None
            if extraction_result.data and document.entity_id:
                linked_req_id = self._link_to_requirement(document, extraction_result)

            self.db.commit()

            return DocumentProcessingResult(
                success=True,
                document_id=document_id,
                raw_text=raw_text,
                extracted_data=extraction_result.data,
                confidence=extraction_result.confidence,
                field_confidences=extraction_result.field_confidences,
                errors=extraction_result.errors,
                linked_requirement_id=linked_req_id,
            )

        except Exception as e:
            # Update document with error
            document.status = DocumentStatus.FAILED.value
            document.processing_error = str(e)
            self.db.commit()

            return DocumentProcessingResult(
                success=False,
                document_id=document_id,
                errors=[str(e)],
            )

    def _extract_text(self, document: Document) -> str:
        """Extract text from document using OCR."""
        # Build file path
        file_path = os.path.join(settings.local_storage_path, document.storage_path)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document file not found: {file_path}")

        return self.ocr.extract_text(file_path, document.mime_type)

    def _get_document_type(self, document: Document) -> Optional[DocumentType]:
        """Get the document type configuration."""
        if document.document_type_id:
            return self.db.query(DocumentType).filter(
                DocumentType.id == document.document_type_id
            ).first()
        return None

    def _extract_data(
        self, raw_text: str, doc_type: Optional[DocumentType]
    ) -> ExtractionResult:
        """Extract structured data using LLM."""
        if not doc_type or not doc_type.extraction_prompt:
            # No extraction configuration - return empty result
            return ExtractionResult(
                data={},
                confidence=0.0,
                field_confidences={},
                raw_response="",
                errors=["No extraction configuration for this document type"],
            )

        # Get expected fields from extraction schema
        expected_fields = []
        if doc_type.extraction_schema and "properties" in doc_type.extraction_schema:
            for field_name, field_config in doc_type.extraction_schema["properties"].items():
                expected_fields.append({
                    "name": field_name,
                    "type": field_config.get("type", "string"),
                    "required": field_name in doc_type.extraction_schema.get("required", []),
                })

        return self.extractor.extract(
            text=raw_text,
            extraction_prompt=doc_type.extraction_prompt,
            expected_fields=expected_fields,
        )

    def _update_document(
        self, document: Document, raw_text: str, extraction_result: ExtractionResult
    ):
        """Update document record with extraction results."""
        document.raw_text = raw_text
        document.extracted_data = extraction_result.data
        document.extraction_confidence = extraction_result.confidence
        document.field_confidences = extraction_result.field_confidences
        document.processed_at = datetime.utcnow()
        document.processing_error = (
            "; ".join(extraction_result.errors) if extraction_result.errors else None
        )

        # Set status based on confidence
        if extraction_result.errors and not extraction_result.data:
            document.status = DocumentStatus.FAILED.value
        elif extraction_result.needs_review:
            document.status = DocumentStatus.NEEDS_REVIEW.value
        else:
            document.status = DocumentStatus.PROCESSED.value

    def _link_to_requirement(
        self, document: Document, extraction_result: ExtractionResult
    ) -> Optional[uuid.UUID]:
        """
        Link document to relevant requirement and update due date.

        For COIs, this updates the requirement's due_date to the certificate's
        expiration_date.
        """
        if not document.entity_id or not document.document_type_id:
            return None

        # Get document type to find related requirement types
        doc_type = self._get_document_type(document)
        if not doc_type:
            return None

        # Find requirements for this entity that accept this document type
        from app.models.requirement import RequirementType

        # Find requirement types that use this document type
        req_types = self.db.query(RequirementType).filter(
            RequirementType.required_document_types.contains([doc_type.code])
        ).all()

        if not req_types:
            return None

        req_type_ids = [rt.id for rt in req_types]

        # Find open requirement for this entity
        requirement = self.db.query(Requirement).filter(
            Requirement.entity_id == document.entity_id,
            Requirement.requirement_type_id.in_(req_type_ids),
            Requirement.status.in_([
                RequirementStatus.PENDING.value,
                RequirementStatus.EXPIRING_SOON.value,
                RequirementStatus.EXPIRED.value,
            ]),
        ).first()

        if not requirement:
            return None

        # Link document to requirement
        requirement.document_id = document.id

        # Update due date from extracted data if available
        expiration_date = extraction_result.data.get("expiration_date")
        if expiration_date:
            try:
                from datetime import datetime
                new_due_date = datetime.strptime(expiration_date, "%Y-%m-%d").date()
                requirement.due_date = new_due_date
            except (ValueError, TypeError):
                pass

        # Update status to compliant if confidence is high enough
        if extraction_result.confidence >= settings.extraction_confidence_threshold:
            requirement.status = RequirementStatus.COMPLIANT.value

        return requirement.id


def process_document(db: Session, document_id: uuid.UUID) -> DocumentProcessingResult:
    """Convenience function to process a document."""
    processor = DocumentProcessor(db)
    return processor.process_document(document_id)
