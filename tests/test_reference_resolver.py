"""Tests for document reference resolution.

Tests the reference_resolver module that matches partial document
references (e.g., "the hummel paper") to exact filenames.
"""

from __future__ import annotations

import pytest

from ragd.chat.reference_resolver import (
    DocumentReferenceResolver,
    ResolvedReference,
    resolve_document_references,
)
from ragd.citation import Citation


class TestDocumentReferenceResolver:
    """Tests for DocumentReferenceResolver class."""

    @pytest.fixture
    def citations_with_metadata(self) -> list[Citation]:
        """Create test citations with author_hint and year metadata."""
        return [
            Citation(
                document_id="doc1",
                filename="hummel-et-al-2021-data-sovereignty-a-review.pdf",
                author="Hummel, Patrik et al.",
                author_hint="hummel",
                year="2021",
                content_preview="Data sovereignty refers to...",
            ),
            Citation(
                document_id="doc2",
                filename="smith-2020-machine-learning.pdf",
                author="Smith, John",
                author_hint="smith",
                year="2020",
                content_preview="Machine learning algorithms...",
            ),
            Citation(
                document_id="doc3",
                filename="jones-2021-ai-ethics.pdf",
                author="Jones, Mary",
                author_hint="jones",
                year="2021",
                content_preview="AI ethics considerations...",
            ),
        ]

    @pytest.fixture
    def citations_without_metadata(self) -> list[Citation]:
        """Create test citations without author_hint/year metadata."""
        return [
            Citation(
                document_id="doc1",
                filename="data-sovereignty-review.pdf",
                content_preview="Data sovereignty refers to...",
            ),
            Citation(
                document_id="doc2",
                filename="machine-learning-basics.pdf",
                content_preview="Machine learning algorithms...",
            ),
        ]

    def test_resolve_author_name(self, citations_with_metadata):
        """Test resolving 'the hummel paper' to correct filename."""
        resolver = DocumentReferenceResolver(citations_with_metadata)
        resolutions = resolver.resolve("summarise the hummel paper for me")

        assert len(resolutions) == 1
        assert resolutions[0].matched_filename == "hummel-et-al-2021-data-sovereignty-a-review.pdf"
        assert resolutions[0].confidence >= 0.7
        assert resolutions[0].match_type == "author"

    def test_resolve_author_possessive(self, citations_with_metadata):
        """Test resolving 'hummel's paper'."""
        resolver = DocumentReferenceResolver(citations_with_metadata)
        resolutions = resolver.resolve("what does hummel's paper say?")

        assert len(resolutions) == 1
        assert resolutions[0].matched_filename == "hummel-et-al-2021-data-sovereignty-a-review.pdf"

    def test_resolve_et_al(self, citations_with_metadata):
        """Test resolving 'hummel et al'."""
        resolver = DocumentReferenceResolver(citations_with_metadata)
        resolutions = resolver.resolve("according to hummel et al.")

        assert len(resolutions) == 1
        assert resolutions[0].matched_filename == "hummel-et-al-2021-data-sovereignty-a-review.pdf"

    def test_resolve_year_only(self, citations_with_metadata):
        """Test resolving 'the 2020 paper' when only one paper from that year."""
        resolver = DocumentReferenceResolver(citations_with_metadata)
        resolutions = resolver.resolve("summarise the 2020 paper")

        assert len(resolutions) == 1
        assert resolutions[0].matched_filename == "smith-2020-machine-learning.pdf"
        assert resolutions[0].match_type == "year"
        # Year-only matches have lower confidence
        assert resolutions[0].confidence < 0.8

    def test_resolve_author_and_year(self, citations_with_metadata):
        """Test resolving 'hummel 2021' with both author and year."""
        resolver = DocumentReferenceResolver(citations_with_metadata)
        resolutions = resolver.resolve("the hummel 2021 paper")

        assert len(resolutions) == 1
        assert resolutions[0].matched_filename == "hummel-et-al-2021-data-sovereignty-a-review.pdf"
        assert resolutions[0].match_type == "author+year"
        # Combined match has highest confidence
        assert resolutions[0].confidence >= 0.9

    def test_resolve_from_by_phrase(self, citations_with_metadata):
        """Test resolving 'by hummel'."""
        resolver = DocumentReferenceResolver(citations_with_metadata)
        resolutions = resolver.resolve("the research by hummel")

        assert len(resolutions) == 1
        assert resolutions[0].matched_filename == "hummel-et-al-2021-data-sovereignty-a-review.pdf"

    def test_no_match_unknown_author(self, citations_with_metadata):
        """Test that unknown authors don't match."""
        resolver = DocumentReferenceResolver(citations_with_metadata)
        resolutions = resolver.resolve("summarise the wilson paper")

        # No match or low confidence match
        assert len(resolutions) == 0 or all(r.confidence < 0.6 for r in resolutions)

    def test_multiple_citations_same_year(self, citations_with_metadata):
        """Test year-only match when multiple papers from same year."""
        # Two papers from 2021: hummel and jones
        resolver = DocumentReferenceResolver(citations_with_metadata)
        resolutions = resolver.resolve("the 2021 paper")

        # Should return matches for both, or no confident match
        # Implementation may vary - key is it doesn't falsely match wrong one
        if resolutions:
            # All matches should be from 2021
            for r in resolutions:
                assert "2021" in r.matched_filename

    def test_empty_citations(self):
        """Test resolver with no citations."""
        resolver = DocumentReferenceResolver([])
        resolutions = resolver.resolve("the hummel paper")

        assert len(resolutions) == 0

    def test_empty_query(self, citations_with_metadata):
        """Test resolver with empty query."""
        resolver = DocumentReferenceResolver(citations_with_metadata)
        resolutions = resolver.resolve("")

        assert len(resolutions) == 0

    def test_query_without_document_reference(self, citations_with_metadata):
        """Test query that doesn't reference any documents."""
        resolver = DocumentReferenceResolver(citations_with_metadata)
        # Use a query that doesn't overlap with any filename tokens
        resolutions = resolver.resolve("what is the weather today?")

        # Should have no confident matches
        assert len(resolutions) == 0 or all(r.confidence < 0.6 for r in resolutions)

    def test_fallback_filename_token_matching(self, citations_without_metadata):
        """Test fallback matching when no author_hint/year available."""
        resolver = DocumentReferenceResolver(citations_without_metadata)
        resolutions = resolver.resolve("summarise the sovereignty document")

        # Should attempt filename token matching
        if resolutions:
            assert "sovereignty" in resolutions[0].matched_filename.lower()

    def test_case_insensitive_matching(self, citations_with_metadata):
        """Test that matching is case-insensitive."""
        resolver = DocumentReferenceResolver(citations_with_metadata)

        # Test with different cases
        for query in ["the HUMMEL paper", "the Hummel Paper", "THE hummel PAPER"]:
            resolutions = resolver.resolve(query)
            assert len(resolutions) == 1
            assert resolutions[0].matched_filename == "hummel-et-al-2021-data-sovereignty-a-review.pdf"

    def test_no_duplicate_resolutions(self, citations_with_metadata):
        """Test that same document isn't resolved multiple times."""
        resolver = DocumentReferenceResolver(citations_with_metadata)
        resolutions = resolver.resolve("the hummel paper and hummel et al study")

        # Should only have one resolution for hummel, not duplicates
        hummel_matches = [r for r in resolutions if "hummel" in r.matched_filename]
        assert len(hummel_matches) <= 1


class TestConvenienceFunction:
    """Tests for the resolve_document_references convenience function."""

    def test_convenience_function(self):
        """Test the convenience function."""
        citations = [
            Citation(
                document_id="doc1",
                filename="test-paper.pdf",
                author_hint="test",
                year="2023",
            )
        ]

        resolutions = resolve_document_references("the test paper", citations)
        assert len(resolutions) == 1
        assert resolutions[0].matched_filename == "test-paper.pdf"


class TestResolvedReference:
    """Tests for ResolvedReference dataclass."""

    def test_resolved_reference_attributes(self):
        """Test ResolvedReference has expected attributes."""
        ref = ResolvedReference(
            original_text="hummel paper",
            matched_filename="hummel-2021.pdf",
            confidence=0.85,
            match_type="author",
        )

        assert ref.original_text == "hummel paper"
        assert ref.matched_filename == "hummel-2021.pdf"
        assert ref.confidence == 0.85
        assert ref.match_type == "author"


class TestPDFMetadataExtraction:
    """Tests for PDF metadata extraction in extractor."""

    def test_extract_author_hint_surname_first(self):
        """Test extracting surname from 'Surname, First' format."""
        from ragd.ingestion.extractor import PDFExtractor

        extractor = PDFExtractor()
        assert extractor._extract_author_hint("Hummel, Patrik") == "hummel"
        assert extractor._extract_author_hint("Smith, John D.") == "smith"

    def test_extract_author_hint_first_last(self):
        """Test extracting surname from 'First Last' format."""
        from ragd.ingestion.extractor import PDFExtractor

        extractor = PDFExtractor()
        assert extractor._extract_author_hint("John Smith") == "smith"
        assert extractor._extract_author_hint("Mary Jane Jones") == "jones"

    def test_extract_author_hint_et_al(self):
        """Test extracting surname from 'Author et al.' format."""
        from ragd.ingestion.extractor import PDFExtractor

        extractor = PDFExtractor()
        assert extractor._extract_author_hint("Hummel et al.") == "hummel"
        assert extractor._extract_author_hint("Smith Et Al") == "smith"

    def test_extract_author_hint_multiple_authors(self):
        """Test extracting first author from multiple authors."""
        from ragd.ingestion.extractor import PDFExtractor

        extractor = PDFExtractor()
        assert extractor._extract_author_hint("Smith, John and Jones, Mary") == "smith"
        assert extractor._extract_author_hint("John Smith & Mary Jones") == "smith"

    def test_extract_author_hint_empty(self):
        """Test handling empty/None author."""
        from ragd.ingestion.extractor import PDFExtractor

        extractor = PDFExtractor()
        assert extractor._extract_author_hint("") is None
        assert extractor._extract_author_hint(None) is None

    def test_extract_year_pdf_date_format(self):
        """Test extracting year from PDF date format."""
        from ragd.ingestion.extractor import PDFExtractor

        extractor = PDFExtractor()
        assert extractor._extract_year("D:20210315123456") == "2021"
        assert extractor._extract_year("D:2020") == "2020"

    def test_extract_year_iso_format(self):
        """Test extracting year from ISO date format."""
        from ragd.ingestion.extractor import PDFExtractor

        extractor = PDFExtractor()
        assert extractor._extract_year("2021-03-15") == "2021"
        assert extractor._extract_year("2019-12-31T23:59:59") == "2019"

    def test_extract_year_empty(self):
        """Test handling empty/None date."""
        from ragd.ingestion.extractor import PDFExtractor

        extractor = PDFExtractor()
        assert extractor._extract_year("") is None
        assert extractor._extract_year(None) is None

    def test_extract_year_invalid(self):
        """Test handling invalid date strings."""
        from ragd.ingestion.extractor import PDFExtractor

        extractor = PDFExtractor()
        assert extractor._extract_year("not a date") is None
        assert extractor._extract_year("1899") is None  # Before valid range
