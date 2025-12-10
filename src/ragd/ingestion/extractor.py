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

                # Extract PDF metadata (author, creation date, etc.)
                pdf_metadata = self._extract_pdf_metadata(doc)

            return ExtractionResult(
                text=text,
                metadata={
                    "source": str(path),
                    "format": "pdf",
                    **pdf_metadata,
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

    def _extract_pdf_metadata(self, doc: fitz.Document) -> dict[str, Any]:
        """Extract metadata from PDF document.

        Extracts author and publication year for document reference resolution.

        Args:
            doc: PyMuPDF document object

        Returns:
            Dictionary with author, publication_year, and other metadata
        """
        import re

        metadata: dict[str, Any] = {}

        try:
            pdf_meta = doc.metadata
            if not pdf_meta:
                return metadata

            # Extract author
            author = pdf_meta.get("author", "")
            if author:
                metadata["author"] = author
                # Extract first author surname for matching
                metadata["author_hint"] = self._extract_author_hint(author)

            # Extract title
            title = pdf_meta.get("title", "")
            if title:
                metadata["title"] = title

            # Extract publication year from creation date
            # Format: D:YYYYMMDDHHmmSS or D:YYYYMMDD etc.
            creation_date = pdf_meta.get("creationDate", "") or pdf_meta.get(
                "creation_date", ""
            )
            if creation_date:
                metadata["creation_date"] = creation_date
                year = self._extract_year(creation_date)
                if year:
                    metadata["publication_year"] = year

            # Also try modification date as fallback
            if "publication_year" not in metadata:
                mod_date = pdf_meta.get("modDate", "") or pdf_meta.get(
                    "modification_date", ""
                )
                if mod_date:
                    year = self._extract_year(mod_date)
                    if year:
                        metadata["publication_year"] = year

        except Exception:
            # Don't fail extraction if metadata parsing fails
            pass

        return metadata

    def _extract_author_hint(self, author: str) -> str | None:
        """Extract first author surname for matching.

        Handles various author formats:
        - "Smith, John" -> "smith"
        - "John Smith" -> "smith"
        - "Smith et al." -> "smith"
        - "John Smith and Jane Doe" -> "smith"

        Args:
            author: Author string from PDF metadata

        Returns:
            Lowercase first author surname, or None if parsing fails
        """
        import re

        if not author:
            return None

        # Clean up the string
        author = author.strip()

        # Handle "et al." by taking only what's before it
        if "et al" in author.lower():
            author = re.split(r"\s+et\s+al", author, flags=re.IGNORECASE)[0].strip()

        # Handle multiple authors (take first)
        for sep in [" and ", " & ", ";", ","]:
            if sep in author:
                author = author.split(sep)[0].strip()
                break

        # Handle "Surname, First" format
        if "," in author:
            surname = author.split(",")[0].strip()
            return surname.lower() if surname else None

        # Handle "First Surname" format - take last word
        parts = author.split()
        if parts:
            # Last word is typically surname
            return parts[-1].lower()

        return None

    def _extract_year(self, date_string: str) -> str | None:
        """Extract 4-digit year from PDF date string.

        Handles formats like:
        - D:20210315123456
        - D:2021
        - 2021-03-15

        Args:
            date_string: Date string from PDF metadata

        Returns:
            4-digit year string, or None if not found
        """
        import re

        if not date_string:
            return None

        # Look for 4-digit year (between 1900 and 2099)
        match = re.search(r"(19|20)\d{2}", date_string)
        if match:
            return match.group(0)

        return None


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
    Includes script tag mining for JavaScript-rendered content (v0.7.6).
    """

    # Minimum content length to consider extraction successful
    MIN_CONTENT_LENGTH = 20  # Lowered from 50 in v0.7.6

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

    def _extract_from_script_tags(self, soup: "BeautifulSoup") -> str:
        """Extract text content from script tags containing JSON data.

        Many modern web apps (React, Next.js, Vue) embed article content
        in script tags as JSON (e.g., __NEXT_DATA__, application/ld+json).

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            Extracted text content or empty string
        """
        import json
        import re

        extracted_text = []

        # Try to find JSON-LD structured data (Schema.org)
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                # Extract text from common fields
                for field in ["articleBody", "description", "text", "content"]:
                    if field in data and isinstance(data[field], str):
                        extracted_text.append(data[field])
            except (json.JSONDecodeError, TypeError):
                pass

        # Try to find framework-embedded state (Next.js, Nuxt, Redux, Apollo, etc.)
        framework_patterns = (
            r"__NEXT_DATA__|__NUXT__|__APP_STATE__|__APP_DATA__|"
            r"__INITIAL_STATE__|__PRELOADED_STATE__|__APOLLO_STATE__"
        )
        for script in soup.find_all("script", id=re.compile(framework_patterns)):
            try:
                data = json.loads(script.string or "")
                # Deep search for content-like fields
                content = self._find_content_in_json(data)
                if content:
                    extracted_text.append(content)
            except (json.JSONDecodeError, TypeError):
                pass

        return "\n\n".join(extracted_text)

    def _find_content_in_json(self, data: dict | list, depth: int = 0) -> str:
        """Recursively search JSON structure for article content.

        Args:
            data: JSON data structure
            depth: Current recursion depth (max 10)

        Returns:
            Extracted content or empty string
        """
        if depth > 10:
            return ""

        content_fields = {"content", "body", "text", "articleBody", "description", "markdown"}
        results = []

        if isinstance(data, dict):
            for key, value in data.items():
                if key.lower() in content_fields and isinstance(value, str) and len(value) > 100:
                    results.append(value)
                elif isinstance(value, (dict, list)):
                    nested = self._find_content_in_json(value, depth + 1)
                    if nested:
                        results.append(nested)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    nested = self._find_content_in_json(item, depth + 1)
                    if nested:
                        results.append(nested)

        return "\n\n".join(results)

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

            # Parse with BeautifulSoup for metadata and fallback
            soup = BeautifulSoup(raw_data, "html.parser")
            title = soup.title.string if soup.title else None

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

                    if text and len(text) > self.MIN_CONTENT_LENGTH:
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
                    pass  # Fall through to other methods

            # Try script tag mining (v0.7.6: for JavaScript-rendered content)
            script_text = self._extract_from_script_tags(soup)
            if script_text and len(script_text) > self.MIN_CONTENT_LENGTH:
                return ExtractionResult(
                    text=script_text,
                    metadata={
                        "source": str(path),
                        "format": "html",
                        "encoding": encoding,
                        "title": title,
                    },
                    extraction_method="script_json",
                )

            # Fallback: BeautifulSoup with SPACE separator (not newline!)
            # Create a fresh soup for text extraction (scripts not removed yet)
            soup_for_text = BeautifulSoup(raw_data, "html.parser")

            # Remove script and style elements, but be more selective with nav/footer
            for element in soup_for_text(["script", "style"]):
                element.decompose()

            # Only remove nav/footer/header if there's content in main/article tags
            main_content = soup_for_text.find(["main", "article"])
            if main_content:
                text = main_content.get_text(separator=" ", strip=True)
            else:
                # No main/article, remove nav/footer/header as fallback
                for element in soup_for_text(["nav", "footer", "header"]):
                    element.decompose()
                text = soup_for_text.get_text(separator=" ", strip=True)

            # Normalise whitespace
            import re
            text = re.sub(r"\s+", " ", text)
            text = text.strip()

            return ExtractionResult(
                text=text,
                metadata={
                    "source": str(path),
                    "format": "html",
                    "encoding": soup.original_encoding or encoding,
                    "title": title,
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
