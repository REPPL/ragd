"""PDF pipeline factory for intelligent processor selection.

This module provides automatic selection of the appropriate PDF processor
based on document quality assessment and available features.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

from ragd.features import DOCLING_AVAILABLE, DependencyError, get_detector
from ragd.pdf.processor import ExtractedContent, PDFProcessor, PyMuPDFProcessor
from ragd.pdf.quality import PDFQualityDetector, QualityAssessment

logger = logging.getLogger(__name__)

PipelineType = Literal["fast", "structure", "ocr", "auto"]


class PDFPipelineFactory:
    """Factory for selecting appropriate PDF processor based on document quality.

    The factory analyses PDF documents and selects the best processor:
    - fast: PyMuPDF for digital-native PDFs (default, always available)
    - structure: Docling for complex layouts (requires [pdf] extras)
    - ocr: OCR pipeline for scanned documents (requires [ocr] extras)

    Example:
        >>> factory = PDFPipelineFactory()
        >>> processor = factory.get_processor(Path("document.pdf"))
        >>> content = processor.extract(Path("document.pdf"))

        # Force specific pipeline
        >>> processor = factory.get_processor(
        ...     Path("document.pdf"),
        ...     force_pipeline="structure"
        ... )
    """

    def __init__(self) -> None:
        """Initialise the pipeline factory."""
        self._quality_detector = PDFQualityDetector()
        self._feature_detector = get_detector()
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def get_processor(
        self,
        pdf_path: Path,
        *,
        force_pipeline: PipelineType | None = None,
    ) -> PDFProcessor:
        """Get appropriate processor based on PDF quality.

        Args:
            pdf_path: Path to PDF file
            force_pipeline: Override automatic selection
                ("fast", "structure", "ocr", or None for auto)

        Returns:
            PDFProcessor instance appropriate for the document

        Raises:
            DependencyError: If required optional dependency not installed
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If file is not a valid PDF
        """
        if force_pipeline:
            return self._get_forced_processor(force_pipeline)

        # Assess document quality
        try:
            assessment = self._quality_detector.assess(pdf_path)
        except (FileNotFoundError, ValueError):
            raise
        except Exception as e:
            self._logger.warning("Quality assessment failed: %s, using fast", e)
            return PyMuPDFProcessor()

        return self._select_processor(assessment)

    def get_processor_for_assessment(
        self,
        assessment: QualityAssessment,
    ) -> PDFProcessor:
        """Get processor for a pre-computed quality assessment.

        Useful when you've already assessed the document and want to
        get the appropriate processor without re-assessing.

        Args:
            assessment: Pre-computed QualityAssessment

        Returns:
            PDFProcessor instance
        """
        return self._select_processor(assessment)

    def assess_and_extract(
        self,
        pdf_path: Path,
        *,
        force_pipeline: PipelineType | None = None,
    ) -> tuple[QualityAssessment, ExtractedContent]:
        """Assess PDF quality and extract content in one step.

        Args:
            pdf_path: Path to PDF file
            force_pipeline: Override automatic selection

        Returns:
            Tuple of (QualityAssessment, ExtractedContent)
        """
        # Get assessment
        assessment = self._quality_detector.assess(pdf_path)

        # Get processor (respecting force_pipeline)
        if force_pipeline:
            processor = self._get_forced_processor(force_pipeline)
        else:
            processor = self._select_processor(assessment)

        # Extract content
        content = processor.extract(pdf_path)

        return assessment, content

    def _select_processor(self, assessment: QualityAssessment) -> PDFProcessor:
        """Select processor based on quality assessment.

        Args:
            assessment: Document quality assessment

        Returns:
            Appropriate PDFProcessor
        """
        pipeline = assessment.recommended_pipeline

        self._logger.debug(
            "Selecting processor: quality=%s, recommended=%s",
            assessment.quality.value,
            pipeline,
        )

        if pipeline == "ocr":
            return self._get_ocr_processor(assessment)

        if pipeline == "structure":
            return self._get_structure_processor(assessment)

        # Default: fast pipeline
        return PyMuPDFProcessor()

    def _get_forced_processor(self, pipeline: PipelineType) -> PDFProcessor:
        """Get processor for forced pipeline selection.

        Args:
            pipeline: Pipeline type to use

        Returns:
            PDFProcessor for the requested pipeline

        Raises:
            DependencyError: If required dependency not available
        """
        if pipeline == "fast":
            return PyMuPDFProcessor()

        if pipeline == "structure":
            if not DOCLING_AVAILABLE:
                raise DependencyError(
                    "Docling is required for structure pipeline.",
                    feature="docling",
                    install_command="pip install 'ragd[pdf]'",
                )
            from ragd.pdf.docling import DoclingProcessor

            return DoclingProcessor(extract_tables=True)

        if pipeline == "ocr":
            if not self._feature_detector.ocr.available:
                raise DependencyError(
                    "OCR is required for scanned documents.",
                    feature="ocr",
                    install_command="pip install 'ragd[ocr]'",
                )
            # OCR processor will be implemented in v0.2.1
            # For now, fall back to Docling with OCR if available
            if DOCLING_AVAILABLE:
                from ragd.pdf.docling import DoclingProcessor

                return DoclingProcessor(enable_ocr=True, extract_tables=True)
            raise DependencyError(
                "No OCR processor available. Install Docling or OCR extras.",
                feature="ocr",
                install_command="pip install 'ragd[pdf]' or pip install 'ragd[ocr]'",
            )

        # auto or unknown - use fast
        return PyMuPDFProcessor()

    def _get_structure_processor(
        self,
        assessment: QualityAssessment,
    ) -> PDFProcessor:
        """Get processor for structure-aware extraction.

        Falls back to PyMuPDF if Docling not available.

        Args:
            assessment: Document quality assessment

        Returns:
            Structure-aware processor or fallback
        """
        if DOCLING_AVAILABLE:
            from ragd.pdf.docling import DoclingProcessor

            return DoclingProcessor(extract_tables=assessment.has_tables)

        # Graceful degradation
        self._logger.warning(
            "Docling not available for complex layout. "
            "Using PyMuPDF (table extraction may be limited). "
            "Install with: pip install 'ragd[pdf]'"
        )
        return PyMuPDFProcessor()

    def _get_ocr_processor(self, assessment: QualityAssessment) -> PDFProcessor:
        """Get processor for OCR extraction.

        Falls back to structure or fast if OCR not available.

        Args:
            assessment: Document quality assessment

        Returns:
            OCR-capable processor or fallback
        """
        # Try Docling with OCR enabled (if available)
        if DOCLING_AVAILABLE:
            from ragd.pdf.docling import DoclingProcessor

            if self._feature_detector.ocr.available:
                self._logger.info("Using Docling with OCR for scanned document")
                return DoclingProcessor(enable_ocr=True, extract_tables=True)
            else:
                self._logger.warning(
                    "OCR not available. Docling will attempt extraction "
                    "without OCR (may produce limited results for scanned pages)."
                )
                return DoclingProcessor(enable_ocr=False, extract_tables=True)

        # No Docling - check for standalone OCR
        if self._feature_detector.ocr.available:
            # OCR processor will be implemented in v0.2.1
            self._logger.warning(
                "Standalone OCR processor not yet implemented. "
                "Using PyMuPDF (limited results for scanned documents)."
            )
            return PyMuPDFProcessor()

        # No OCR available at all
        self._logger.warning(
            "No OCR capability available. "
            "Scanned document will have limited text extraction. "
            "Install with: pip install 'ragd[ocr]'"
        )
        return PyMuPDFProcessor()

    def get_available_pipelines(self) -> list[str]:
        """Get list of available pipeline types.

        Returns:
            List of available pipeline names
        """
        available = ["fast"]  # Always available

        if DOCLING_AVAILABLE:
            available.append("structure")

        if self._feature_detector.ocr.available or DOCLING_AVAILABLE:
            available.append("ocr")

        return available


# Module-level convenience function
_factory: PDFPipelineFactory | None = None


def get_factory() -> PDFPipelineFactory:
    """Get the shared pipeline factory instance.

    Returns:
        Shared PDFPipelineFactory instance
    """
    global _factory
    if _factory is None:
        _factory = PDFPipelineFactory()
    return _factory


def extract_pdf(
    pdf_path: Path,
    *,
    force_pipeline: PipelineType | None = None,
) -> ExtractedContent:
    """Extract content from PDF using automatic pipeline selection.

    Convenience function for simple extraction without managing factory.

    Args:
        pdf_path: Path to PDF file
        force_pipeline: Override automatic selection

    Returns:
        ExtractedContent from the document
    """
    factory = get_factory()
    processor = factory.get_processor(pdf_path, force_pipeline=force_pipeline)
    return processor.extract(pdf_path)
