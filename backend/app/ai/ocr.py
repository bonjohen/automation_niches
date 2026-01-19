"""OCR text extraction from documents."""
import io
import os
from pathlib import Path
from typing import Optional

from app.config.settings import get_settings

settings = get_settings()


class OCRProcessor:
    """Extracts text from images and PDFs using OCR."""

    def __init__(self):
        self.use_google_vision = settings.use_google_vision
        self._tesseract_available = False
        self._google_vision_client = None

        # Check Tesseract availability
        try:
            import pytesseract
            if settings.tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = settings.tesseract_path
            # Test if tesseract is available
            pytesseract.get_tesseract_version()
            self._tesseract_available = True
        except Exception:
            pass

    def extract_text(self, file_path: str, mime_type: str) -> str:
        """
        Extract text from a document file.

        Args:
            file_path: Path to the file
            mime_type: MIME type of the file

        Returns:
            Extracted text content
        """
        if mime_type == "application/pdf":
            return self._extract_from_pdf(file_path)
        elif mime_type.startswith("image/"):
            return self._extract_from_image(file_path)
        else:
            raise ValueError(f"Unsupported MIME type for OCR: {mime_type}")

    def extract_text_from_bytes(self, content: bytes, mime_type: str) -> str:
        """
        Extract text from file bytes.

        Args:
            content: File content as bytes
            mime_type: MIME type of the file

        Returns:
            Extracted text content
        """
        if mime_type == "application/pdf":
            return self._extract_from_pdf_bytes(content)
        elif mime_type.startswith("image/"):
            return self._extract_from_image_bytes(content)
        else:
            raise ValueError(f"Unsupported MIME type for OCR: {mime_type}")

    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from a PDF file."""
        try:
            from pdf2image import convert_from_path
        except ImportError:
            raise RuntimeError("pdf2image is required for PDF processing")

        # Convert PDF pages to images
        images = convert_from_path(file_path)

        # Extract text from each page
        all_text = []
        for i, image in enumerate(images):
            page_text = self._ocr_image(image)
            all_text.append(f"--- Page {i + 1} ---\n{page_text}")

        return "\n\n".join(all_text)

    def _extract_from_pdf_bytes(self, content: bytes) -> str:
        """Extract text from PDF bytes."""
        try:
            from pdf2image import convert_from_bytes
        except ImportError:
            raise RuntimeError("pdf2image is required for PDF processing")

        images = convert_from_bytes(content)

        all_text = []
        for i, image in enumerate(images):
            page_text = self._ocr_image(image)
            all_text.append(f"--- Page {i + 1} ---\n{page_text}")

        return "\n\n".join(all_text)

    def _extract_from_image(self, file_path: str) -> str:
        """Extract text from an image file."""
        try:
            from PIL import Image
        except ImportError:
            raise RuntimeError("Pillow is required for image processing")

        image = Image.open(file_path)
        return self._ocr_image(image)

    def _extract_from_image_bytes(self, content: bytes) -> str:
        """Extract text from image bytes."""
        try:
            from PIL import Image
        except ImportError:
            raise RuntimeError("Pillow is required for image processing")

        image = Image.open(io.BytesIO(content))
        return self._ocr_image(image)

    def _ocr_image(self, image) -> str:
        """Perform OCR on a PIL Image."""
        if self.use_google_vision and settings.google_vision_api_key:
            return self._ocr_with_google_vision(image)
        elif self._tesseract_available:
            return self._ocr_with_tesseract(image)
        else:
            raise RuntimeError(
                "No OCR engine available. Install Tesseract or configure Google Vision API."
            )

    def _ocr_with_tesseract(self, image) -> str:
        """Use Tesseract for OCR."""
        import pytesseract

        # Configure Tesseract for better COI extraction
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(image, config=custom_config)
        return text.strip()

    def _ocr_with_google_vision(self, image) -> str:
        """Use Google Cloud Vision for OCR."""
        try:
            from google.cloud import vision
        except ImportError:
            raise RuntimeError("google-cloud-vision is required for Google Vision OCR")

        if self._google_vision_client is None:
            self._google_vision_client = vision.ImageAnnotatorClient()

        # Convert PIL image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        content = img_byte_arr.getvalue()

        vision_image = vision.Image(content=content)
        response = self._google_vision_client.document_text_detection(image=vision_image)

        if response.error.message:
            raise RuntimeError(f"Google Vision API error: {response.error.message}")

        return response.full_text_annotation.text if response.full_text_annotation else ""


# Global OCR processor instance
_ocr_processor: Optional[OCRProcessor] = None


def get_ocr_processor() -> OCRProcessor:
    """Get the global OCR processor instance."""
    global _ocr_processor
    if _ocr_processor is None:
        _ocr_processor = OCRProcessor()
    return _ocr_processor
