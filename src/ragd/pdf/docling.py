"""Docling-based PDF processor for complex documents.

This module provides PDF processing using IBM's Docling library for
documents with complex layouts, tables, and multi-column content.

Docling is an optional dependency and must be installed separately:
    pip install 'ragd[pdf]'
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ragd.features import DOCLING_AVAILABLE, DependencyError
from ragd.pdf.processor import ExtractedContent, ExtractedTable

if TYPE_CHECKING:
    from docling.document_converter import DocumentConverter

logger = logging.getLogger(__name__)


class DoclingProcessor:
    """PDF processor using IBM Docling for complex layouts.

    Docling provides advanced document understanding with:
    - Layout analysis (DocLayNet model)
    - Table structure extraction (TableFormer model)
    - Multi-column detection
    - Reading order reconstruction
    - Optional OCR integration

    The processor uses lazy loading to defer model initialisation until
    first use, avoiding startup overhead when Docling isn't needed.

    Example:
        >>> processor = DoclingProcessor()
        >>> content = processor.extract(Path("complex-report.pdf"))
        >>> print(content.text)
        >>> for table in content.tables:
        ...     print(table.markdown)

    Note:
        Docling models are downloaded on first use (~1.5GB total).
        First extraction may take 2-3 minutes for model download.
    """

    def __init__(
        self,
        *,
        enable_ocr: bool = False,
        extract_tables: bool = True,
        max_pages: int | None = None,
        artifacts_path: Path | None = None,
    ) -> None:
        """Initialise the Docling processor.

        Args:
            enable_ocr: Enable OCR for scanned documents
            extract_tables: Enable table structure extraction
            max_pages: Maximum number of pages to process (None for all)
            artifacts_path: Custom path for model artifacts

        Raises:
            DependencyError: If Docling is not installed
        """
        if not DOCLING_AVAILABLE:
            raise DependencyError(
                "Docling is required for complex PDF processing.",
                feature="docling",
                install_command="pip install 'ragd[pdf]'",
            )

        self._enable_ocr = enable_ocr
        self._extract_tables = extract_tables
        self._max_pages = max_pages
        self._artifacts_path = artifacts_path
        self._converter: DocumentConverter | None = None
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    def name(self) -> str:
        """Name of this processor."""
        return "Docling"

    @property
    def supports_tables(self) -> bool:
        """Docling has excellent table support."""
        return True

    @property
    def supports_layout(self) -> bool:
        """Docling handles complex layouts."""
        return True

    def _ensure_converter(self) -> DocumentConverter:
        """Lazy load the converter on first use.

        Returns:
            Initialised DocumentConverter instance
        """
        if self._converter is None:
            self._logger.info("Initialising Docling converter (first use)...")
            start = time.perf_counter()

            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            from docling.document_converter import DocumentConverter, PdfFormatOption

            pipeline_options = PdfPipelineOptions(
                do_table_structure=self._extract_tables,
                do_ocr=self._enable_ocr,
            )

            if self._artifacts_path:
                pipeline_options.artifacts_path = str(self._artifacts_path)

            self._converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )

            elapsed = time.perf_counter() - start
            self._logger.info("Docling converter initialised in %.1fs", elapsed)

        return self._converter

    def extract(self, pdf_path: Path) -> ExtractedContent:
        """Extract text and structure from PDF using Docling.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            ExtractedContent with text, pages, tables, and metadata

        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            ValueError: If the file is not a valid PDF
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError(f"Not a PDF file: {pdf_path}")

        start_time = time.perf_counter()

        try:
            converter = self._ensure_converter()

            # Convert document
            convert_kwargs: dict[str, Any] = {}
            if self._max_pages:
                convert_kwargs["max_num_pages"] = self._max_pages

            result = converter.convert(str(pdf_path), **convert_kwargs)

            # Check conversion status
            from docling.datamodel.document import ConversionStatus

            if result.status == ConversionStatus.FAILURE:
                return ExtractedContent(
                    text="",
                    processor_name=self.name,
                    success=False,
                    error=f"Conversion failed: {result.errors}",
                )

            # Extract content
            doc = result.document
            markdown = doc.export_to_markdown()

            # Extract pages (Docling provides page-level access)
            pages: list[str] = []
            try:
                for page_num in range(len(result.pages)):
                    # Get text for this page from document elements
                    page_text = self._extract_page_text(doc, page_num)
                    pages.append(page_text)
            except Exception as e:
                self._logger.warning("Failed to extract page text: %s", e)
                pages = [markdown]  # Fallback to full text

            # Extract tables
            tables: list[ExtractedTable] = []
            if self._extract_tables:
                try:
                    for table in doc.tables:
                        tables.append(
                            ExtractedTable(
                                page_number=getattr(table, "page_no", 0),
                                table_index=len(tables),
                                markdown=table.export_to_markdown(),
                                rows=getattr(table, "num_rows", 0),
                                cols=getattr(table, "num_cols", 0),
                                confidence=1.0,
                            )
                        )
                except Exception as e:
                    self._logger.warning("Failed to extract tables: %s", e)

            # Extract metadata from PDF properties
            metadata: dict[str, Any] = {}
            try:
                if hasattr(result.input, "metadata") and result.input.metadata:
                    input_meta = result.input.metadata
                    metadata = {
                        "title": getattr(input_meta, "title", ""),
                        "author": getattr(input_meta, "author", ""),
                        "subject": getattr(input_meta, "subject", ""),
                    }
                    metadata = {k: v for k, v in metadata.items() if v}
            except Exception:
                pass

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            # Log warnings if partial success
            if result.status == ConversionStatus.PARTIAL_SUCCESS:
                for error in result.errors:
                    self._logger.warning("Conversion warning: %s", error)

            return ExtractedContent(
                text=markdown,
                pages=pages,
                tables=tables,
                metadata=metadata,
                processing_time_ms=elapsed_ms,
                processor_name=self.name,
                success=True,
            )

        except ImportError as e:
            return ExtractedContent(
                text="",
                processor_name=self.name,
                success=False,
                error=f"Docling import error: {e}",
            )
        except Exception as e:
            self._logger.exception("Docling extraction failed")
            return ExtractedContent(
                text="",
                processor_name=self.name,
                success=False,
                error=f"Extraction failed: {e}",
            )

    def _extract_page_text(self, doc: Any, page_num: int) -> str:
        """Extract text from a specific page.

        Args:
            doc: Docling document
            page_num: Page number (0-indexed)

        Returns:
            Text content for the page
        """
        page_text_parts: list[str] = []

        try:
            for element in doc.body:
                if hasattr(element, "page_no") and element.page_no == page_num:
                    if hasattr(element, "text") and element.text:
                        page_text_parts.append(element.text)
        except Exception:
            pass

        return "\n".join(page_text_parts)


def create_docling_processor(
    *,
    enable_ocr: bool = False,
    extract_tables: bool = True,
    max_pages: int | None = None,
) -> DoclingProcessor | None:
    """Create a Docling processor if available.

    Factory function that returns None if Docling is not installed,
    allowing callers to handle unavailability gracefully.

    Args:
        enable_ocr: Enable OCR for scanned documents
        extract_tables: Enable table structure extraction
        max_pages: Maximum pages to process

    Returns:
        DoclingProcessor if Docling is available, None otherwise
    """
    if not DOCLING_AVAILABLE:
        return None

    return DoclingProcessor(
        enable_ocr=enable_ocr,
        extract_tables=extract_tables,
        max_pages=max_pages,
    )
