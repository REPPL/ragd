"""Citation data model for ragd.

Defines the Citation dataclass and citation styles enum.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any


class CitationStyle(str, Enum):
    """Supported citation styles."""

    APA = "apa"  # APA 7th edition
    MLA = "mla"  # MLA 9th edition
    CHICAGO = "chicago"  # Chicago Manual of Style (notes-bibliography)
    BIBTEX = "bibtex"  # BibTeX format
    INLINE = "inline"  # Simple inline format (filename:page)
    MARKDOWN = "markdown"  # Markdown link format


@dataclass
class Citation:
    """Citation metadata for a document or chunk.

    Contains all information needed to generate citations in various formats.
    """

    # Core identifiers
    document_id: str
    filename: str

    # Source location
    page_number: int | None = None
    chunk_index: int | None = None
    char_start: int | None = None
    char_end: int | None = None

    # Document metadata
    title: str | None = None
    author: str | None = None
    author_hint: str | None = None  # First author surname (lowercase) for matching
    year: str | None = None  # Publication year (4 digits)
    file_type: str | None = None
    file_path: str | None = None

    # Temporal metadata
    indexed_at: str | None = None
    accessed_date: date | None = None

    # Search context
    relevance_score: float | None = None
    content_preview: str | None = None

    # Additional metadata
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_search_result(
        cls,
        result: Any,  # SearchResult or HybridSearchResult
        accessed_date: date | None = None,
    ) -> "Citation":
        """Create Citation from a search result.

        Args:
            result: SearchResult or HybridSearchResult object
            accessed_date: Date document was accessed (defaults to today)

        Returns:
            Citation object with extracted metadata
        """
        # Handle both SearchResult and HybridSearchResult
        metadata = getattr(result, "metadata", {}) or {}
        location = getattr(result, "location", None)

        # Extract page number from location or metadata
        page_number = None
        if location and hasattr(location, "page_number"):
            page_number = location.page_number
        elif "page_number" in metadata:
            page_number = metadata["page_number"]
        elif "pages" in metadata:
            # Some extractors store pages as string "1-5"
            pages = metadata["pages"]
            if isinstance(pages, int):
                page_number = pages
            elif isinstance(pages, str) and pages:
                page_number = int(pages.split("-")[0]) if "-" in pages else int(pages)

        # Get char positions
        char_start = None
        char_end = None
        if location:
            char_start = getattr(location, "char_start", None)
            char_end = getattr(location, "char_end", None)
        char_start = char_start or metadata.get("start_char")
        char_end = char_end or metadata.get("end_char")

        # Get score
        score = getattr(result, "score", None)
        if score is None:
            score = getattr(result, "combined_score", None)

        return cls(
            document_id=getattr(result, "document_id", ""),
            filename=getattr(result, "document_name", "") or metadata.get("filename", ""),
            page_number=page_number,
            chunk_index=getattr(result, "chunk_index", None) or metadata.get("chunk_index"),
            char_start=char_start,
            char_end=char_end,
            title=metadata.get("title") or _derive_title(metadata.get("filename", "")),
            author=metadata.get("author"),
            author_hint=metadata.get("author_hint"),
            year=metadata.get("publication_year"),
            file_type=metadata.get("file_type"),
            file_path=metadata.get("source"),
            indexed_at=metadata.get("indexed_at"),
            accessed_date=accessed_date or date.today(),
            relevance_score=score,
            content_preview=_truncate(getattr(result, "content", ""), 200),
            extra=metadata,
        )

    @property
    def location_string(self) -> str:
        """Get human-readable location string."""
        parts = []
        if self.page_number:
            parts.append(f"p. {self.page_number}")
        if self.chunk_index is not None:
            parts.append(f"chunk {self.chunk_index}")
        return ", ".join(parts) if parts else ""

    @property
    def display_title(self) -> str:
        """Get display title (derived from filename if not set)."""
        return self.title or _derive_title(self.filename)


def _derive_title(filename: str) -> str:
    """Derive a title from filename.

    Args:
        filename: Document filename

    Returns:
        Human-readable title
    """
    if not filename:
        return "Untitled"

    # Remove extension
    name = Path(filename).stem

    # Replace common separators with spaces
    for sep in ["_", "-", "."]:
        name = name.replace(sep, " ")

    # Title case
    return name.title()


def _truncate(text: str, max_length: int) -> str:
    """Truncate text with ellipsis.

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        Truncated text
    """
    if not text:
        return ""
    text = " ".join(text.split())  # Normalise whitespace
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
