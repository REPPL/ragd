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
    """Extract text from HTML files, stripping tags."""

    def extract(self, path: Path) -> ExtractionResult:
        """Extract text from HTML file.

        Args:
            path: Path to HTML file

        Returns:
            ExtractionResult with stripped text
        """
        try:
            with open(path, "rb") as f:
                raw_data = f.read()

            # Let BeautifulSoup handle encoding (respects meta charset)
            soup = BeautifulSoup(raw_data, "html.parser")
            detected_encoding = soup.original_encoding or "utf-8"

            # Remove script and style elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()

            # Get text with reasonable spacing
            text = soup.get_text(separator="\n", strip=True)

            # Clean up excessive whitespace
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            text = "\n".join(lines)

            return ExtractionResult(
                text=text,
                metadata={
                    "source": str(path),
                    "format": "html",
                    "encoding": detected_encoding,
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
