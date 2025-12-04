"""OCR pipeline with automatic fallback.

This module provides a high-level OCR pipeline that:
- Uses PaddleOCR as primary engine
- Falls back to EasyOCR on failure
- Processes entire PDFs page by page
- Provides confidence-based quality assessment
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import fitz

from ragd.features import EASYOCR_AVAILABLE, PADDLEOCR_AVAILABLE, DependencyError
from ragd.ocr.engine import (
    EasyOCREngine,
    OCREngine,
    OCRResult,
    PageOCRResult,
    PaddleOCREngine,
)

logger = logging.getLogger(__name__)


@dataclass
class OCRConfig:
    """Configuration for OCR processing."""

    min_confidence: float = 0.3  # Minimum confidence threshold
    use_gpu: bool = False  # Enable GPU acceleration
    language: str = "en"  # OCR language
    fallback_enabled: bool = True  # Use fallback engine if primary fails
    dpi: int = 300  # Resolution for PDF rendering


@dataclass
class DocumentOCRResult:
    """OCR results for an entire document."""

    pages: list[PageOCRResult] = field(default_factory=list)
    total_processing_time_ms: int = 0
    primary_engine: str = ""
    fallback_used: bool = False
    fallback_pages: list[int] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        """Concatenated text from all pages."""
        return "\n\n".join(page.full_text for page in self.pages)

    @property
    def average_confidence(self) -> float:
        """Average confidence across all pages."""
        if not self.pages:
            return 0.0
        confidences = [p.average_confidence for p in self.pages if p.results]
        return sum(confidences) / len(confidences) if confidences else 0.0

    @property
    def page_count(self) -> int:
        """Number of pages processed."""
        return len(self.pages)

    def get_quality_assessment(self) -> str:
        """Assess overall OCR quality."""
        conf = self.average_confidence
        if conf >= 0.9:
            return "excellent"
        elif conf >= 0.7:
            return "good"
        elif conf >= 0.5:
            return "fair - some text may be incorrect"
        else:
            return "poor - results may be unreliable"

    def __str__(self) -> str:
        """Human-readable summary."""
        return (
            f"DocumentOCRResult({self.page_count} pages, "
            f"{self.average_confidence:.0%} confidence, "
            f"quality: {self.get_quality_assessment()})"
        )


class OCRPipeline:
    """OCR pipeline with automatic fallback.

    Processes PDF documents using OCR with intelligent fallback:
    1. Try PaddleOCR (primary, best accuracy)
    2. If PaddleOCR fails or returns low confidence, try EasyOCR
    3. Return best available results

    Example:
        >>> pipeline = OCRPipeline()
        >>> result = pipeline.process_pdf(Path("scanned.pdf"))
        >>> print(result.full_text)
        >>> print(f"Quality: {result.get_quality_assessment()}")

        # Process with streaming
        >>> for page_result in pipeline.process_pdf_streaming(Path("large.pdf")):
        ...     print(f"Page {page_result.page_number}: {page_result.text_count} segments")
    """

    def __init__(self, config: OCRConfig | None = None) -> None:
        """Initialise the OCR pipeline.

        Args:
            config: OCR configuration (uses defaults if None)

        Raises:
            DependencyError: If no OCR engine is available
        """
        self._config = config or OCRConfig()
        self._primary: OCREngine | None = None
        self._fallback: OCREngine | None = None
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Verify at least one engine is available
        if not PADDLEOCR_AVAILABLE and not EASYOCR_AVAILABLE:
            raise DependencyError(
                "No OCR engine available. Install PaddleOCR or EasyOCR.",
                feature="ocr",
                install_command="pip install 'ragd[ocr]'",
            )

    @property
    def primary_engine(self) -> str:
        """Name of primary OCR engine."""
        if PADDLEOCR_AVAILABLE:
            return "PaddleOCR"
        if EASYOCR_AVAILABLE:
            return "EasyOCR"
        return "none"

    @property
    def fallback_engine(self) -> str | None:
        """Name of fallback engine, if configured."""
        if not self._config.fallback_enabled:
            return None
        if PADDLEOCR_AVAILABLE and EASYOCR_AVAILABLE:
            return "EasyOCR"
        return None

    def _get_primary(self) -> OCREngine:
        """Get primary OCR engine (lazy loaded)."""
        if self._primary is None:
            if PADDLEOCR_AVAILABLE:
                self._primary = PaddleOCREngine(
                    lang=self._config.language,
                    use_gpu=self._config.use_gpu,
                )
            elif EASYOCR_AVAILABLE:
                self._primary = EasyOCREngine(
                    languages=[self._config.language],
                    use_gpu=self._config.use_gpu,
                )
            else:
                raise DependencyError(
                    "No OCR engine available.",
                    feature="ocr",
                    install_command="pip install 'ragd[ocr]'",
                )
        return self._primary

    def _get_fallback(self) -> OCREngine | None:
        """Get fallback OCR engine (lazy loaded)."""
        if not self._config.fallback_enabled:
            return None

        if self._fallback is None:
            # Only use EasyOCR as fallback if PaddleOCR is primary
            if PADDLEOCR_AVAILABLE and EASYOCR_AVAILABLE:
                self._fallback = EasyOCREngine(
                    languages=[self._config.language],
                    use_gpu=self._config.use_gpu,
                )
        return self._fallback

    def process_pdf(
        self,
        pdf_path: Path,
        max_pages: int | None = None,
    ) -> DocumentOCRResult:
        """Process entire PDF with OCR.

        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum pages to process (None for all)

        Returns:
            DocumentOCRResult with all pages
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        start_time = time.perf_counter()

        doc = fitz.open(pdf_path)
        page_count = min(len(doc), max_pages) if max_pages else len(doc)
        doc.close()

        pages: list[PageOCRResult] = []
        fallback_pages: list[int] = []
        fallback_used = False

        for page_num in range(page_count):
            page_result, used_fallback = self._process_page(pdf_path, page_num)
            pages.append(page_result)

            if used_fallback:
                fallback_used = True
                fallback_pages.append(page_num)

        total_time = int((time.perf_counter() - start_time) * 1000)

        return DocumentOCRResult(
            pages=pages,
            total_processing_time_ms=total_time,
            primary_engine=self.primary_engine,
            fallback_used=fallback_used,
            fallback_pages=fallback_pages,
        )

    def process_pdf_streaming(
        self,
        pdf_path: Path,
        max_pages: int | None = None,
    ) -> Iterator[PageOCRResult]:
        """Process PDF with OCR, yielding results page by page.

        Useful for large documents where you want to process results
        incrementally without waiting for the entire document.

        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum pages to process (None for all)

        Yields:
            PageOCRResult for each page
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        doc = fitz.open(pdf_path)
        page_count = min(len(doc), max_pages) if max_pages else len(doc)
        doc.close()

        for page_num in range(page_count):
            page_result, _ = self._process_page(pdf_path, page_num)
            yield page_result

    def process_page(
        self,
        pdf_path: Path,
        page_number: int,
    ) -> PageOCRResult:
        """Process a single PDF page with OCR.

        Args:
            pdf_path: Path to PDF file
            page_number: Page number (0-indexed)

        Returns:
            PageOCRResult for the page
        """
        result, _ = self._process_page(pdf_path, page_number)
        return result

    def _process_page(
        self,
        pdf_path: Path,
        page_number: int,
    ) -> tuple[PageOCRResult, bool]:
        """Process a single page, using fallback if needed.

        Returns:
            Tuple of (PageOCRResult, used_fallback)
        """
        used_fallback = False

        # Try primary engine
        try:
            primary = self._get_primary()
            result = primary.ocr_pdf_page(
                pdf_path,
                page_number,
                dpi=self._config.dpi,
            )

            # Check if quality is acceptable
            if result.average_confidence >= self._config.min_confidence:
                return result, False

            self._logger.warning(
                "%s page %d: low confidence (%.2f), trying fallback",
                pdf_path.name,
                page_number,
                result.average_confidence,
            )

        except Exception as e:
            self._logger.warning(
                "%s page %d: primary OCR failed (%s), trying fallback",
                pdf_path.name,
                page_number,
                e,
            )
            result = PageOCRResult(page_number=page_number, engine_used="failed")

        # Try fallback engine
        fallback = self._get_fallback()
        if fallback is not None:
            try:
                fallback_result = fallback.ocr_pdf_page(
                    pdf_path,
                    page_number,
                    dpi=self._config.dpi,
                )

                # Use fallback if better or primary failed
                if (
                    fallback_result.average_confidence > result.average_confidence
                    or not result.results
                ):
                    return fallback_result, True

            except Exception as e:
                self._logger.warning(
                    "Page %d: fallback OCR also failed: %s",
                    page_number,
                    e,
                )

        return result, used_fallback

    def get_available_engines(self) -> list[str]:
        """Get list of available OCR engines.

        Returns:
            List of available engine names
        """
        engines = []
        if PADDLEOCR_AVAILABLE:
            engines.append("PaddleOCR")
        if EASYOCR_AVAILABLE:
            engines.append("EasyOCR")
        return engines


def filter_by_confidence(
    results: list[OCRResult],
    min_confidence: float = 0.5,
) -> list[OCRResult]:
    """Filter OCR results by confidence threshold.

    Args:
        results: List of OCR results
        min_confidence: Minimum confidence to keep

    Returns:
        Filtered list of OCR results
    """
    return [r for r in results if r.confidence >= min_confidence]


def calculate_weighted_confidence(results: list[OCRResult]) -> float:
    """Calculate text-length-weighted confidence score.

    Longer text segments are weighted more heavily since they're
    typically more reliable indicators of OCR quality.

    Args:
        results: List of OCR results

    Returns:
        Weighted confidence score (0.0-1.0)
    """
    if not results:
        return 0.0

    total_weight = sum(len(r.text) for r in results)
    if total_weight == 0:
        return 0.0

    weighted_sum = sum(r.confidence * len(r.text) for r in results)
    return weighted_sum / total_weight
