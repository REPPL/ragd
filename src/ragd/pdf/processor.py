"""PDF processor protocol and data models for text extraction.

This module defines the protocol for PDF processing and common data structures
used across all PDF processor implementations (PyMuPDF, Docling, OCR).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass
class ExtractedTable:
    """A table extracted from a PDF document.

    Contains the table content in Markdown format along with metadata
    about the table structure and extraction confidence.
    """

    page_number: int
    table_index: int  # 0-indexed within page
    markdown: str  # Table as Markdown
    rows: int
    cols: int
    confidence: float = 1.0

    def __str__(self) -> str:
        """Human-readable summary."""
        return f"Table[p{self.page_number}, {self.rows}x{self.cols}]"


@dataclass
class ExtractedContent:
    """Content extracted from a PDF document.

    Contains all extracted text, page-by-page content, tables, and metadata
    from the extraction process.
    """

    text: str  # Full text in reading order
    pages: list[str] = field(default_factory=list)  # Text per page
    tables: list[ExtractedTable] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)  # PDF metadata
    processing_time_ms: int = 0
    processor_name: str = "unknown"
    success: bool = True
    error: str | None = None

    @property
    def page_count(self) -> int:
        """Number of pages extracted."""
        return len(self.pages)

    @property
    def table_count(self) -> int:
        """Number of tables extracted."""
        return len(self.tables)

    def __str__(self) -> str:
        """Human-readable summary."""
        return (
            f"ExtractedContent({self.page_count} pages, "
            f"{self.table_count} tables, "
            f"{len(self.text)} chars, "
            f"{self.processing_time_ms}ms)"
        )


class PDFProcessor(Protocol):
    """Protocol for PDF text extraction processors.

    Implementations must provide text extraction from PDF files with
    optional table extraction and layout analysis capabilities.
    """

    def extract(self, pdf_path: Path) -> ExtractedContent:
        """Extract text and structure from PDF.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            ExtractedContent with extracted text, pages, tables, and metadata

        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            ValueError: If the file is not a valid PDF
        """
        ...

    @property
    def name(self) -> str:
        """Name of this processor (e.g., 'PyMuPDF', 'Docling')."""
        ...

    @property
    def supports_tables(self) -> bool:
        """Whether this processor can extract tables."""
        ...

    @property
    def supports_layout(self) -> bool:
        """Whether this processor handles complex layouts."""
        ...


class PyMuPDFProcessor:
    """Fast PDF processor using PyMuPDF.

    This processor provides fast text extraction from digital-native PDFs.
    It's the default processor for simple documents without complex layouts.

    Features:
    - Fast text extraction
    - Basic table detection heuristics
    - PDF metadata extraction
    - No external model dependencies

    Limitations:
    - Limited table structure extraction
    - No OCR capability
    - May struggle with complex multi-column layouts
    """

    def __init__(self) -> None:
        """Initialise the PyMuPDF processor."""
        import fitz  # noqa: F401 - verify import works

    @property
    def name(self) -> str:
        """Name of this processor."""
        return "PyMuPDF"

    @property
    def supports_tables(self) -> bool:
        """PyMuPDF has limited table support."""
        return False

    @property
    def supports_layout(self) -> bool:
        """PyMuPDF has basic layout support."""
        return False

    def extract(self, pdf_path: Path) -> ExtractedContent:
        """Extract text from PDF using PyMuPDF.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            ExtractedContent with extracted text and metadata
        """
        import fitz

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError(f"Not a PDF file: {pdf_path}")

        start_time = time.perf_counter()

        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            return ExtractedContent(
                text="",
                processor_name=self.name,
                success=False,
                error=f"Cannot open PDF: {e}",
            )

        try:
            pages: list[str] = []
            all_text_parts: list[str] = []
            metadata: dict[str, Any] = {}

            # Extract PDF metadata
            if doc.metadata:
                metadata = {
                    "title": doc.metadata.get("title", ""),
                    "author": doc.metadata.get("author", ""),
                    "subject": doc.metadata.get("subject", ""),
                    "keywords": doc.metadata.get("keywords", ""),
                    "creator": doc.metadata.get("creator", ""),
                    "producer": doc.metadata.get("producer", ""),
                    "creation_date": doc.metadata.get("creationDate", ""),
                    "modification_date": doc.metadata.get("modDate", ""),
                }
                # Filter empty values
                metadata = {k: v for k, v in metadata.items() if v}

            # Extract text from each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()
                pages.append(page_text)
                all_text_parts.append(page_text)

            full_text = "\n\n".join(all_text_parts)

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            return ExtractedContent(
                text=full_text,
                pages=pages,
                tables=[],  # PyMuPDF doesn't extract table structure
                metadata=metadata,
                processing_time_ms=elapsed_ms,
                processor_name=self.name,
                success=True,
            )
        finally:
            doc.close()
