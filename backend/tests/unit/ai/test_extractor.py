"""Unit tests for LLM extractor."""
import pytest
import json
from unittest.mock import MagicMock, patch


class TestExtractionResult:
    """Tests for the ExtractionResult class."""

    def test_needs_review_low_confidence(self):
        """needs_review should return True when confidence is below threshold."""
        from app.ai.extractor import ExtractionResult

        result = ExtractionResult(
            data={"field": "value"},
            confidence=0.5,  # Below default threshold of 0.75
            field_confidences={"field": 0.5},
            raw_response="{}",
        )

        assert result.needs_review is True

    def test_needs_review_high_confidence(self):
        """needs_review should return False when confidence is above threshold."""
        from app.ai.extractor import ExtractionResult

        result = ExtractionResult(
            data={"field": "value"},
            confidence=0.95,
            field_confidences={"field": 0.95},
            raw_response="{}",
        )

        assert result.needs_review is False

    def test_to_dict(self):
        """to_dict should return proper structure."""
        from app.ai.extractor import ExtractionResult

        result = ExtractionResult(
            data={"name": "Test"},
            confidence=0.9,
            field_confidences={"name": 0.9},
            raw_response='{"name": "Test"}',
            errors=["warning"],
        )

        d = result.to_dict()

        assert d["data"] == {"name": "Test"}
        assert d["confidence"] == 0.9
        assert d["field_confidences"] == {"name": 0.9}
        assert "needs_review" in d
        assert d["errors"] == ["warning"]


class TestLLMExtractor:
    """Tests for the LLM extractor."""

    @pytest.fixture
    def extractor(self):
        """Create an extractor instance."""
        from app.ai.extractor import LLMExtractor

        return LLMExtractor()

    @pytest.fixture
    def expected_fields(self):
        """Sample expected fields for extraction."""
        return [
            {"name": "named_insured", "type": "string", "required": True},
            {"name": "policy_number", "type": "string", "required": True},
            {"name": "expiration_date", "type": "date", "required": True},
            {"name": "general_liability_limit", "type": "number", "required": True},
            {"name": "auto_liability_limit", "type": "number", "required": False},
        ]

    def test_extract_no_api_key(self, extractor, expected_fields):
        """Extract should return error when API key not configured."""
        with patch('app.ai.extractor.settings') as mock_settings:
            mock_settings.openai_api_key = None

            result = extractor.extract(
                text="Sample document text",
                extraction_prompt="Extract fields",
                expected_fields=expected_fields,
            )

            assert result.data == {}
            assert result.confidence == 0.0
            assert "not configured" in result.errors[0]

    @patch('app.ai.extractor.settings')
    def test_extract_success(self, mock_settings, extractor, expected_fields):
        """Successful extraction should parse JSON response."""
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = "gpt-4"
        mock_settings.extraction_confidence_threshold = 0.75

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"named_insured": "Test Company", "policy_number": "POL-123"}'
                )
            )
        ]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch.object(extractor, '_get_client', return_value=mock_client):
            result = extractor.extract(
                text="CERTIFICATE OF INSURANCE\nInsured: Test Company\nPolicy: POL-123",
                extraction_prompt="Extract the insurance details.",
                expected_fields=expected_fields,
            )

            assert result.data["named_insured"] == "Test Company"
            assert result.data["policy_number"] == "POL-123"

    @patch('app.ai.extractor.settings')
    def test_extract_json_in_markdown(self, mock_settings, extractor, expected_fields):
        """Extract should handle JSON wrapped in markdown code blocks."""
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = "gpt-4"

        # Response with JSON wrapped in markdown
        response_content = '''```json
{"named_insured": "ABC Corp", "policy_number": "POL-456"}
```'''

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=response_content))
        ]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch.object(extractor, '_get_client', return_value=mock_client):
            # The regex in _parse_response should extract the JSON
            result = extractor._parse_response(response_content)

            assert result.get("named_insured") == "ABC Corp"

    @patch('app.ai.extractor.settings')
    def test_extract_openai_error(self, mock_settings, extractor, expected_fields):
        """API errors should be handled gracefully."""
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = "gpt-4"

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API rate limit")

        with patch.object(extractor, '_get_client', return_value=mock_client):
            result = extractor.extract(
                text="Document text",
                extraction_prompt="Extract fields",
                expected_fields=expected_fields,
            )

            assert result.data == {}
            assert result.confidence == 0.0
            assert "API rate limit" in result.errors[0]

    def test_build_system_prompt(self, extractor):
        """System prompt should contain extraction guidelines."""
        prompt = extractor._build_system_prompt()

        assert "JSON" in prompt
        assert "date" in prompt.lower()
        assert "OCR" in prompt

    def test_parse_response_valid_json(self, extractor):
        """_parse_response should parse valid JSON."""
        response = '{"name": "Test", "value": 123}'

        result = extractor._parse_response(response)

        assert result == {"name": "Test", "value": 123}

    def test_parse_response_invalid_json(self, extractor):
        """_parse_response should return empty dict for invalid JSON."""
        response = "This is not valid JSON"

        result = extractor._parse_response(response)

        assert result == {}

    def test_parse_response_json_in_text(self, extractor):
        """_parse_response should extract JSON embedded in text."""
        response = 'Here is the data: {"key": "value"} extracted from document.'

        result = extractor._parse_response(response)

        assert result == {"key": "value"}

    def test_calculate_field_confidences_present(self, extractor, expected_fields):
        """High confidence for valid values."""
        data = {
            "named_insured": "Test Company",
            "policy_number": "POL-123",
            "expiration_date": "2025-01-01",
            "general_liability_limit": 1000000,
        }

        confidences = extractor._calculate_field_confidences(data, expected_fields)

        assert confidences["named_insured"] == 0.95
        assert confidences["policy_number"] == 0.95
        assert confidences["expiration_date"] == 0.95

    def test_calculate_field_confidences_missing_required(self, extractor, expected_fields):
        """Low confidence for missing required fields."""
        data = {"named_insured": "Test"}  # Missing required fields

        confidences = extractor._calculate_field_confidences(data, expected_fields)

        assert confidences["named_insured"] == 0.95
        assert confidences["policy_number"] == 0.3  # Required but missing
        assert confidences["auto_liability_limit"] == 0.8  # Optional and missing

    def test_calculate_field_confidences_wrong_type(self, extractor, expected_fields):
        """Medium confidence for wrong type."""
        data = {
            "named_insured": "Test",
            "policy_number": "POL-123",
            "expiration_date": "not-a-date",  # Wrong format
            "general_liability_limit": "not-a-number",
        }

        confidences = extractor._calculate_field_confidences(data, expected_fields)

        assert confidences["expiration_date"] == 0.5  # Wrong type
        assert confidences["general_liability_limit"] == 0.5

    def test_validate_field_type_string(self, extractor):
        """String validation should work."""
        assert extractor._validate_field_type("hello", "string") is True
        assert extractor._validate_field_type(123, "string") is False

    def test_validate_field_type_date(self, extractor):
        """Date validation should check ISO format."""
        assert extractor._validate_field_type("2025-01-01", "date") is True
        assert extractor._validate_field_type("01/01/2025", "date") is False
        assert extractor._validate_field_type("not-a-date", "date") is False

    def test_validate_field_type_number(self, extractor):
        """Number validation should accept int and float."""
        assert extractor._validate_field_type(100, "number") is True
        assert extractor._validate_field_type(1000000.50, "number") is True
        assert extractor._validate_field_type("100", "number") is False

    def test_validate_field_type_boolean(self, extractor):
        """Boolean validation should only accept bool."""
        assert extractor._validate_field_type(True, "boolean") is True
        assert extractor._validate_field_type(False, "boolean") is True
        assert extractor._validate_field_type("true", "boolean") is False

    def test_validate_field_type_none(self, extractor):
        """None should be valid for any type."""
        assert extractor._validate_field_type(None, "string") is True
        assert extractor._validate_field_type(None, "number") is True

    def test_clean_value_currency(self, extractor):
        """_clean_value should remove currency symbols."""
        result = extractor._clean_value("$1,000,000", "number")
        assert result == 1000000.0

        result = extractor._clean_value("$500.50", "number")
        assert result == 500.5

    def test_clean_value_date_formats(self, extractor):
        """_clean_value should normalize various date formats."""
        # ISO format (already correct)
        assert extractor._clean_value("2025-01-15", "date") == "2025-01-15"

        # US format
        assert extractor._clean_value("01/15/2025", "date") == "2025-01-15"

        # Dash format
        assert extractor._clean_value("01-15-2025", "date") == "2025-01-15"

    def test_clean_value_boolean(self, extractor):
        """_clean_value should convert string booleans."""
        assert extractor._clean_value("true", "boolean") is True
        assert extractor._clean_value("yes", "boolean") is True
        assert extractor._clean_value("X", "boolean") is True
        assert extractor._clean_value("false", "boolean") is False
        assert extractor._clean_value("no", "boolean") is False

    def test_clean_extracted_data(self, extractor, expected_fields):
        """_clean_extracted_data should clean all fields."""
        data = {
            "named_insured": "Test Company",
            "policy_number": "POL-123",
            "expiration_date": "01/15/2025",
            "general_liability_limit": "$1,000,000",
            "auto_liability_limit": None,
        }

        result = extractor._clean_extracted_data(data, expected_fields)

        assert result["expiration_date"] == "2025-01-15"
        assert result["general_liability_limit"] == 1000000.0
        assert result["auto_liability_limit"] is None

    def test_calculate_overall_confidence(self, extractor):
        """Overall confidence should be average of field confidences."""
        confidences = {"field1": 1.0, "field2": 0.5, "field3": 0.8}

        result = extractor._calculate_overall_confidence(confidences)

        expected = (1.0 + 0.5 + 0.8) / 3
        assert abs(result - expected) < 0.001

    def test_calculate_overall_confidence_empty(self, extractor):
        """Empty confidences should return 0."""
        result = extractor._calculate_overall_confidence({})

        assert result == 0.0


class TestSampleCOIData:
    """Tests using the sample COI data fixture."""

    @pytest.fixture
    def sample_coi_data(self):
        """Load sample COI test data."""
        import json
        from pathlib import Path

        fixture_path = Path(__file__).parent.parent.parent / "fixtures" / "sample_coi_data.json"
        with open(fixture_path) as f:
            return json.load(f)

    def test_sample_data_structure(self, sample_coi_data):
        """Verify sample data has expected structure."""
        assert "samples" in sample_coi_data
        assert "edge_cases" in sample_coi_data
        assert "vendor_test_data" in sample_coi_data
        assert len(sample_coi_data["samples"]) >= 5

    def test_sample_coi_001_expected_fields(self, sample_coi_data):
        """Verify COI 001 has correct expected extraction."""
        coi_001 = next(s for s in sample_coi_data["samples"] if s["id"] == "coi_001")
        expected = coi_001["expected_extraction"]

        assert expected["named_insured"] == "ABC Construction Services LLC"
        assert expected["policy_number"] == "GL-2024-001234"
        assert expected["carrier_name"] == "National Insurance Company"
        assert expected["general_liability_limit"] == 1000000
        assert expected["additional_insured"] is True

    def test_sample_coi_003_is_expired(self, sample_coi_data):
        """COI 003 should be marked as expired in validation tests."""
        coi_003 = next(s for s in sample_coi_data["samples"] if s["id"] == "coi_003")

        assert coi_003["validation_tests"]["is_current"] is False

    def test_edge_case_ocr_errors(self, sample_coi_data):
        """Edge case 001 tests OCR error correction."""
        edge_001 = next(e for e in sample_coi_data["edge_cases"] if e["id"] == "edge_001")

        # Raw text has OCR errors (0 instead of O, 1 instead of I)
        assert "CERTIF1CATE" in edge_001["raw_text_simulation"]

        # Expected extraction should have corrected values
        assert edge_001["expected_extraction"]["named_insured"] == "Quality Plumbing Svcs"
