"""LLM-based data extraction from document text."""
import json
import re
from datetime import date, datetime
from typing import Any, Optional

from app.config.settings import get_settings

settings = get_settings()


class ExtractionResult:
    """Result of AI extraction with confidence scores."""

    def __init__(
        self,
        data: dict[str, Any],
        confidence: float,
        field_confidences: dict[str, float],
        raw_response: str,
        errors: list[str] = None,
    ):
        self.data = data
        self.confidence = confidence
        self.field_confidences = field_confidences
        self.raw_response = raw_response
        self.errors = errors or []

    @property
    def needs_review(self) -> bool:
        """Check if extraction needs human review."""
        return self.confidence < settings.extraction_confidence_threshold

    def to_dict(self) -> dict:
        return {
            "data": self.data,
            "confidence": self.confidence,
            "field_confidences": self.field_confidences,
            "needs_review": self.needs_review,
            "errors": self.errors,
        }


class LLMExtractor:
    """Extracts structured data from document text using LLM."""

    def __init__(self):
        self.client = None
        self.model = settings.openai_model

    def _get_client(self):
        """Lazy-load OpenAI client."""
        if self.client is None:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=settings.openai_api_key)
            except ImportError:
                raise RuntimeError("openai package is required for LLM extraction")
        return self.client

    def extract(
        self,
        text: str,
        extraction_prompt: str,
        expected_fields: list[dict],
    ) -> ExtractionResult:
        """
        Extract structured data from document text.

        Args:
            text: Raw text from OCR
            extraction_prompt: LLM prompt for extraction (from YAML config)
            expected_fields: List of expected fields with types

        Returns:
            ExtractionResult with extracted data and confidence scores
        """
        if not settings.openai_api_key:
            return ExtractionResult(
                data={},
                confidence=0.0,
                field_confidences={},
                raw_response="",
                errors=["OpenAI API key not configured"],
            )

        # Build the full prompt
        system_prompt = self._build_system_prompt()
        user_prompt = f"{extraction_prompt}\n\nDocument text:\n```\n{text}\n```"

        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                response_format={"type": "json_object"},
            )

            raw_response = response.choices[0].message.content
            extracted_data = self._parse_response(raw_response)

            # Calculate confidence scores
            field_confidences = self._calculate_field_confidences(
                extracted_data, expected_fields
            )
            overall_confidence = self._calculate_overall_confidence(field_confidences)

            # Validate and clean data
            cleaned_data = self._clean_extracted_data(extracted_data, expected_fields)

            return ExtractionResult(
                data=cleaned_data,
                confidence=overall_confidence,
                field_confidences=field_confidences,
                raw_response=raw_response,
            )

        except Exception as e:
            return ExtractionResult(
                data={},
                confidence=0.0,
                field_confidences={},
                raw_response="",
                errors=[str(e)],
            )

    def _build_system_prompt(self) -> str:
        """Build the system prompt for extraction."""
        return """You are an expert document analyst specializing in insurance certificates and compliance documents.

Your task is to extract structured data from document text that was obtained via OCR.

Important guidelines:
1. Return ONLY valid JSON - no explanations or additional text
2. Use null for any fields you cannot find or are uncertain about
3. For dates, use ISO format (YYYY-MM-DD)
4. For currency/money amounts, return as numbers without symbols (e.g., 1000000 not "$1,000,000")
5. For boolean fields, use true/false
6. Be aware of common OCR errors: 0/O, 1/I/l, 5/S, 8/B
7. If the document quality is poor, extract what you can and leave uncertain fields as null

Always prioritize accuracy over completeness."""

    def _parse_response(self, raw_response: str) -> dict[str, Any]:
        """Parse the JSON response from the LLM."""
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {}

    def _calculate_field_confidences(
        self,
        data: dict[str, Any],
        expected_fields: list[dict],
    ) -> dict[str, float]:
        """Calculate confidence scores for each field."""
        confidences = {}

        for field in expected_fields:
            field_name = field["name"]
            field_type = field.get("type", "string")
            is_required = field.get("required", False)

            value = data.get(field_name)

            if value is None:
                # Missing field - low confidence if required
                confidences[field_name] = 0.3 if is_required else 0.8
            elif self._validate_field_type(value, field_type):
                # Value present and valid type
                confidences[field_name] = 0.95
            else:
                # Value present but wrong type
                confidences[field_name] = 0.5

        return confidences

    def _validate_field_type(self, value: Any, expected_type: str) -> bool:
        """Validate that a value matches the expected type."""
        if value is None:
            return True  # None is valid for optional fields

        type_validators = {
            "string": lambda v: isinstance(v, str),
            "text": lambda v: isinstance(v, str),
            "number": lambda v: isinstance(v, (int, float)),
            "date": lambda v: self._is_valid_date(v),
            "boolean": lambda v: isinstance(v, bool),
            "array": lambda v: isinstance(v, list),
        }

        validator = type_validators.get(expected_type, lambda v: True)
        return validator(value)

    def _is_valid_date(self, value: Any) -> bool:
        """Check if a value is a valid date string."""
        if not isinstance(value, str):
            return False
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def _calculate_overall_confidence(
        self, field_confidences: dict[str, float]
    ) -> float:
        """Calculate overall extraction confidence."""
        if not field_confidences:
            return 0.0
        return sum(field_confidences.values()) / len(field_confidences)

    def _clean_extracted_data(
        self,
        data: dict[str, Any],
        expected_fields: list[dict],
    ) -> dict[str, Any]:
        """Clean and normalize extracted data."""
        cleaned = {}

        for field in expected_fields:
            field_name = field["name"]
            field_type = field.get("type", "string")
            value = data.get(field_name)

            if value is not None:
                cleaned[field_name] = self._clean_value(value, field_type)
            else:
                cleaned[field_name] = None

        return cleaned

    def _clean_value(self, value: Any, field_type: str) -> Any:
        """Clean a single value based on its type."""
        if value is None:
            return None

        if field_type == "number":
            # Convert string numbers
            if isinstance(value, str):
                # Remove currency symbols and commas
                cleaned = re.sub(r'[$,]', '', value)
                try:
                    return float(cleaned)
                except ValueError:
                    return None
            return value

        if field_type == "date":
            # Normalize date format
            if isinstance(value, str):
                # Try various date formats
                formats = [
                    "%Y-%m-%d",
                    "%m/%d/%Y",
                    "%m-%d-%Y",
                    "%d/%m/%Y",
                    "%B %d, %Y",
                    "%b %d, %Y",
                ]
                for fmt in formats:
                    try:
                        dt = datetime.strptime(value, fmt)
                        return dt.strftime("%Y-%m-%d")
                    except ValueError:
                        continue
            return value

        if field_type == "boolean":
            if isinstance(value, str):
                return value.lower() in ("true", "yes", "1", "x", "checked")
            return bool(value)

        return value


# Global extractor instance
_extractor: Optional[LLMExtractor] = None


def get_llm_extractor() -> LLMExtractor:
    """Get the global LLM extractor instance."""
    global _extractor
    if _extractor is None:
        _extractor = LLMExtractor()
    return _extractor
