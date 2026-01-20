"""Unit tests for OCR processor."""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import io
import sys


class TestOCRProcessor:
    """Tests for the OCR processor."""

    @pytest.fixture
    def processor(self):
        """Create an OCR processor with mocked dependencies."""
        # Create a mock pytesseract module
        mock_pytesseract = MagicMock()
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"

        with patch.dict(sys.modules, {'pytesseract': mock_pytesseract}):
            with patch('app.ai.ocr.settings') as mock_settings:
                mock_settings.use_google_vision = False
                mock_settings.google_vision_api_key = None
                mock_settings.tesseract_path = None

                from app.ai.ocr import OCRProcessor
                processor = OCRProcessor()
                processor._tesseract_available = True

                return processor

    def test_extract_text_pdf(self, processor):
        """extract_text should route PDF to _extract_from_pdf."""
        with patch.object(processor, '_extract_from_pdf') as mock_extract:
            mock_extract.return_value = "PDF text content"

            result = processor.extract_text("/path/to/doc.pdf", "application/pdf")

            assert result == "PDF text content"
            mock_extract.assert_called_once_with("/path/to/doc.pdf")

    def test_extract_text_image(self, processor):
        """extract_text should route images to _extract_from_image."""
        with patch.object(processor, '_extract_from_image') as mock_extract:
            mock_extract.return_value = "Image text content"

            result = processor.extract_text("/path/to/doc.png", "image/png")

            assert result == "Image text content"
            mock_extract.assert_called_once_with("/path/to/doc.png")

    def test_extract_text_jpeg(self, processor):
        """extract_text should handle JPEG images."""
        with patch.object(processor, '_extract_from_image') as mock_extract:
            mock_extract.return_value = "JPEG text"

            result = processor.extract_text("/path/to/doc.jpg", "image/jpeg")

            assert result == "JPEG text"

    def test_extract_text_unsupported_type(self, processor):
        """extract_text should raise for unsupported MIME types."""
        with pytest.raises(ValueError, match="Unsupported MIME type"):
            processor.extract_text("/path/to/doc.docx", "application/msword")

    def test_extract_text_from_bytes_pdf(self, processor):
        """extract_text_from_bytes should route PDF bytes correctly."""
        with patch.object(processor, '_extract_from_pdf_bytes') as mock_extract:
            mock_extract.return_value = "PDF text from bytes"

            result = processor.extract_text_from_bytes(b"PDF content", "application/pdf")

            assert result == "PDF text from bytes"

    def test_extract_text_from_bytes_image(self, processor):
        """extract_text_from_bytes should route image bytes correctly."""
        with patch.object(processor, '_extract_from_image_bytes') as mock_extract:
            mock_extract.return_value = "Image text from bytes"

            result = processor.extract_text_from_bytes(b"PNG content", "image/png")

            assert result == "Image text from bytes"

    def test_ocr_with_tesseract(self, processor):
        """_ocr_with_tesseract should call pytesseract correctly."""
        mock_pytesseract = MagicMock()
        mock_pytesseract.image_to_string.return_value = "  Extracted text  "

        with patch.dict(sys.modules, {'pytesseract': mock_pytesseract}):
            mock_image = MagicMock()

            result = processor._ocr_with_tesseract(mock_image)

            assert result == "Extracted text"  # Should be stripped
            mock_pytesseract.image_to_string.assert_called_once()

    def test_ocr_with_tesseract_config(self, processor):
        """_ocr_with_tesseract should use custom config."""
        mock_pytesseract = MagicMock()
        mock_pytesseract.image_to_string.return_value = "Text"

        with patch.dict(sys.modules, {'pytesseract': mock_pytesseract}):
            mock_image = MagicMock()

            processor._ocr_with_tesseract(mock_image)

            # Check that custom config was passed
            call_args = mock_pytesseract.image_to_string.call_args
            assert "config" in call_args.kwargs or len(call_args.args) > 1

    def test_ocr_image_no_engine_available(self):
        """_ocr_image should raise when no OCR engine is available."""
        with patch('app.ai.ocr.settings') as mock_settings:
            mock_settings.use_google_vision = False
            mock_settings.google_vision_api_key = None
            mock_settings.tesseract_path = None

            from app.ai.ocr import OCRProcessor
            processor = OCRProcessor()
            processor._tesseract_available = False

            with pytest.raises(RuntimeError, match="No OCR engine available"):
                processor._ocr_image(MagicMock())

    def test_ocr_image_uses_google_vision_when_configured(self):
        """_ocr_image should prefer Google Vision when configured."""
        with patch('app.ai.ocr.settings') as mock_settings:
            mock_settings.use_google_vision = True
            mock_settings.google_vision_api_key = "test-key"
            mock_settings.tesseract_path = None

            from app.ai.ocr import OCRProcessor
            processor = OCRProcessor()

            with patch.object(processor, '_ocr_with_google_vision') as mock_gv:
                mock_gv.return_value = "Vision text"
                mock_image = MagicMock()

                result = processor._ocr_image(mock_image)

                assert result == "Vision text"
                mock_gv.assert_called_once_with(mock_image)


class TestOCRProcessorPDF:
    """Tests for PDF processing."""

    def test_extract_from_pdf_single_page(self):
        """_extract_from_pdf should process single page PDF."""
        mock_convert = MagicMock(return_value=[MagicMock()])
        mock_pdf2image = MagicMock()
        mock_pdf2image.convert_from_path = mock_convert

        mock_pytesseract = MagicMock()
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"
        mock_pytesseract.image_to_string.return_value = "Page 1 text"

        with patch.dict(sys.modules, {'pdf2image': mock_pdf2image, 'pytesseract': mock_pytesseract}):
            with patch('app.ai.ocr.settings') as mock_settings:
                mock_settings.use_google_vision = False
                mock_settings.tesseract_path = None

                from app.ai.ocr import OCRProcessor
                processor = OCRProcessor()
                processor._tesseract_available = True

                result = processor._extract_from_pdf("/path/to/doc.pdf")

                assert "Page 1" in result
                assert "Page 1 text" in result

    def test_extract_from_pdf_multi_page(self):
        """_extract_from_pdf should process multiple pages."""
        mock_convert = MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock()])
        mock_pdf2image = MagicMock()
        mock_pdf2image.convert_from_path = mock_convert

        mock_pytesseract = MagicMock()
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"
        mock_pytesseract.image_to_string.side_effect = ["Page 1", "Page 2", "Page 3"]

        with patch.dict(sys.modules, {'pdf2image': mock_pdf2image, 'pytesseract': mock_pytesseract}):
            with patch('app.ai.ocr.settings') as mock_settings:
                mock_settings.use_google_vision = False
                mock_settings.tesseract_path = None

                from app.ai.ocr import OCRProcessor
                processor = OCRProcessor()
                processor._tesseract_available = True

                result = processor._extract_from_pdf("/path/to/doc.pdf")

                assert "Page 1" in result
                assert "Page 2" in result
                assert "Page 3" in result

    def test_extract_from_pdf_missing_dependency(self):
        """_extract_from_pdf should raise when pdf2image not installed."""
        # Remove pdf2image from sys.modules to simulate missing dependency
        with patch.dict(sys.modules, {'pdf2image': None}):
            with patch('app.ai.ocr.settings') as mock_settings:
                mock_settings.use_google_vision = False
                mock_settings.tesseract_path = None

                from app.ai.ocr import OCRProcessor
                processor = OCRProcessor()

                with pytest.raises(RuntimeError, match="pdf2image is required"):
                    processor._extract_from_pdf("/path/to/doc.pdf")


class TestOCRProcessorImage:
    """Tests for image processing."""

    def test_extract_from_image(self):
        """_extract_from_image should open and process image file."""
        mock_image = MagicMock()
        mock_pil = MagicMock()
        mock_pil.Image.open.return_value = mock_image

        mock_pytesseract = MagicMock()
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"
        mock_pytesseract.image_to_string.return_value = "Image text"

        with patch.dict(sys.modules, {'PIL': mock_pil, 'PIL.Image': mock_pil.Image, 'pytesseract': mock_pytesseract}):
            with patch('app.ai.ocr.settings') as mock_settings:
                mock_settings.use_google_vision = False
                mock_settings.tesseract_path = None

                from app.ai.ocr import OCRProcessor
                processor = OCRProcessor()
                processor._tesseract_available = True

                result = processor._extract_from_image("/path/to/image.png")

                assert result == "Image text"

    def test_extract_from_image_bytes(self):
        """_extract_from_image_bytes should open image from bytes."""
        mock_image = MagicMock()
        mock_pil = MagicMock()
        mock_pil.Image.open.return_value = mock_image

        mock_pytesseract = MagicMock()
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"
        mock_pytesseract.image_to_string.return_value = "Bytes image text"

        with patch.dict(sys.modules, {'PIL': mock_pil, 'PIL.Image': mock_pil.Image, 'pytesseract': mock_pytesseract}):
            with patch('app.ai.ocr.settings') as mock_settings:
                mock_settings.use_google_vision = False
                mock_settings.tesseract_path = None

                from app.ai.ocr import OCRProcessor
                processor = OCRProcessor()
                processor._tesseract_available = True

                result = processor._extract_from_image_bytes(b"PNG content")

                assert result == "Bytes image text"


class TestGetOCRProcessor:
    """Tests for the get_ocr_processor singleton."""

    def test_get_ocr_processor_returns_instance(self):
        """get_ocr_processor should return an OCRProcessor instance."""
        mock_pytesseract = MagicMock()
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"

        with patch.dict(sys.modules, {'pytesseract': mock_pytesseract}):
            with patch('app.ai.ocr.settings') as mock_settings:
                mock_settings.use_google_vision = False
                mock_settings.tesseract_path = None

                # Reset singleton
                import app.ai.ocr as ocr_module
                ocr_module._ocr_processor = None

                from app.ai.ocr import get_ocr_processor, OCRProcessor

                processor = get_ocr_processor()

                assert isinstance(processor, OCRProcessor)

    def test_get_ocr_processor_returns_same_instance(self):
        """get_ocr_processor should return the same singleton instance."""
        mock_pytesseract = MagicMock()
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"

        with patch.dict(sys.modules, {'pytesseract': mock_pytesseract}):
            with patch('app.ai.ocr.settings') as mock_settings:
                mock_settings.use_google_vision = False
                mock_settings.tesseract_path = None

                # Reset singleton
                import app.ai.ocr as ocr_module
                ocr_module._ocr_processor = None

                from app.ai.ocr import get_ocr_processor

                processor1 = get_ocr_processor()
                processor2 = get_ocr_processor()

                assert processor1 is processor2
