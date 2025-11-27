"""Tests for citation module (F-009).

Tests citation data models and formatters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any
from unittest.mock import MagicMock

import pytest

from ragd.citation import (
    Citation,
    CitationStyle,
    CitationFormatter,
    format_citation,
    format_citations,
    get_formatter,
)
from ragd.citation.formatter import (
    APAFormatter,
    MLAFormatter,
    ChicagoFormatter,
    BibTeXFormatter,
    InlineFormatter,
    MarkdownFormatter,
)


class TestCitation:
    """Tests for Citation dataclass."""

    def test_citation_creation(self):
        """Test creating a citation with required fields."""
        citation = Citation(
            document_id="doc123",
            filename="research.pdf",
        )
        assert citation.document_id == "doc123"
        assert citation.filename == "research.pdf"
        assert citation.page_number is None

    def test_citation_with_all_fields(self):
        """Test citation with all fields populated."""
        citation = Citation(
            document_id="doc123",
            filename="research.pdf",
            page_number=42,
            chunk_index=5,
            char_start=1000,
            char_end=2000,
            title="Research Paper",
            author="Smith, J.",
            file_type="pdf",
            file_path="/docs/research.pdf",
            indexed_at="2025-01-15T10:30:00",
            accessed_date=date(2025, 11, 27),
            relevance_score=0.95,
            content_preview="This is a preview...",
        )
        assert citation.page_number == 42
        assert citation.author == "Smith, J."
        assert citation.accessed_date == date(2025, 11, 27)

    def test_location_string_with_page(self):
        """Test location string with page number."""
        citation = Citation(
            document_id="doc123",
            filename="test.pdf",
            page_number=15,
        )
        assert "p. 15" in citation.location_string

    def test_location_string_with_chunk(self):
        """Test location string with chunk index."""
        citation = Citation(
            document_id="doc123",
            filename="test.pdf",
            chunk_index=3,
        )
        assert "chunk 3" in citation.location_string

    def test_location_string_empty(self):
        """Test location string with no location info."""
        citation = Citation(
            document_id="doc123",
            filename="test.pdf",
        )
        assert citation.location_string == ""

    def test_display_title_from_title(self):
        """Test display title uses title if set."""
        citation = Citation(
            document_id="doc123",
            filename="test.pdf",
            title="Custom Title",
        )
        assert citation.display_title == "Custom Title"

    def test_display_title_from_filename(self):
        """Test display title derived from filename."""
        citation = Citation(
            document_id="doc123",
            filename="machine_learning_guide.pdf",
        )
        assert citation.display_title == "Machine Learning Guide"


class TestCitationFromSearchResult:
    """Tests for Citation.from_search_result factory method."""

    @dataclass
    class MockSearchResult:
        """Mock search result for testing."""
        content: str = "Test content"
        score: float = 0.85
        document_id: str = "doc123"
        document_name: str = "test.pdf"
        chunk_index: int = 0
        metadata: dict[str, Any] = field(default_factory=dict)
        location: Any = None

    def test_from_search_result_basic(self):
        """Test creating citation from basic search result."""
        result = self.MockSearchResult()
        citation = Citation.from_search_result(result)

        assert citation.document_id == "doc123"
        assert citation.filename == "test.pdf"
        # chunk_index comes from metadata if not on result directly
        assert citation.relevance_score == 0.85

    def test_from_search_result_with_metadata(self):
        """Test creating citation with metadata."""
        result = self.MockSearchResult(
            metadata={
                "filename": "research.pdf",
                "file_type": "pdf",
                "source": "/path/to/research.pdf",
                "author": "John Doe",
            }
        )
        citation = Citation.from_search_result(result)

        assert citation.file_type == "pdf"
        assert citation.file_path == "/path/to/research.pdf"
        assert citation.author == "John Doe"

    def test_from_search_result_with_accessed_date(self):
        """Test creating citation with custom accessed date."""
        result = self.MockSearchResult()
        accessed = date(2025, 6, 15)
        citation = Citation.from_search_result(result, accessed_date=accessed)

        assert citation.accessed_date == accessed


class TestCitationStyle:
    """Tests for CitationStyle enum."""

    def test_all_styles_defined(self):
        """Test all expected styles are defined."""
        styles = [s.value for s in CitationStyle]
        assert "apa" in styles
        assert "mla" in styles
        assert "chicago" in styles
        assert "bibtex" in styles
        assert "inline" in styles
        assert "markdown" in styles

    def test_style_string_values(self):
        """Test style enum string values."""
        assert CitationStyle.APA.value == "apa"
        assert CitationStyle.BIBTEX.value == "bibtex"


class TestAPAFormatter:
    """Tests for APA formatter."""

    def test_basic_format(self):
        """Test basic APA formatting."""
        citation = Citation(
            document_id="doc123",
            filename="research_paper.pdf",
            indexed_at="2025-01-15T10:00:00",
        )
        formatter = APAFormatter()
        result = formatter.format(citation)

        assert "2025" in result
        assert "Research Paper" in result

    def test_format_with_author(self):
        """Test APA formatting with author."""
        citation = Citation(
            document_id="doc123",
            filename="paper.pdf",
            author="Smith, J.",
            title="Important Research",
            indexed_at="2025-01-15T10:00:00",
        )
        formatter = APAFormatter()
        result = formatter.format(citation)

        assert "Smith, J." in result
        assert "Important Research" in result

    def test_format_with_page(self):
        """Test APA formatting with page number."""
        citation = Citation(
            document_id="doc123",
            filename="paper.pdf",
            page_number=42,
        )
        formatter = APAFormatter()
        result = formatter.format(citation)

        assert "p. 42" in result


class TestMLAFormatter:
    """Tests for MLA formatter."""

    def test_basic_format(self):
        """Test basic MLA formatting."""
        citation = Citation(
            document_id="doc123",
            filename="my_document.pdf",
        )
        formatter = MLAFormatter()
        result = formatter.format(citation)

        # MLA puts period inside quotes
        assert "My Document" in result
        assert '"' in result

    def test_format_with_file_type(self):
        """Test MLA formatting includes file type."""
        citation = Citation(
            document_id="doc123",
            filename="paper.pdf",
            file_type="pdf",
        )
        formatter = MLAFormatter()
        result = formatter.format(citation)

        assert "PDF" in result


class TestChicagoFormatter:
    """Tests for Chicago formatter."""

    def test_basic_format(self):
        """Test basic Chicago formatting."""
        citation = Citation(
            document_id="doc123",
            filename="research.pdf",
        )
        formatter = ChicagoFormatter()
        result = formatter.format(citation)

        assert '"Research"' in result


class TestBibTeXFormatter:
    """Tests for BibTeX formatter."""

    def test_basic_format(self):
        """Test basic BibTeX formatting."""
        citation = Citation(
            document_id="doc123",
            filename="research.pdf",
            title="Research Paper",
        )
        formatter = BibTeXFormatter()
        result = formatter.format(citation)

        assert "@misc{" in result
        assert "title = {Research Paper}" in result
        assert "}" in result

    def test_format_with_author(self):
        """Test BibTeX with author."""
        citation = Citation(
            document_id="doc123",
            filename="paper.pdf",
            author="Smith, John",
        )
        formatter = BibTeXFormatter()
        result = formatter.format(citation)

        assert "author = {Smith, John}" in result

    def test_format_with_year(self):
        """Test BibTeX extracts year."""
        citation = Citation(
            document_id="doc123",
            filename="paper.pdf",
            indexed_at="2025-01-15T10:00:00",
        )
        formatter = BibTeXFormatter()
        result = formatter.format(citation)

        assert "year = {2025}" in result


class TestInlineFormatter:
    """Tests for inline formatter."""

    def test_basic_format(self):
        """Test basic inline formatting."""
        citation = Citation(
            document_id="doc123",
            filename="document.pdf",
        )
        formatter = InlineFormatter()
        result = formatter.format(citation)

        assert "(document.pdf)" in result

    def test_format_with_page(self):
        """Test inline with page."""
        citation = Citation(
            document_id="doc123",
            filename="doc.pdf",
            page_number=5,
        )
        formatter = InlineFormatter()
        result = formatter.format(citation)

        assert "(doc.pdf, p. 5)" in result

    def test_format_with_chunk(self):
        """Test inline with chunk index."""
        citation = Citation(
            document_id="doc123",
            filename="doc.pdf",
            chunk_index=3,
        )
        formatter = InlineFormatter()
        result = formatter.format(citation)

        assert "chunk 3" in result


class TestMarkdownFormatter:
    """Tests for markdown formatter."""

    def test_basic_format(self):
        """Test basic markdown formatting."""
        citation = Citation(
            document_id="doc123",
            filename="document.pdf",
            file_path="/path/to/document.pdf",
        )
        formatter = MarkdownFormatter()
        result = formatter.format(citation)

        assert "[Document]" in result
        assert "(/path/to/document.pdf)" in result

    def test_format_with_page(self):
        """Test markdown with page."""
        citation = Citation(
            document_id="doc123",
            filename="doc.pdf",
            file_path="/doc.pdf",
            page_number=10,
        )
        formatter = MarkdownFormatter()
        result = formatter.format(citation)

        assert "p. 10" in result


class TestGetFormatter:
    """Tests for get_formatter function."""

    def test_get_apa_formatter(self):
        """Test getting APA formatter."""
        formatter = get_formatter(CitationStyle.APA)
        assert isinstance(formatter, APAFormatter)

    def test_get_formatter_by_string(self):
        """Test getting formatter by string name."""
        formatter = get_formatter("bibtex")
        assert isinstance(formatter, BibTeXFormatter)

    def test_invalid_style_raises(self):
        """Test invalid style raises ValueError."""
        with pytest.raises(ValueError):
            get_formatter("invalid_style")


class TestFormatCitation:
    """Tests for format_citation function."""

    def test_format_citation_default(self):
        """Test format_citation with default style."""
        citation = Citation(
            document_id="doc123",
            filename="test.pdf",
        )
        result = format_citation(citation)
        assert "(test.pdf)" in result

    def test_format_citation_apa(self):
        """Test format_citation with APA style."""
        citation = Citation(
            document_id="doc123",
            filename="paper.pdf",
            indexed_at="2025-01-01T00:00:00",
        )
        result = format_citation(citation, CitationStyle.APA)
        assert "2025" in result


class TestFormatCitations:
    """Tests for format_citations function."""

    def test_format_multiple_citations(self):
        """Test formatting multiple citations."""
        citations = [
            Citation(document_id="doc1", filename="paper1.pdf"),
            Citation(document_id="doc2", filename="paper2.pdf"),
        ]
        results = format_citations(citations, CitationStyle.INLINE)

        assert len(results) == 2
        assert "paper1.pdf" in results[0]
        assert "paper2.pdf" in results[1]

    def test_format_empty_list(self):
        """Test formatting empty list."""
        results = format_citations([], CitationStyle.APA)
        assert results == []
