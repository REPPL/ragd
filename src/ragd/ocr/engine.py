"""OCR engine implementations.

This module provides OCR engine implementations using:
- PaddleOCR (primary, best accuracy)
- EasyOCR (fallback, easier setup)

Both engines use lazy loading to avoid startup overhead.
"""

from __future__ import annotations

import logging
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

import fitz

from ragd.features import (
    EASYOCR_AVAILABLE,
    PADDLEOCR_AVAILABLE,
    DependencyError,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BoundingBox:
    """Bounding box for detected text."""

    x1: int
    y1: int
    x2: int
    y2: int

    @classmethod
    def from_quad(cls, quad: list[list[float]]) -> BoundingBox:
        """Create from quadrilateral coordinates [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]."""
        xs = [p[0] for p in quad]
        ys = [p[1] for p in quad]
        return cls(
            x1=int(min(xs)),
            y1=int(min(ys)),
            x2=int(max(xs)),
            y2=int(max(ys)),
        )


@dataclass
class OCRResult:
    """Single text detection result from OCR."""

    text: str
    confidence: float  # 0.0-1.0
    bbox: BoundingBox | None = None
    line_number: int | None = None
    engine: str = "unknown"

    def __str__(self) -> str:
        """Human-readable representation."""
        return f'"{self.text}" ({self.confidence:.2f})'


@dataclass
class PageOCRResult:
    """OCR results for a single page."""

    page_number: int
    results: list[OCRResult] = field(default_factory=list)
    processing_time_ms: int = 0
    engine_used: str = "unknown"

    @property
    def full_text(self) -> str:
        """Concatenated text from all results in reading order."""
        return "\n".join(r.text for r in self.results)

    @property
    def average_confidence(self) -> float:
        """Average confidence across all results."""
        if not self.results:
            return 0.0
        return sum(r.confidence for r in self.results) / len(self.results)

    @property
    def text_count(self) -> int:
        """Number of text segments detected."""
        return len(self.results)

    def __str__(self) -> str:
        """Human-readable summary."""
        return (
            f"Page {self.page_number}: {self.text_count} segments, "
            f"{self.average_confidence:.0%} avg confidence, "
            f"{self.processing_time_ms}ms"
        )


class OCREngine(Protocol):
    """Protocol for OCR engines."""

    def ocr_image(self, image_path: Path) -> list[OCRResult]:
        """Run OCR on a single image file.

        Args:
            image_path: Path to image file (PNG, JPEG, etc.)

        Returns:
            List of OCRResult objects
        """
        ...

    def ocr_pdf_page(
        self,
        pdf_path: Path,
        page_number: int,
        dpi: int = 300,
    ) -> PageOCRResult:
        """Run OCR on a single PDF page.

        Args:
            pdf_path: Path to PDF file
            page_number: Page number (0-indexed)
            dpi: Resolution for rendering (higher = better quality, slower)

        Returns:
            PageOCRResult with all detected text
        """
        ...

    @property
    def name(self) -> str:
        """Name of this OCR engine."""
        ...

    @property
    def supports_gpu(self) -> bool:
        """Whether this engine can use GPU acceleration."""
        ...


class PaddleOCREngine:
    """OCR engine using PaddleOCR.

    PaddleOCR provides high accuracy text recognition with support for
    109+ languages. Uses lazy loading to defer model initialisation.

    Example:
        >>> engine = PaddleOCREngine(lang="en")
        >>> results = engine.ocr_image(Path("scanned.png"))
        >>> for result in results:
        ...     print(f"{result.text}: {result.confidence:.2%}")
    """

    def __init__(
        self,
        *,
        lang: str = "en",
        use_gpu: bool = False,
        use_angle_cls: bool = True,
    ) -> None:
        """Initialise PaddleOCR engine.

        Args:
            lang: Language code ('en', 'ch', 'ja', etc.)
            use_gpu: Deprecated in PaddleOCR 3.x (GPU auto-detected)
            use_angle_cls: Enable text line orientation classification

        Raises:
            DependencyError: If PaddleOCR is not installed

        Note:
            PaddleOCR 3.x changed the API significantly:
            - show_log parameter removed
            - use_gpu parameter removed (auto-detection)
            - use_angle_cls renamed to use_textline_orientation
        """
        if not PADDLEOCR_AVAILABLE:
            raise DependencyError(
                "PaddleOCR is required for OCR processing.",
                feature="paddleocr",
                install_command="pip install 'ragd[ocr]'",
            )

        self._lang = lang
        self._use_gpu = use_gpu
        self._use_angle_cls = use_angle_cls
        self._ocr: Any = None
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    def name(self) -> str:
        """Name of this engine."""
        return "PaddleOCR"

    @property
    def supports_gpu(self) -> bool:
        """PaddleOCR supports GPU on Linux/Windows."""
        return True

    def _ensure_ocr(self) -> Any:
        """Lazy load PaddleOCR."""
        if self._ocr is None:
            self._logger.info("Loading PaddleOCR model (lang=%s)...", self._lang)
            start = time.perf_counter()

            import warnings

            # Suppress PaddlePaddle C++ extension ccache warning
            warnings.filterwarnings(
                "ignore",
                message=".*ccache.*",
                category=UserWarning,
            )

            # Suppress PaddleX verbose "Creating model" messages
            paddle_loggers = [
                "ppocr",
                "paddlex",
                "paddle",
                "paddle.utils.cpp_extension.extension_utils",
            ]
            for logger_name in paddle_loggers:
                logging.getLogger(logger_name).setLevel(logging.WARNING)

            from paddleocr import PaddleOCR

            # PaddleOCR 3.x API: show_log and use_gpu removed,
            # use_angle_cls renamed to use_textline_orientation
            self._ocr = PaddleOCR(
                lang=self._lang,
                use_textline_orientation=self._use_angle_cls,
            )

            elapsed = time.perf_counter() - start
            self._logger.info("PaddleOCR loaded in %.1fs", elapsed)

        return self._ocr

    def ocr_image(self, image_path: Path) -> list[OCRResult]:
        """Run OCR on an image file."""
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        ocr = self._ensure_ocr()
        # PaddleOCR 3.x: cls parameter removed (orientation set at init time)
        result = ocr.ocr(str(image_path))

        ocr_results: list[OCRResult] = []
        line_num = 0

        for page_result in result:
            if page_result is None:
                continue
            for line in page_result:
                bbox_coords = line[0]
                text = line[1][0]
                confidence = float(line[1][1])

                ocr_results.append(
                    OCRResult(
                        text=text,
                        confidence=confidence,
                        bbox=BoundingBox.from_quad(bbox_coords),
                        line_number=line_num,
                        engine=self.name,
                    )
                )
                line_num += 1

        return ocr_results

    def ocr_pdf_page(
        self,
        pdf_path: Path,
        page_number: int,
        dpi: int = 300,
    ) -> PageOCRResult:
        """Run OCR on a PDF page."""
        start_time = time.perf_counter()

        # Render page to image
        image_path = self._render_pdf_page(pdf_path, page_number, dpi)

        try:
            results = self.ocr_image(image_path)
        finally:
            # Clean up temporary image
            if image_path.exists():
                image_path.unlink()

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        return PageOCRResult(
            page_number=page_number,
            results=results,
            processing_time_ms=elapsed_ms,
            engine_used=self.name,
        )

    def _render_pdf_page(
        self,
        pdf_path: Path,
        page_number: int,
        dpi: int,
    ) -> Path:
        """Render a PDF page to a temporary image file."""
        doc = fitz.open(pdf_path)
        try:
            if page_number >= len(doc):
                raise ValueError(
                    f"Page {page_number} out of range (document has {len(doc)} pages)"
                )

            page = doc[page_number]

            # Render at specified DPI
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)

            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".png",
                delete=False,
            )
            pix.save(temp_file.name)

            return Path(temp_file.name)
        finally:
            doc.close()


class EasyOCREngine:
    """OCR engine using EasyOCR as fallback.

    EasyOCR provides simpler setup and good accuracy for scene text.
    Used as fallback when PaddleOCR fails or is unavailable.
    """

    def __init__(
        self,
        *,
        languages: list[str] | None = None,
        use_gpu: bool = False,
    ) -> None:
        """Initialise EasyOCR engine.

        Args:
            languages: List of language codes (default: ['en'])
            use_gpu: Enable GPU acceleration

        Raises:
            DependencyError: If EasyOCR is not installed
        """
        if not EASYOCR_AVAILABLE:
            raise DependencyError(
                "EasyOCR is required for OCR fallback.",
                feature="easyocr",
                install_command="pip install easyocr",
            )

        self._languages = languages or ["en"]
        self._use_gpu = use_gpu
        self._reader: Any = None
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    def name(self) -> str:
        """Name of this engine."""
        return "EasyOCR"

    @property
    def supports_gpu(self) -> bool:
        """EasyOCR supports GPU via PyTorch."""
        return True

    def _ensure_reader(self) -> Any:
        """Lazy load EasyOCR reader."""
        if self._reader is None:
            self._logger.info("Loading EasyOCR model (languages=%s)...", self._languages)
            start = time.perf_counter()

            import easyocr

            self._reader = easyocr.Reader(
                self._languages,
                gpu=self._use_gpu,
            )

            elapsed = time.perf_counter() - start
            self._logger.info("EasyOCR loaded in %.1fs", elapsed)

        return self._reader

    def ocr_image(self, image_path: Path) -> list[OCRResult]:
        """Run OCR on an image file."""
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        reader = self._ensure_reader()
        result = reader.readtext(str(image_path))

        ocr_results: list[OCRResult] = []
        for line_num, (bbox, text, confidence) in enumerate(result):
            # EasyOCR bbox is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            ocr_results.append(
                OCRResult(
                    text=text,
                    confidence=float(confidence),
                    bbox=BoundingBox.from_quad(bbox),
                    line_number=line_num,
                    engine=self.name,
                )
            )

        return ocr_results

    def ocr_pdf_page(
        self,
        pdf_path: Path,
        page_number: int,
        dpi: int = 300,
    ) -> PageOCRResult:
        """Run OCR on a PDF page."""
        start_time = time.perf_counter()

        # Render page to image
        image_path = self._render_pdf_page(pdf_path, page_number, dpi)

        try:
            results = self.ocr_image(image_path)
        finally:
            if image_path.exists():
                image_path.unlink()

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        return PageOCRResult(
            page_number=page_number,
            results=results,
            processing_time_ms=elapsed_ms,
            engine_used=self.name,
        )

    def _render_pdf_page(
        self,
        pdf_path: Path,
        page_number: int,
        dpi: int,
    ) -> Path:
        """Render a PDF page to a temporary image file."""
        doc = fitz.open(pdf_path)
        try:
            if page_number >= len(doc):
                raise ValueError(
                    f"Page {page_number} out of range (document has {len(doc)} pages)"
                )

            page = doc[page_number]
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)

            temp_file = tempfile.NamedTemporaryFile(
                suffix=".png",
                delete=False,
            )
            pix.save(temp_file.name)

            return Path(temp_file.name)
        finally:
            doc.close()


def get_available_engine() -> OCREngine | None:
    """Get the best available OCR engine.

    Returns:
        OCREngine instance (PaddleOCR preferred) or None if none available
    """
    if PADDLEOCR_AVAILABLE:
        return PaddleOCREngine()
    if EASYOCR_AVAILABLE:
        return EasyOCREngine()
    return None


def create_ocr_engine(
    engine: str = "auto",
    *,
    lang: str = "en",
    use_gpu: bool = False,
) -> OCREngine:
    """Create an OCR engine by name.

    Args:
        engine: Engine name ("auto", "paddleocr", "easyocr")
        lang: Language code
        use_gpu: Enable GPU acceleration

    Returns:
        OCREngine instance

    Raises:
        DependencyError: If requested engine not available
        ValueError: If unknown engine name
    """
    if engine == "auto":
        result = get_available_engine()
        if result is None:
            raise DependencyError(
                "No OCR engine available.",
                feature="ocr",
                install_command="pip install 'ragd[ocr]'",
            )
        return result

    if engine == "paddleocr":
        return PaddleOCREngine(lang=lang, use_gpu=use_gpu)

    if engine == "easyocr":
        return EasyOCREngine(languages=[lang], use_gpu=use_gpu)

    raise ValueError(f"Unknown OCR engine: {engine}")
