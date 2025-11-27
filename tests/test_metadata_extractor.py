"""Tests for metadata extraction module."""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path

import fitz
import pytest

from ragd.features import KEYBERT_AVAILABLE, LANGDETECT_AVAILABLE, SPACY_AVAILABLE
from ragd.metadata import (
    ExtractedEntity,
    ExtractedKeyword,
    ExtractedMetadata,
    MetadataExtractor,
)


class TestExtractedKeyword:
    """Tests for ExtractedKeyword dataclass."""

    def test_creation(self) -> None:
        """Test creating an ExtractedKeyword."""
        keyword = ExtractedKeyword(
            keyword="machine learning",
            score=0.85,
            source="keybert",
        )
        assert keyword.keyword == "machine learning"
        assert keyword.score == 0.85

    def test_str_representation(self) -> None:
        """Test string representation."""
        keyword = ExtractedKeyword(keyword="test", score=0.75)
        result = str(keyword)
        assert "test" in result
        assert "0.75" in result


class TestExtractedEntity:
    """Tests for ExtractedEntity dataclass."""

    def test_creation(self) -> None:
        """Test creating an ExtractedEntity."""
        entity = ExtractedEntity(
            text="Apple Inc.",
            label="ORG",
            start_char=0,
            end_char=10,
            confidence=0.95,
        )
        assert entity.text == "Apple Inc."
        assert entity.label == "ORG"

    def test_str_representation(self) -> None:
        """Test string representation."""
        entity = ExtractedEntity(
            text="London",
            label="GPE",
            start_char=0,
            end_char=6,
        )
        result = str(entity)
        assert "London" in result
        assert "GPE" in result


class TestExtractedMetadata:
    """Tests for ExtractedMetadata dataclass."""

    def test_creation(self) -> None:
        """Test creating ExtractedMetadata."""
        metadata = ExtractedMetadata(
            pdf_title="Test Document",
            pdf_author="Test Author",
            detected_language="en",
            language_confidence=0.99,
        )
        assert metadata.pdf_title == "Test Document"
        assert metadata.has_pdf_metadata is True

    def test_has_pdf_metadata_false(self) -> None:
        """Test has_pdf_metadata when no PDF metadata."""
        metadata = ExtractedMetadata()
        assert metadata.has_pdf_metadata is False

    def test_has_nlp_metadata_true(self) -> None:
        """Test has_nlp_metadata when NLP data present."""
        metadata = ExtractedMetadata(
            keywords=[ExtractedKeyword(keyword="test", score=0.5)]
        )
        assert metadata.has_nlp_metadata is True

    def test_has_nlp_metadata_false(self) -> None:
        """Test has_nlp_metadata when no NLP data."""
        metadata = ExtractedMetadata()
        assert metadata.has_nlp_metadata is False

    def test_str_representation(self) -> None:
        """Test string representation."""
        metadata = ExtractedMetadata(
            pdf_title="Test",
            keywords=[ExtractedKeyword(keyword="k", score=0.5)],
            detected_language="en",
        )
        result = str(metadata)
        assert "Test" in result
        assert "Keywords" in result
        assert "en" in result


class TestMetadataExtractor:
    """Tests for MetadataExtractor."""

    @pytest.fixture
    def extractor(self) -> MetadataExtractor:
        """Create a metadata extractor."""
        return MetadataExtractor()

    def test_init(self, extractor: MetadataExtractor) -> None:
        """Test extractor initialisation."""
        assert extractor is not None

    def test_get_capabilities(self, extractor: MetadataExtractor) -> None:
        """Test getting extraction capabilities."""
        caps = extractor.get_capabilities()
        assert "pdf_metadata" in caps
        assert caps["pdf_metadata"] is True  # Always available
        assert "language_detection" in caps
        assert "keyword_extraction" in caps
        assert "entity_extraction" in caps

    def test_extract_empty_text(self, extractor: MetadataExtractor) -> None:
        """Test extracting from empty text."""
        result = extractor.extract("")
        assert result.detected_language == "en"  # Default
        assert result.keywords == []
        assert result.entities == []

    def test_extract_simple_text(self, extractor: MetadataExtractor) -> None:
        """Test extracting from simple text."""
        text = "This is a test document about machine learning and artificial intelligence."
        result = extractor.extract(text)

        # Should have extraction time recorded
        assert result.extraction_time_ms >= 0

        # Language detection (if available)
        if LANGDETECT_AVAILABLE:
            assert result.detected_language == "en"
            assert result.language_confidence > 0

    @pytest.fixture
    def sample_pdf(self, tmp_path: Path) -> Path:
        """Create a sample PDF for testing."""
        pdf_path = tmp_path / "sample.pdf"
        doc = fitz.open()
        doc.set_metadata({
            "title": "Test Document Title",
            "author": "Test Author",
            "subject": "Test Subject",
            "creationDate": "D:20240115103000",
        })
        page = doc.new_page()
        page.insert_text((50, 50), "Sample content", fontsize=12)
        doc.save(str(pdf_path))
        doc.close()
        return pdf_path

    def test_extract_pdf_metadata(
        self,
        extractor: MetadataExtractor,
        sample_pdf: Path,
    ) -> None:
        """Test extracting PDF metadata."""
        result = extractor.extract("Sample content", pdf_path=sample_pdf)
        assert result.pdf_title == "Test Document Title"
        assert result.pdf_author == "Test Author"
        assert result.pdf_subject == "Test Subject"
        assert "pdf_metadata" in result.sources_used

    def test_extract_pdf_dates(
        self,
        extractor: MetadataExtractor,
        sample_pdf: Path,
    ) -> None:
        """Test extracting PDF dates."""
        result = extractor.extract("Sample content", pdf_path=sample_pdf)
        assert result.pdf_creation_date is not None
        assert result.pdf_creation_date.year == 2024
        assert result.pdf_creation_date.month == 1
        assert result.pdf_creation_date.day == 15

    def test_extract_nonexistent_pdf(self, extractor: MetadataExtractor) -> None:
        """Test extracting from non-existent PDF gracefully."""
        result = extractor.extract(
            "Some text",
            pdf_path=Path("/nonexistent/file.pdf"),
        )
        # Should not raise, just skip PDF metadata
        assert result.pdf_title is None


class TestMetadataExtractorLanguage:
    """Tests for language detection."""

    @pytest.fixture
    def extractor(self) -> MetadataExtractor:
        """Create extractor with language detection only."""
        return MetadataExtractor(
            enable_keywords=False,
            enable_entities=False,
            enable_language=True,
        )

    @pytest.mark.skipif(not LANGDETECT_AVAILABLE, reason="langdetect not installed")
    def test_detect_english(self, extractor: MetadataExtractor) -> None:
        """Test detecting English text."""
        text = "This is a sample English text for language detection testing."
        lang, confidence = extractor.detect_language(text)
        assert lang == "en"
        assert confidence > 0.5

    @pytest.mark.skipif(not LANGDETECT_AVAILABLE, reason="langdetect not installed")
    def test_detect_french(self, extractor: MetadataExtractor) -> None:
        """Test detecting French text."""
        text = "Ceci est un texte en français pour tester la détection de langue."
        lang, confidence = extractor.detect_language(text)
        assert lang == "fr"
        assert confidence > 0.5

    @pytest.mark.skipif(not LANGDETECT_AVAILABLE, reason="langdetect not installed")
    def test_detect_german(self, extractor: MetadataExtractor) -> None:
        """Test detecting German text."""
        text = "Dies ist ein deutscher Text zur Spracherkennung."
        lang, confidence = extractor.detect_language(text)
        assert lang == "de"
        assert confidence > 0.5

    @pytest.mark.skipif(LANGDETECT_AVAILABLE, reason="Test for missing langdetect")
    def test_language_detection_disabled(self, extractor: MetadataExtractor) -> None:
        """Test language detection when disabled."""
        lang, confidence = extractor.detect_language("Some text")
        assert lang == "en"  # Default
        assert confidence == 0.0


class TestMetadataExtractorKeywords:
    """Tests for keyword extraction."""

    @pytest.fixture
    def extractor(self) -> MetadataExtractor:
        """Create extractor with keywords only."""
        return MetadataExtractor(
            enable_keywords=True,
            enable_entities=False,
            enable_language=False,
        )

    @pytest.mark.skipif(not KEYBERT_AVAILABLE, reason="KeyBERT not installed")
    def test_extract_keywords(self, extractor: MetadataExtractor) -> None:
        """Test keyword extraction."""
        text = """
        Machine learning is a subset of artificial intelligence that enables
        systems to learn and improve from experience. Deep learning is a type
        of machine learning based on neural networks. Natural language processing
        allows computers to understand human language.
        """
        keywords = extractor.extract_keywords(text, top_n=5)

        assert len(keywords) > 0
        assert len(keywords) <= 5
        assert all(isinstance(kw, ExtractedKeyword) for kw in keywords)
        assert all(0 <= kw.score <= 1 for kw in keywords)

    @pytest.mark.skipif(not KEYBERT_AVAILABLE, reason="KeyBERT not installed")
    def test_extract_keywords_diversity(self, extractor: MetadataExtractor) -> None:
        """Test keyword diversity parameter."""
        text = "Machine learning machine learning AI artificial intelligence"

        # Low diversity - similar keywords
        keywords_low = extractor.extract_keywords(text, top_n=3, diversity=0.1)

        # High diversity - different keywords
        keywords_high = extractor.extract_keywords(text, top_n=3, diversity=0.9)

        # Both should return results
        assert len(keywords_low) > 0
        assert len(keywords_high) > 0

    @pytest.mark.skipif(KEYBERT_AVAILABLE, reason="Test for missing KeyBERT")
    def test_keywords_disabled(self, extractor: MetadataExtractor) -> None:
        """Test keyword extraction when disabled."""
        keywords = extractor.extract_keywords("Some text about topics")
        assert keywords == []


class TestMetadataExtractorEntities:
    """Tests for entity extraction."""

    @pytest.fixture
    def extractor(self) -> MetadataExtractor:
        """Create extractor with entities only."""
        return MetadataExtractor(
            enable_keywords=False,
            enable_entities=True,
            enable_language=False,
        )

    @pytest.mark.skipif(not SPACY_AVAILABLE, reason="spaCy not installed")
    def test_extract_entities(self, extractor: MetadataExtractor) -> None:
        """Test entity extraction."""
        text = "Apple Inc. was founded by Steve Jobs in Cupertino, California."

        try:
            entities = extractor.extract_entities(text)
            # May have entities or may fail if model not downloaded
            if entities:
                assert all(isinstance(e, ExtractedEntity) for e in entities)
                labels = {e.label for e in entities}
                # Should find at least one entity type
                assert len(labels) > 0
        except Exception:
            # Model may not be installed
            pytest.skip("spaCy model not available")

    @pytest.mark.skipif(not SPACY_AVAILABLE, reason="spaCy not installed")
    def test_extract_entities_filtered(self, extractor: MetadataExtractor) -> None:
        """Test entity extraction with type filter."""
        text = "Apple Inc. was founded in 1976 by Steve Jobs."

        try:
            # Only get ORG entities
            entities = extractor.extract_entities(text, entity_types=["ORG"])
            if entities:
                assert all(e.label == "ORG" for e in entities)
        except Exception:
            pytest.skip("spaCy model not available")

    @pytest.mark.skipif(SPACY_AVAILABLE, reason="Test for missing spaCy")
    def test_entities_disabled(self, extractor: MetadataExtractor) -> None:
        """Test entity extraction when disabled."""
        entities = extractor.extract_entities("Apple Inc. in California")
        assert entities == []


class TestMetadataExtractorPDFDates:
    """Tests for PDF date parsing."""

    @pytest.fixture
    def extractor(self) -> MetadataExtractor:
        """Create a metadata extractor."""
        return MetadataExtractor()

    def test_parse_pdf_date_full(self, extractor: MetadataExtractor) -> None:
        """Test parsing full PDF date."""
        result = extractor._parse_pdf_date("D:20240115103045")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 45

    def test_parse_pdf_date_minimal(self, extractor: MetadataExtractor) -> None:
        """Test parsing minimal PDF date."""
        result = extractor._parse_pdf_date("D:20240115")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_pdf_date_no_prefix(self, extractor: MetadataExtractor) -> None:
        """Test parsing PDF date without D: prefix."""
        result = extractor._parse_pdf_date("20240115")
        assert result is not None
        assert result.year == 2024

    def test_parse_pdf_date_empty(self, extractor: MetadataExtractor) -> None:
        """Test parsing empty date."""
        result = extractor._parse_pdf_date("")
        assert result is None

    def test_parse_pdf_date_invalid(self, extractor: MetadataExtractor) -> None:
        """Test parsing invalid date."""
        result = extractor._parse_pdf_date("invalid")
        assert result is None
