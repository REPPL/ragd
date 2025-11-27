"""Image extraction and processing utilities.

Provides image extraction from documents (PDFs) and basic image processing
for multi-modal RAG support.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ImageMetadata:
    """Metadata for an extracted image."""

    width: int
    height: int
    format: str  # e.g., "png", "jpeg"
    size_bytes: int
    page_number: int | None = None  # For PDF extraction
    xref: int | None = None  # PyMuPDF reference
    colorspace: str = ""
    bits_per_component: int = 8


@dataclass
class ExtractedImage:
    """An image extracted from a document."""

    data: bytes
    metadata: ImageMetadata
    document_id: str = ""
    image_id: str = ""
    source_path: str = ""
    caption: str = ""  # Optional generated caption
    embedding: list[float] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Generate image_id from content hash if not provided."""
        if not self.image_id:
            self.image_id = hashlib.sha256(self.data).hexdigest()[:16]

    @property
    def aspect_ratio(self) -> float:
        """Calculate aspect ratio (width/height)."""
        if self.metadata.height == 0:
            return 0.0
        return self.metadata.width / self.metadata.height

    @property
    def is_landscape(self) -> bool:
        """Check if image is landscape orientation."""
        return self.aspect_ratio > 1.0

    @property
    def megapixels(self) -> float:
        """Calculate megapixels."""
        return (self.metadata.width * self.metadata.height) / 1_000_000

    def to_pil_image(self) -> Any:
        """Convert to PIL Image.

        Returns:
            PIL.Image.Image object

        Raises:
            ImportError: If Pillow is not installed
        """
        import io

        from PIL import Image

        return Image.open(io.BytesIO(self.data))

    def save(self, path: Path) -> None:
        """Save image to file.

        Args:
            path: Output path
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(self.data)


def extract_images_from_pdf(
    pdf_path: Path,
    min_width: int = 100,
    min_height: int = 100,
    document_id: str = "",
) -> list[ExtractedImage]:
    """Extract images from a PDF document.

    Uses PyMuPDF (fitz) for extraction. Filters out small images
    (icons, decorations) based on minimum dimensions.

    Args:
        pdf_path: Path to PDF file
        min_width: Minimum image width in pixels
        min_height: Minimum image height in pixels
        document_id: Document ID for linking

    Returns:
        List of ExtractedImage objects

    Raises:
        ImportError: If PyMuPDF is not installed
        FileNotFoundError: If PDF file doesn't exist
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError(
            "PDF image extraction requires PyMuPDF. "
            "Install with: pip install pymupdf"
        )

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    images: list[ExtractedImage] = []
    doc = fitz.open(pdf_path)

    try:
        for page_num, page in enumerate(doc):
            image_list = page.get_images(full=True)

            for img_index, img in enumerate(image_list):
                xref = img[0]

                try:
                    base_image = doc.extract_image(xref)
                except Exception as e:
                    logger.warning(
                        "Failed to extract image xref=%d from page %d: %s",
                        xref,
                        page_num,
                        e,
                    )
                    continue

                if not base_image:
                    continue

                image_data = base_image["image"]
                image_ext = base_image.get("ext", "png")
                width = base_image.get("width", 0)
                height = base_image.get("height", 0)

                # Filter small images
                if width < min_width or height < min_height:
                    logger.debug(
                        "Skipping small image (%dx%d) on page %d",
                        width,
                        height,
                        page_num,
                    )
                    continue

                metadata = ImageMetadata(
                    width=width,
                    height=height,
                    format=image_ext,
                    size_bytes=len(image_data),
                    page_number=page_num + 1,  # 1-indexed
                    xref=xref,
                    colorspace=base_image.get("colorspace", ""),
                    bits_per_component=base_image.get("bpc", 8),
                )

                extracted = ExtractedImage(
                    data=image_data,
                    metadata=metadata,
                    document_id=document_id,
                    source_path=str(pdf_path),
                )

                images.append(extracted)

    finally:
        doc.close()

    logger.info(
        "Extracted %d images from %s (filtered by min size %dx%d)",
        len(images),
        pdf_path.name,
        min_width,
        min_height,
    )

    return images


def extract_images_from_bytes(
    pdf_bytes: bytes,
    min_width: int = 100,
    min_height: int = 100,
    document_id: str = "",
    source_name: str = "document.pdf",
) -> list[ExtractedImage]:
    """Extract images from PDF bytes.

    Args:
        pdf_bytes: PDF file content
        min_width: Minimum image width in pixels
        min_height: Minimum image height in pixels
        document_id: Document ID for linking
        source_name: Name of the source document

    Returns:
        List of ExtractedImage objects
    """
    try:
        import fitz
    except ImportError:
        raise ImportError(
            "PDF image extraction requires PyMuPDF. "
            "Install with: pip install pymupdf"
        )

    images: list[ExtractedImage] = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    try:
        for page_num, page in enumerate(doc):
            image_list = page.get_images(full=True)

            for img in image_list:
                xref = img[0]

                try:
                    base_image = doc.extract_image(xref)
                except Exception as e:
                    logger.warning(
                        "Failed to extract image xref=%d from page %d: %s",
                        xref,
                        page_num,
                        e,
                    )
                    continue

                if not base_image:
                    continue

                image_data = base_image["image"]
                image_ext = base_image.get("ext", "png")
                width = base_image.get("width", 0)
                height = base_image.get("height", 0)

                # Filter small images
                if width < min_width or height < min_height:
                    continue

                metadata = ImageMetadata(
                    width=width,
                    height=height,
                    format=image_ext,
                    size_bytes=len(image_data),
                    page_number=page_num + 1,
                    xref=xref,
                    colorspace=base_image.get("colorspace", ""),
                    bits_per_component=base_image.get("bpc", 8),
                )

                extracted = ExtractedImage(
                    data=image_data,
                    metadata=metadata,
                    document_id=document_id,
                    source_path=source_name,
                )

                images.append(extracted)

    finally:
        doc.close()

    return images


def check_image_extraction_available() -> tuple[bool, str]:
    """Check if image extraction dependencies are available.

    Returns:
        Tuple of (available: bool, message: str)
    """
    try:
        import fitz
        return True, "Image extraction is available"
    except ImportError:
        return False, (
            "Image extraction requires PyMuPDF. "
            "Install with: pip install pymupdf"
        )


def check_ocr_available() -> tuple[bool, str]:
    """Check if OCR dependencies are available.

    Returns:
        Tuple of (available: bool, message: str)
    """
    try:
        from ragd.features import PADDLEOCR_AVAILABLE, EASYOCR_AVAILABLE

        if PADDLEOCR_AVAILABLE:
            return True, "OCR is available (PaddleOCR)"
        if EASYOCR_AVAILABLE:
            return True, "OCR is available (EasyOCR)"
        return False, (
            "OCR requires PaddleOCR or EasyOCR. "
            "Install with: pip install 'ragd[ocr]'"
        )
    except ImportError:
        return False, "OCR dependencies not available"


def ocr_image_file(
    path: Path,
    *,
    engine: str = "auto",
    lang: str = "en",
    use_gpu: bool = False,
) -> tuple[str, float]:
    """Extract text from an image file using OCR.

    Args:
        path: Path to image file
        engine: OCR engine ("auto", "paddleocr", "easyocr")
        lang: Language code
        use_gpu: Enable GPU acceleration

    Returns:
        Tuple of (extracted_text, average_confidence)

    Raises:
        FileNotFoundError: If image file doesn't exist
        ImportError: If OCR dependencies not available
    """
    available, message = check_ocr_available()
    if not available:
        raise ImportError(message)

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    from ragd.ocr.engine import create_ocr_engine

    ocr = create_ocr_engine(engine, lang=lang, use_gpu=use_gpu)
    results = ocr.ocr_image(path)

    if not results:
        return "", 0.0

    # Combine all text with newlines
    text = "\n".join(r.text for r in results)
    avg_confidence = sum(r.confidence for r in results) / len(results)

    return text, avg_confidence


def ocr_image_bytes(
    data: bytes,
    format_: str = "png",
    *,
    engine: str = "auto",
    lang: str = "en",
    use_gpu: bool = False,
) -> tuple[str, float]:
    """Extract text from image bytes using OCR.

    Args:
        data: Image data as bytes
        format_: Image format (png, jpeg, etc.)
        engine: OCR engine
        lang: Language code
        use_gpu: Enable GPU acceleration

    Returns:
        Tuple of (extracted_text, average_confidence)
    """
    import tempfile

    available, message = check_ocr_available()
    if not available:
        raise ImportError(message)

    # Write to temporary file for OCR
    with tempfile.NamedTemporaryFile(
        suffix=f".{format_}",
        delete=False,
    ) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)

    try:
        return ocr_image_file(tmp_path, engine=engine, lang=lang, use_gpu=use_gpu)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def load_image_file(path: Path) -> ExtractedImage:
    """Load a standalone image file.

    Args:
        path: Path to image file

    Returns:
        ExtractedImage object

    Raises:
        FileNotFoundError: If image file doesn't exist
        ImportError: If Pillow is not installed
    """
    from PIL import Image

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    with open(path, "rb") as f:
        data = f.read()

    with Image.open(path) as img:
        width, height = img.size
        format_ = img.format or path.suffix.lstrip(".").upper()

    metadata = ImageMetadata(
        width=width,
        height=height,
        format=format_.lower(),
        size_bytes=len(data),
    )

    return ExtractedImage(
        data=data,
        metadata=metadata,
        source_path=str(path),
    )
