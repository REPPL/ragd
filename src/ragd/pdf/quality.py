"""PDF quality detection for intelligent pipeline routing.

This module analyses PDF documents to determine the best processing pipeline:
- fast: Digital-native PDFs with good text layer (PyMuPDF)
- structure: Complex layouts with tables/multi-column (Docling)
- ocr: Scanned documents requiring OCR (PaddleOCR/EasyOCR)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Protocol

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class PDFQuality(Enum):
    """Classification of PDF quality for pipeline routing."""

    DIGITAL_NATIVE = "digital_native"  # Good text layer, simple layout
    COMPLEX_LAYOUT = "complex_layout"  # Tables, multi-column, figures
    SCANNED = "scanned"  # No text layer, needs OCR
    MIXED = "mixed"  # Some pages digital, some scanned


@dataclass(frozen=True)
class QualityAssessment:
    """Result of PDF quality analysis."""

    quality: PDFQuality
    text_coverage: float  # 0.0-1.0, percentage of pages with extractable text
    scan_probability: float  # 0.0-1.0, likelihood document is scanned
    has_tables: bool
    has_multi_column: bool
    page_count: int
    recommended_pipeline: str  # "fast", "structure", "ocr"
    confidence: float  # 0.0-1.0, confidence in assessment

    def __str__(self) -> str:
        """Human-readable summary."""
        return (
            f"Quality: {self.quality.value} | "
            f"Pipeline: {self.recommended_pipeline} | "
            f"Text coverage: {self.text_coverage:.0%} | "
            f"Scan probability: {self.scan_probability:.0%}"
        )


class PDFQualityDetectorProtocol(Protocol):
    """Protocol for PDF quality detection."""

    def assess(self, pdf_path: Path) -> QualityAssessment:
        """Analyse PDF and return quality assessment."""
        ...


class PDFQualityDetector:
    """Analyse PDF quality to determine optimal processing pipeline.

    This detector examines:
    1. Text layer presence and coverage
    2. Image density (indicator of scanned content)
    3. Layout complexity (tables, columns)
    4. Font embedding and text extraction quality

    Based on these factors, it recommends one of three pipelines:
    - fast: Use PyMuPDF directly (digital PDFs with good text)
    - structure: Use Docling for layout analysis (complex layouts)
    - ocr: Use OCR pipeline (scanned documents)
    """

    # Thresholds for classification
    TEXT_COVERAGE_THRESHOLD = 0.8  # Below this, likely scanned
    SCAN_PROBABILITY_THRESHOLD = 0.7  # Above this, likely scanned
    IMAGE_RATIO_THRESHOLD = 0.5  # Images dominating content

    def __init__(self) -> None:
        """Initialise the quality detector."""
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def assess(self, pdf_path: Path) -> QualityAssessment:
        """Analyse PDF and return quality assessment.

        Args:
            pdf_path: Path to the PDF file to analyse

        Returns:
            QualityAssessment with quality classification and recommendations

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If file is not a valid PDF
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError(f"Not a PDF file: {pdf_path}")

        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            raise ValueError(f"Cannot open PDF: {pdf_path}: {e}") from e

        try:
            return self._analyse_document(doc, pdf_path)
        finally:
            doc.close()

    def _analyse_document(self, doc: fitz.Document, pdf_path: Path) -> QualityAssessment:
        """Perform detailed analysis of the PDF document."""
        page_count = len(doc)
        if page_count == 0:
            return QualityAssessment(
                quality=PDFQuality.DIGITAL_NATIVE,
                text_coverage=0.0,
                scan_probability=0.0,
                has_tables=False,
                has_multi_column=False,
                page_count=0,
                recommended_pipeline="fast",
                confidence=1.0,
            )

        # Analyse each page
        pages_with_text = 0
        total_text_chars = 0
        total_image_area = 0
        total_page_area = 0
        table_indicators = 0
        multi_column_indicators = 0

        for page_num in range(min(page_count, 10)):  # Sample first 10 pages
            page = doc[page_num]
            page_rect = page.rect
            page_area = page_rect.width * page_rect.height
            total_page_area += page_area

            # Text analysis
            text = page.get_text()
            text_len = len(text.strip())
            if text_len > 50:  # Meaningful text threshold
                pages_with_text += 1
            total_text_chars += text_len

            # Image analysis
            image_list = page.get_images(full=True)
            for img in image_list:
                try:
                    xref = img[0]
                    img_rect = page.get_image_rects(xref)
                    for rect in img_rect:
                        img_area = rect.width * rect.height
                        total_image_area += img_area
                except Exception:
                    # Some images may not have retrievable rects
                    pass

            # Table detection heuristics
            blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
            for block in blocks:
                if block.get("type") == 0:  # Text block
                    lines = block.get("lines", [])
                    if len(lines) > 3:
                        # Check for aligned text (table indicator)
                        x_positions = [line["spans"][0]["bbox"][0] for line in lines if line.get("spans")]
                        if len(set(round(x, 0) for x in x_positions)) >= 2:
                            table_indicators += 1

            # Multi-column detection
            text_blocks = [b for b in blocks if b.get("type") == 0]
            if len(text_blocks) >= 2:
                x_centres = [
                    (b["bbox"][0] + b["bbox"][2]) / 2
                    for b in text_blocks
                    if "bbox" in b
                ]
                if len(x_centres) >= 2:
                    # Check if text blocks are in distinct columns
                    x_centres_sorted = sorted(x_centres)
                    gaps = [
                        x_centres_sorted[i + 1] - x_centres_sorted[i]
                        for i in range(len(x_centres_sorted) - 1)
                    ]
                    if gaps and max(gaps) > page_rect.width * 0.2:  # 20% gap
                        multi_column_indicators += 1

        # Calculate metrics
        sampled_pages = min(page_count, 10)
        text_coverage = pages_with_text / sampled_pages if sampled_pages > 0 else 0.0
        image_ratio = total_image_area / total_page_area if total_page_area > 0 else 0.0

        # Scan probability based on multiple factors
        scan_indicators = 0
        if text_coverage < self.TEXT_COVERAGE_THRESHOLD:
            scan_indicators += 2
        if image_ratio > self.IMAGE_RATIO_THRESHOLD:
            scan_indicators += 2
        if total_text_chars < 100 * sampled_pages:  # Very little text per page
            scan_indicators += 1
        scan_probability = min(1.0, scan_indicators / 5.0)

        # Layout complexity
        has_tables = table_indicators >= 2
        has_multi_column = multi_column_indicators >= 2

        # Determine quality and pipeline
        quality, pipeline, confidence = self._classify(
            text_coverage=text_coverage,
            scan_probability=scan_probability,
            has_tables=has_tables,
            has_multi_column=has_multi_column,
            image_ratio=image_ratio,
        )

        self._logger.debug(
            "PDF analysis: %s - quality=%s, pipeline=%s, text_coverage=%.2f, scan_prob=%.2f",
            pdf_path.name,
            quality.value,
            pipeline,
            text_coverage,
            scan_probability,
        )

        return QualityAssessment(
            quality=quality,
            text_coverage=text_coverage,
            scan_probability=scan_probability,
            has_tables=has_tables,
            has_multi_column=has_multi_column,
            page_count=page_count,
            recommended_pipeline=pipeline,
            confidence=confidence,
        )

    def _classify(
        self,
        text_coverage: float,
        scan_probability: float,
        has_tables: bool,
        has_multi_column: bool,
        image_ratio: float,
    ) -> tuple[PDFQuality, str, float]:
        """Classify PDF quality and determine pipeline.

        Returns:
            Tuple of (quality, pipeline, confidence)
        """
        # Scanned document detection
        if scan_probability >= self.SCAN_PROBABILITY_THRESHOLD:
            return PDFQuality.SCANNED, "ocr", 0.8 + (scan_probability * 0.2)

        # Mixed content (some pages scanned)
        if 0.3 < text_coverage < 0.7 and scan_probability > 0.3:
            return PDFQuality.MIXED, "ocr", 0.6 + (scan_probability * 0.2)

        # Complex layout detection
        if has_tables or has_multi_column:
            confidence = 0.7
            if has_tables:
                confidence += 0.15
            if has_multi_column:
                confidence += 0.1
            return PDFQuality.COMPLEX_LAYOUT, "structure", min(confidence, 0.95)

        # Digital native (good text, simple layout)
        if text_coverage >= self.TEXT_COVERAGE_THRESHOLD:
            confidence = 0.8 + (text_coverage * 0.2)
            return PDFQuality.DIGITAL_NATIVE, "fast", min(confidence, 0.98)

        # Default to structure pipeline for uncertain cases
        return PDFQuality.COMPLEX_LAYOUT, "structure", 0.5
