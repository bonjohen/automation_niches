"""Unit tests for document processor."""
import pytest
import uuid
from datetime import date, datetime
from unittest.mock import MagicMock, patch


class TestDocumentProcessingResult:
    """Tests for DocumentProcessingResult class."""

    def test_init_defaults(self):
        """Result should have sensible defaults."""
        from app.ai.document_processor import DocumentProcessingResult

        result = DocumentProcessingResult(
            success=True,
            document_id=uuid.uuid4(),
        )

        assert result.success is True
        assert result.raw_text == ""
        assert result.extracted_data == {}
        assert result.confidence == 0.0
        assert result.field_confidences == {}
        assert result.errors == []
        assert result.linked_requirement_id is None

    def test_init_with_values(self):
        """Result should accept all parameters."""
        from app.ai.document_processor import DocumentProcessingResult

        doc_id = uuid.uuid4()
        req_id = uuid.uuid4()

        result = DocumentProcessingResult(
            success=True,
            document_id=doc_id,
            raw_text="Sample text",
            extracted_data={"field": "value"},
            confidence=0.95,
            field_confidences={"field": 0.95},
            errors=["warning"],
            linked_requirement_id=req_id,
        )

        assert result.document_id == doc_id
        assert result.raw_text == "Sample text"
        assert result.extracted_data == {"field": "value"}
        assert result.confidence == 0.95
        assert result.linked_requirement_id == req_id


class TestDocumentProcessor:
    """Tests for the DocumentProcessor class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.fixture
    def processor(self, mock_db):
        """Create a document processor with mocked dependencies."""
        with patch('app.ai.document_processor.get_ocr_processor') as mock_ocr:
            with patch('app.ai.document_processor.get_llm_extractor') as mock_llm:
                mock_ocr.return_value = MagicMock()
                mock_llm.return_value = MagicMock()

                from app.ai.document_processor import DocumentProcessor

                processor = DocumentProcessor(mock_db)
                return processor

    @pytest.fixture
    def mock_document(self):
        """Create a mock document."""
        doc = MagicMock()
        doc.id = uuid.uuid4()
        doc.storage_path = "uploads/test.pdf"
        doc.mime_type = "application/pdf"
        doc.entity_id = uuid.uuid4()
        doc.document_type_id = uuid.uuid4()
        return doc

    @pytest.fixture
    def mock_document_type(self):
        """Create a mock document type."""
        doc_type = MagicMock()
        doc_type.id = uuid.uuid4()
        doc_type.code = "coi"
        doc_type.extraction_prompt = "Extract COI fields"
        doc_type.extraction_schema = {
            "properties": {
                "named_insured": {"type": "string"},
                "expiration_date": {"type": "date"},
                "general_liability_limit": {"type": "number"},
            },
            "required": ["named_insured", "expiration_date"],
        }
        return doc_type

    def test_process_document_not_found(self, processor, mock_db):
        """process_document should return error when document not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        doc_id = uuid.uuid4()

        result = processor.process_document(doc_id)

        assert result.success is False
        assert "not found" in result.errors[0].lower()

    def test_process_document_success(self, processor, mock_db, mock_document, mock_document_type):
        """process_document should successfully process a document."""
        from app.ai.extractor import ExtractionResult

        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_document,  # First call - get document
            mock_document_type,  # Second call - get document type
            mock_document_type,  # Third call - for _link_to_requirement
        ]

        # Mock OCR
        processor.ocr.extract_text.return_value = "CERTIFICATE OF INSURANCE\nInsured: Test Company"

        # Mock LLM extraction
        extraction_result = ExtractionResult(
            data={"named_insured": "Test Company", "expiration_date": "2025-01-01"},
            confidence=0.95,
            field_confidences={"named_insured": 0.95, "expiration_date": 0.95},
            raw_response="{}",
        )
        processor.extractor.extract.return_value = extraction_result

        # Mock file existence
        with patch('os.path.exists', return_value=True):
            with patch('app.ai.document_processor.settings') as mock_settings:
                mock_settings.local_storage_path = "/storage"
                mock_settings.extraction_confidence_threshold = 0.75

                # Mock requirement lookup to return None (no requirement to link)
                mock_db.query.return_value.filter.return_value.all.return_value = []

                result = processor.process_document(mock_document.id)

        assert result.success is True
        assert result.extracted_data["named_insured"] == "Test Company"
        assert result.confidence == 0.95

    def test_process_document_file_not_found(self, processor, mock_db, mock_document):
        """process_document should fail when file doesn't exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_document

        with patch('os.path.exists', return_value=False):
            with patch('app.ai.document_processor.settings') as mock_settings:
                mock_settings.local_storage_path = "/storage"

                result = processor.process_document(mock_document.id)

        assert result.success is False
        assert any("not found" in e.lower() for e in result.errors)

    def test_extract_text_calls_ocr(self, processor, mock_document):
        """_extract_text should call OCR processor."""
        processor.ocr.extract_text.return_value = "Extracted text"

        with patch('os.path.exists', return_value=True):
            with patch('app.ai.document_processor.settings') as mock_settings:
                mock_settings.local_storage_path = "/storage"

                result = processor._extract_text(mock_document)

        assert result == "Extracted text"
        processor.ocr.extract_text.assert_called_once()

    def test_get_document_type(self, processor, mock_db, mock_document, mock_document_type):
        """_get_document_type should query database."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_document_type

        result = processor._get_document_type(mock_document)

        assert result == mock_document_type

    def test_get_document_type_none(self, processor, mock_document):
        """_get_document_type should return None if no type_id."""
        mock_document.document_type_id = None

        result = processor._get_document_type(mock_document)

        assert result is None

    def test_extract_data_no_doc_type(self, processor):
        """_extract_data should return empty result without doc type config."""
        result = processor._extract_data("Sample text", None)

        assert result.data == {}
        assert "No extraction configuration" in result.errors[0]

    def test_extract_data_no_prompt(self, processor, mock_document_type):
        """_extract_data should return empty result without extraction prompt."""
        mock_document_type.extraction_prompt = None

        result = processor._extract_data("Sample text", mock_document_type)

        assert result.data == {}

    def test_extract_data_with_schema(self, processor, mock_document_type):
        """_extract_data should parse expected fields from schema."""
        from app.ai.extractor import ExtractionResult

        processor.extractor.extract.return_value = ExtractionResult(
            data={"named_insured": "Test"},
            confidence=0.9,
            field_confidences={"named_insured": 0.9},
            raw_response="{}",
        )

        result = processor._extract_data("Sample text", mock_document_type)

        # Verify extractor was called with expected fields from schema
        call_args = processor.extractor.extract.call_args
        expected_fields = call_args.kwargs.get("expected_fields", call_args[1].get("expected_fields"))

        field_names = [f["name"] for f in expected_fields]
        assert "named_insured" in field_names
        assert "expiration_date" in field_names

    def test_update_document_processed_status(self, processor, mock_document):
        """_update_document should set PROCESSED status for high confidence."""
        from app.ai.extractor import ExtractionResult

        with patch('app.ai.document_processor.settings') as mock_settings:
            mock_settings.extraction_confidence_threshold = 0.75

            extraction_result = ExtractionResult(
                data={"field": "value"},
                confidence=0.95,
                field_confidences={"field": 0.95},
                raw_response="{}",
            )

            processor._update_document(mock_document, "raw text", extraction_result)

        assert mock_document.status == "processed"
        assert mock_document.raw_text == "raw text"
        assert mock_document.extracted_data == {"field": "value"}

    def test_update_document_needs_review_status(self, processor, mock_document):
        """_update_document should set NEEDS_REVIEW status for low confidence."""
        from app.ai.extractor import ExtractionResult

        with patch('app.ai.document_processor.settings') as mock_settings:
            mock_settings.extraction_confidence_threshold = 0.75

            extraction_result = ExtractionResult(
                data={"field": "value"},
                confidence=0.5,  # Below threshold
                field_confidences={"field": 0.5},
                raw_response="{}",
            )

            processor._update_document(mock_document, "raw text", extraction_result)

        assert mock_document.status == "needs_review"

    def test_update_document_failed_status(self, processor, mock_document):
        """_update_document should set FAILED status when extraction fails."""
        from app.ai.extractor import ExtractionResult

        with patch('app.ai.document_processor.settings') as mock_settings:
            mock_settings.extraction_confidence_threshold = 0.75

            extraction_result = ExtractionResult(
                data={},
                confidence=0.0,
                field_confidences={},
                raw_response="",
                errors=["API error"],
            )

            processor._update_document(mock_document, "raw text", extraction_result)

        assert mock_document.status == "failed"
        assert mock_document.processing_error == "API error"


class TestLinkToRequirement:
    """Tests for requirement linking functionality."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def processor(self, mock_db):
        with patch('app.ai.document_processor.get_ocr_processor'):
            with patch('app.ai.document_processor.get_llm_extractor'):
                from app.ai.document_processor import DocumentProcessor
                return DocumentProcessor(mock_db)

    def test_link_no_entity_id(self, processor):
        """_link_to_requirement should return None without entity_id."""
        from app.ai.extractor import ExtractionResult

        mock_document = MagicMock()
        mock_document.entity_id = None

        result = processor._link_to_requirement(
            mock_document,
            ExtractionResult({}, 0.9, {}, ""),
        )

        assert result is None

    def test_link_no_document_type(self, processor, mock_db):
        """_link_to_requirement should return None without document type."""
        from app.ai.extractor import ExtractionResult

        mock_document = MagicMock()
        mock_document.entity_id = uuid.uuid4()
        mock_document.document_type_id = uuid.uuid4()

        # Mock _get_document_type to return None
        with patch.object(processor, '_get_document_type', return_value=None):
            result = processor._link_to_requirement(
                mock_document,
                ExtractionResult({}, 0.9, {}, ""),
            )

        assert result is None

    def test_link_updates_due_date(self, processor, mock_db):
        """_link_to_requirement should update requirement due date from extraction."""
        from app.ai.extractor import ExtractionResult

        mock_document = MagicMock()
        mock_document.entity_id = uuid.uuid4()
        mock_document.document_type_id = uuid.uuid4()

        mock_doc_type = MagicMock()
        mock_doc_type.code = "coi"

        mock_requirement = MagicMock()
        mock_requirement.id = uuid.uuid4()
        mock_requirement.due_date = date.today()

        # Setup database query mocks
        mock_db.query.return_value.filter.return_value.all.return_value = [MagicMock(id=uuid.uuid4())]
        mock_db.query.return_value.filter.return_value.first.return_value = mock_requirement

        extraction_result = ExtractionResult(
            data={"expiration_date": "2025-12-31"},
            confidence=0.9,
            field_confidences={},
            raw_response="",
        )

        with patch.object(processor, '_get_document_type', return_value=mock_doc_type):
            with patch('app.ai.document_processor.settings') as mock_settings:
                mock_settings.extraction_confidence_threshold = 0.75

                result = processor._link_to_requirement(mock_document, extraction_result)

        # Requirement should be linked
        assert mock_requirement.document_id == mock_document.id
        # Due date should be updated
        assert mock_requirement.due_date == date(2025, 12, 31)


class TestProcessDocumentFunction:
    """Tests for the convenience process_document function."""

    def test_process_document_creates_processor(self):
        """process_document function should create processor and call it."""
        with patch('app.ai.document_processor.DocumentProcessor') as MockProcessor:
            mock_processor_instance = MagicMock()
            MockProcessor.return_value = mock_processor_instance

            mock_result = MagicMock()
            mock_processor_instance.process_document.return_value = mock_result

            from app.ai.document_processor import process_document

            mock_db = MagicMock()
            doc_id = uuid.uuid4()

            result = process_document(mock_db, doc_id)

            MockProcessor.assert_called_once_with(mock_db)
            mock_processor_instance.process_document.assert_called_once_with(doc_id)
            assert result == mock_result
