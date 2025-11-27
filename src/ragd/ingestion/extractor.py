"""Text extraction from various document formats.

This module provides extractors for PDF, TXT, Markdown, and HTML files.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import fitz  # PyMuPDF
from bs4 import BeautifulSoup

from ragd.utils.paths import FileType, get_file_type


@dataclass
class ExtractionResult:
    """Result of text extraction."""

    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    pages: int | None = None
    extraction_method: str = "unknown"
    success: bool = True
    error: str | None = None


class TextExtractor(Protocol):
    """Protocol for text extractors."""

    def extract(self, path: Path) -> ExtractionResult:
        """Extract text from a document.

        Args:
            path: Path to document

        Returns:
            ExtractionResult with text and metadata
        """
        ...


class PDFExtractor:
    """Extract text from PDF files using PyMuPDF."""

    def extract(self, path: Path) -> ExtractionResult:
        """Extract text from PDF.

        Args:
            path: Path to PDF file

        Returns:
            ExtractionResult with extracted text
        """
        try:
            with fitz.open(path) as doc:
                page_count = len(doc)
                text_parts = []

                for page in doc:
                    page_text = page.get_text()
                    if page_text.strip():
                        text_parts.append(page_text)

                text = "\n\n".join(text_parts)

            return ExtractionResult(
                text=text,
                metadata={
                    "source": str(path),
                    "format": "pdf",
                },
                pages=page_count,
                extraction_method="pymupdf",
            )
        except Exception as e:
            return ExtractionResult(
                text="",
                extraction_method="pymupdf",
                success=False,
                error=str(e),
            )


class PlainTextExtractor:
    """Extract text from plain text files."""

    def extract(self, path: Path) -> ExtractionResult:
        """Extract text from plain text file.

        Args:
            path: Path to text file

        Returns:
            ExtractionResult with file contents
        """
        try:
            with open(path, "rb") as f:
                raw_data = f.read()

            # Try UTF-8 first (most common), fall back to latin-1 (never fails)
            encoding = "utf-8"
            try:
                text = raw_data.decode("utf-8")
            except UnicodeDecodeError:
                text = raw_data.decode("latin-1")
                encoding = "latin-1"

            return ExtractionResult(
                text=text,
                metadata={
                    "source": str(path),
                    "format": "txt",
                    "encoding": encoding,
                },
                extraction_method="plaintext",
            )
        except Exception as e:
            return ExtractionResult(
                text="",
                extraction_method="plaintext",
                success=False,
                error=str(e),
            )


class MarkdownExtractor:
    """Extract text from Markdown files, preserving structure."""

    def extract(self, path: Path) -> ExtractionResult:
        """Extract text from Markdown file.

        Args:
            path: Path to Markdown file

        Returns:
            ExtractionResult with Markdown content
        """
        try:
            with open(path, "rb") as f:
                raw_data = f.read()

            # Try UTF-8 first (most common), fall back to latin-1 (never fails)
            encoding = "utf-8"
            try:
                text = raw_data.decode("utf-8")
            except UnicodeDecodeError:
                text = raw_data.decode("latin-1")
                encoding = "latin-1"

            return ExtractionResult(
                text=text,
                metadata={
                    "source": str(path),
                    "format": "markdown",
                    "encoding": encoding,
                },
                extraction_method="markdown",
            )
        except Exception as e:
            return ExtractionResult(
                text="",
                extraction_method="markdown",
                success=False,
                error=str(e),
            )


class HTMLExtractor:
    """Extract text from HTML files, stripping tags.

    Uses trafilatura for article extraction when available (F-051),
    falls back to BeautifulSoup with proper spacing.
    """

    def __init__(self) -> None:
        """Initialise HTML extractor."""
        self._trafilatura_available = self._check_trafilatura()

    def _check_trafilatura(self) -> bool:
        """Check if trafilatura is available."""
        try:
            import trafilatura
            return True
        except ImportError:
            return False

    def extract(self, path: Path) -> ExtractionResult:
        """Extract text from HTML file.

        Uses trafilatura for article extraction when available,
        falls back to BeautifulSoup with space separator (not newline).

        Args:
            path: Path to HTML file

        Returns:
            ExtractionResult with stripped text
        """
        try:
            with open(path, "rb") as f:
                raw_data = f.read()

            # Try to decode
            try:
                html_content = raw_data.decode("utf-8")
                encoding = "utf-8"
            except UnicodeDecodeError:
                html_content = raw_data.decode("latin-1")
                encoding = "latin-1"

            # Try trafilatura first (F-051: trafilatura-first strategy)
            if self._trafilatura_available:
                try:
                    import trafilatura

                    text = trafilatura.extract(
                        html_content,
                        include_comments=False,
                        include_tables=True,
                        no_fallback=False,
                        favor_precision=True,
                    )

                    if text and len(text) > 50:  # Reasonable content extracted
                        # Get title from HTML
                        soup = BeautifulSoup(raw_data, "html.parser")
                        title = soup.title.string if soup.title else None

                        return ExtractionResult(
                            text=text,
                            metadata={
                                "source": str(path),
                                "format": "html",
                                "encoding": encoding,
                                "title": title,
                            },
                            extraction_method="trafilatura",
                        )
                except Exception:
                    pass  # Fall through to BeautifulSoup

            # Fallback: BeautifulSoup with SPACE separator (not newline!)
            soup = BeautifulSoup(raw_data, "html.parser")

            # Remove script and style elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()

            # F-051: Use space separator, not newline
            # This prevents spurious line breaks at inline element boundaries
            text = soup.get_text(separator=" ", strip=True)

            # Normalise whitespace
            import re
            text = re.sub(r"\s+", " ", text)

            # Add paragraph breaks at block elements
            # This is a simple heuristic - trafilatura handles this better
            text = text.strip()

            return ExtractionResult(
                text=text,
                metadata={
                    "source": str(path),
                    "format": "html",
                    "encoding": soup.original_encoding or encoding,
                    "title": soup.title.string if soup.title else None,
                },
                extraction_method="beautifulsoup",
            )
        except Exception as e:
            return ExtractionResult(
                text="",
                extraction_method="beautifulsoup",
                success=False,
                error=str(e),
            )


class AdvancedHTMLExtractor:
    """Extract text from HTML with F-039 enhancements.

    This extractor provides:
    - Fast parsing with selectolax (10-100x faster than BeautifulSoup)
    - Rich metadata extraction (Open Graph, JSON-LD, Schema.org)
    - Structure preservation (tables, headings, lists as Markdown)
    - SingleFile archive detection (routes to WebArchiveProcessor)
    - Tiered processing based on complexity

    Falls back to basic HTMLExtractor if dependencies unavailable.

    Implements F-039: Advanced HTML Processing.
    """

    def __init__(
        self,
        extract_metadata: bool = True,
        preserve_structure: bool = True,
        use_trafilatura_for_complex: bool = True,
    ) -> None:
        """Initialise advanced HTML extractor.

        Args:
            extract_metadata: Extract rich metadata (OG, JSON-LD, etc.)
            preserve_structure: Preserve tables/lists as Markdown
            use_trafilatura_for_complex: Use trafilatura for complex pages
        """
        self.extract_metadata_flag = extract_metadata
        self.preserve_structure = preserve_structure
        self.use_trafilatura = use_trafilatura_for_complex

        # Check for optional dependencies
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        """Check available optional dependencies."""
        try:
            from ragd.web.parser import SELECTOLAX_AVAILABLE
            self._selectolax_available = SELECTOLAX_AVAILABLE
        except ImportError:
            self._selectolax_available = False

        try:
            from ragd.web.archive import TRAFILATURA_AVAILABLE
            self._trafilatura_available = TRAFILATURA_AVAILABLE
        except ImportError:
            self._trafilatura_available = False

    def extract(self, path: Path) -> ExtractionResult:
        """Extract text from HTML file with enhancements.

        Args:
            path: Path to HTML file

        Returns:
            ExtractionResult with extracted text and rich metadata
        """
        try:
            with open(path, "rb") as f:
                raw_data = f.read()

            # Try to decode
            try:
                html_content = raw_data.decode("utf-8")
                encoding = "utf-8"
            except UnicodeDecodeError:
                html_content = raw_data.decode("latin-1")
                encoding = "latin-1"

            # Check if this is a SingleFile archive
            from ragd.web.archive import is_singlefile_archive, WebArchiveProcessor

            if is_singlefile_archive(html_content):
                # Route to WebArchiveProcessor (F-038)
                processor = WebArchiveProcessor()
                archive_result = processor.process(path)

                return ExtractionResult(
                    text=archive_result.text,
                    metadata={
                        "source": str(path),
                        "format": "html",
                        "encoding": encoding,
                        "archive_type": "singlefile",
                        "original_url": archive_result.metadata.original_url if archive_result.metadata else None,
                        "archive_date": archive_result.metadata.archive_date.isoformat() if archive_result.metadata and archive_result.metadata.archive_date else None,
                        "title": archive_result.metadata.title if archive_result.metadata else None,
                    },
                    extraction_method="singlefile_archive",
                    success=archive_result.success,
                    error=archive_result.error,
                )

            # Use F-039 enhanced processing
            return self._extract_enhanced(html_content, path, encoding)

        except ImportError:
            # F-038/F-039 not available, fall back to basic
            return HTMLExtractor().extract(path)
        except Exception as e:
            return ExtractionResult(
                text="",
                extraction_method="advanced_html",
                success=False,
                error=str(e),
            )

    def _extract_enhanced(
        self, html_content: str, path: Path, encoding: str
    ) -> ExtractionResult:
        """Extract with F-039 enhancements.

        Args:
            html_content: HTML content string
            path: Source file path
            encoding: Detected encoding

        Returns:
            ExtractionResult with enhanced extraction
        """
        from ragd.web.parser import parse_html, ComplexityTier
        from ragd.web.metadata import extract_metadata as extract_html_metadata
        from ragd.web.structure import extract_structure, get_text_with_structure

        # Parse HTML
        parse_result = parse_html(html_content)

        # Extract rich metadata if requested
        metadata_dict: dict[str, Any] = {
            "source": str(path),
            "format": "html",
            "encoding": encoding,
            "complexity_tier": parse_result.tier.name,
            "parser_used": parse_result.parser_used,
            "parse_time_ms": parse_result.parse_time_ms,
        }

        if self.extract_metadata_flag:
            html_metadata = extract_html_metadata(html_content)
            metadata_dict.update({
                "title": html_metadata.get_best_title(),
                "description": html_metadata.get_best_description(),
                "author": html_metadata.get_best_author(),
                "language": html_metadata.language,
                "publication_date": html_metadata.get_best_date().isoformat() if html_metadata.get_best_date() else None,
                "og_type": html_metadata.og_type,
                "schema_type": html_metadata.schema_type,
                "keywords": html_metadata.keywords,
                "tags": html_metadata.tags,
                "canonical_url": html_metadata.canonical_url,
            })

        # Extract text with structure preservation if requested
        if self.preserve_structure:
            text = get_text_with_structure(html_content)
            structure = extract_structure(html_content)
            metadata_dict["structure"] = structure.to_dict()
        else:
            text = parse_result.text

        # For complex pages, optionally use trafilatura
        if (
            parse_result.tier == ComplexityTier.COMPLEX
            and self.use_trafilatura
            and self._trafilatura_available
        ):
            try:
                import trafilatura

                trafilatura_text = trafilatura.extract(
                    html_content,
                    include_tables=True,
                    include_links=True,
                )
                if trafilatura_text and len(trafilatura_text) > len(text) * 0.5:
                    # Use trafilatura text if it's reasonably complete
                    text = trafilatura_text
                    metadata_dict["extraction_enhanced"] = "trafilatura"
            except Exception:
                pass  # Keep original text

        return ExtractionResult(
            text=text,
            metadata=metadata_dict,
            extraction_method="advanced_html",
            success=True,
        )


# Extractor registry
EXTRACTORS: dict[FileType, TextExtractor] = {
    "pdf": PDFExtractor(),
    "txt": PlainTextExtractor(),
    "md": MarkdownExtractor(),
    "html": HTMLExtractor(),
}


def extract_text(path: Path) -> ExtractionResult:
    """Extract text from a file using the appropriate extractor.

    Args:
        path: Path to file

    Returns:
        ExtractionResult with extracted text

    Raises:
        ValueError: If file type is not supported
    """
    file_type = get_file_type(path)

    if file_type == "unknown":
        return ExtractionResult(
            text="",
            extraction_method="none",
            success=False,
            error=f"Unsupported file type: {path.suffix}",
        )

    extractor = EXTRACTORS.get(file_type)
    if not extractor:
        return ExtractionResult(
            text="",
            extraction_method="none",
            success=False,
            error=f"No extractor for file type: {file_type}",
        )

    return extractor.extract(path)
