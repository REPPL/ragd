"""Tests for citation validation system.

Tests the citation extraction and validation modules that detect
potential hallucinations in LLM responses.
"""

from __future__ import annotations

import pytest

from ragd.citation import Citation
from ragd.citation.extractor import (
    ExtractedCitation,
    extract_citation_markers,
    get_used_citation_indices,
)
from ragd.citation.validator import (
    CitationValidation,
    CitationValidator,
    ValidationMode,
    ValidationReport,
    ValidationResult,
    validate_citations,
)


class TestCitationExtraction:
    """Tests for citation marker extraction."""

    def test_single_citation(self):
        """Test extracting single citation marker."""
        text = "Data sovereignty is important [1]."
        extracted = extract_citation_markers(text)
        assert len(extracted) == 1
        assert extracted[0].marker_text == "[1]"
        assert extracted[0].citation_indices == [1]

    def test_multiple_single_citations(self):
        """Test extracting multiple single citation markers."""
        text = "First claim [1]. Second claim [2]. Third claim [3]."
        extracted = extract_citation_markers(text)
        assert len(extracted) == 3
        assert extracted[0].citation_indices == [1]
        assert extracted[1].citation_indices == [2]
        assert extracted[2].citation_indices == [3]

    def test_multi_source_citation(self):
        """Test extracting multi-source citation [1;2]."""
        text = "This is supported by multiple studies [1;2;3]."
        extracted = extract_citation_markers(text)
        assert len(extracted) == 1
        assert extracted[0].marker_text == "[1;2;3]"
        assert extracted[0].citation_indices == [1, 2, 3]

    def test_adjacent_citations(self):
        """Test adjacent citation markers [1][2]."""
        text = "Studies agree [1][2] on this point."
        extracted = extract_citation_markers(text)
        assert len(extracted) == 2
        assert extracted[0].citation_indices == [1]
        assert extracted[1].citation_indices == [2]

    def test_no_citations(self):
        """Test text with no citations."""
        text = "This text has no citations."
        extracted = extract_citation_markers(text)
        assert len(extracted) == 0

    def test_claim_context_extraction(self):
        """Test that claim context is extracted correctly."""
        text = "First point. The key finding is X [1]. Another point."
        extracted = extract_citation_markers(text)
        assert len(extracted) == 1
        # Claim should contain the surrounding sentence without the marker
        assert "key finding is X" in extracted[0].claim_text
        # Marker should be removed from claim
        assert "[1]" not in extracted[0].claim_text

    def test_get_used_citation_indices(self):
        """Test getting set of used citation indices."""
        text = "Claim one [1]. Claim two [2;3]. Claim three [1]."
        used = get_used_citation_indices(text)
        assert used == {1, 2, 3}

    def test_empty_text(self):
        """Test with empty text."""
        assert extract_citation_markers("") == []
        assert get_used_citation_indices("") == set()


class TestCitationValidation:
    """Tests for citation validation logic."""

    @pytest.fixture
    def validator(self):
        """Create a validator with semantic disabled for faster tests."""
        return CitationValidator(mode=ValidationMode.WARN, use_semantic=False)

    @pytest.fixture
    def citations(self):
        """Create test citations."""
        return [
            Citation(
                document_id="doc1",
                filename="data_sovereignty.pdf",
                content_preview="Data sovereignty refers to the control over data. "
                "It involves legal jurisdiction and governance of information.",
            ),
            Citation(
                document_id="doc2",
                filename="machine_learning.pdf",
                content_preview="Machine learning uses algorithms to learn from data. "
                "Neural networks are a key component of deep learning.",
            ),
        ]

    def test_valid_citation_keyword_match(self, validator, citations):
        """Test validation of accurate citation with keyword overlap."""
        extracted = [
            ExtractedCitation(
                marker_text="[1]",
                citation_indices=[1],
                claim_text="Data sovereignty is about control over data",
                char_start=0,
                char_end=3,
            )
        ]

        report = validator.validate("...", citations, extracted)
        assert len(report.validations) == 1
        assert report.validations[0].result == ValidationResult.VALID
        assert report.validations[0].keyword_overlap > 0.2

    def test_invalid_citation_no_match(self, validator, citations):
        """Test validation of inaccurate citation with no content match."""
        extracted = [
            ExtractedCitation(
                marker_text="[1]",
                citation_indices=[1],
                claim_text="Quantum computing enables faster calculations",
                char_start=0,
                char_end=3,
            )
        ]

        report = validator.validate("...", citations, extracted)
        assert len(report.validations) == 1
        assert report.validations[0].result == ValidationResult.INVALID

    def test_out_of_range_citation(self, validator, citations):
        """Test citation index out of range."""
        extracted = [
            ExtractedCitation(
                marker_text="[5]",
                citation_indices=[5],
                claim_text="Something claimed",
                char_start=0,
                char_end=3,
            )
        ]

        report = validator.validate("...", citations, extracted)
        assert len(report.validations) == 1
        assert report.validations[0].result == ValidationResult.OUT_OF_RANGE

    def test_unused_citations_detected(self, validator, citations):
        """Test that unused citations are detected."""
        extracted = [
            ExtractedCitation(
                marker_text="[1]",
                citation_indices=[1],
                claim_text="Data control is important",
                char_start=0,
                char_end=3,
            )
        ]

        report = validator.validate("...", citations, extracted)
        # Citation [2] was not used
        assert 2 in report.unused_citations

    def test_multi_source_citation_validates_all(self, validator, citations):
        """Test validation of multi-source citation [1;2]."""
        extracted = [
            ExtractedCitation(
                marker_text="[1;2]",
                citation_indices=[1, 2],
                claim_text="Data sovereignty concepts",
                char_start=0,
                char_end=5,
            )
        ]

        report = validator.validate("...", citations, extracted)
        # Should have validations for both indices
        assert len(report.validations) == 2

    def test_hallucination_like_lycett_case(self, validator):
        """Test detection of hallucination similar to Lycett paper case.

        The Lycett paper discussed music memorabilia heritage preservation,
        but the LLM claimed it discussed "data sovereignty" and
        "sovereign control over information" - terms not in the source.
        """
        citations = [
            Citation(
                document_id="lycett",
                filename="lycett-metaverse.pdf",
                content_preview="Visitors have a want to preserve heritage in relation "
                "to the artists that they followed. The ability to link information "
                "and create compelling narratives around assets.",
            )
        ]

        # The hallucinated claim - uses terms NOT in the source
        extracted = [
            ExtractedCitation(
                marker_text="[1]",
                citation_indices=[1],
                claim_text="Data sovereignty is discussed in terms of cultural-heritage "
                "control and sovereign control over information",
                char_start=0,
                char_end=3,
            )
        ]

        report = validator.validate("...", citations, extracted)
        assert len(report.validations) == 1
        # Should detect this as INVALID or WEAK due to low keyword overlap
        # "data sovereignty" and "sovereign control" are NOT in the source
        assert report.validations[0].result in (
            ValidationResult.INVALID,
            ValidationResult.WEAK,
        )
        assert report.has_hallucinations or report.validations[0].confidence < 0.5


class TestValidationReport:
    """Tests for ValidationReport properties."""

    def test_valid_count(self):
        """Test valid_count property."""
        report = ValidationReport(
            validations=[
                CitationValidation(
                    citation_index=1,
                    result=ValidationResult.VALID,
                    confidence=0.8,
                    claim_text="",
                    source_preview="",
                    keyword_overlap=0.4,
                ),
                CitationValidation(
                    citation_index=2,
                    result=ValidationResult.INVALID,
                    confidence=0.1,
                    claim_text="",
                    source_preview="",
                    keyword_overlap=0.05,
                ),
            ],
            unused_citations=[],
            overall_confidence=0.45,
        )
        assert report.valid_count == 1
        assert report.invalid_count == 1

    def test_has_hallucinations(self):
        """Test has_hallucinations property."""
        report = ValidationReport(
            validations=[
                CitationValidation(
                    citation_index=1,
                    result=ValidationResult.INVALID,
                    confidence=0.1,
                    claim_text="",
                    source_preview="",
                    keyword_overlap=0.05,
                ),
            ],
            unused_citations=[],
            overall_confidence=0.1,
        )
        assert report.has_hallucinations is True


class TestValidationModes:
    """Tests for different validation modes."""

    @pytest.fixture
    def citations(self):
        return [
            Citation(
                document_id="doc1",
                filename="test.pdf",
                content_preview="Test content about specific topic.",
            )
        ]

    def test_warn_mode_keeps_all(self, citations):
        """Test that warn mode keeps all citations."""
        validator = CitationValidator(mode=ValidationMode.WARN)
        extracted = [
            ExtractedCitation(
                marker_text="[1]",
                citation_indices=[1],
                claim_text="Unrelated claim",
                char_start=0,
                char_end=3,
            )
        ]
        report = validator.validate("...", citations, extracted)
        # Warn mode should still produce a report
        assert report is not None
        assert len(report.validations) == 1

    def test_filter_mode_flags_invalid(self, citations):
        """Test that filter mode flags invalid citations."""
        validator = CitationValidator(mode=ValidationMode.FILTER)
        extracted = [
            ExtractedCitation(
                marker_text="[1]",
                citation_indices=[1],
                # Use words that definitely don't overlap with "Test content about specific topic"
                claim_text="Quantum computing enables faster cryptographic calculations",
                char_start=0,
                char_end=3,
            )
        ]
        report = validator.validate("...", citations, extracted)
        # Should still validate and flag invalid
        assert report.validations[0].result in (
            ValidationResult.INVALID,
            ValidationResult.WEAK,
        )


class TestConvenienceFunction:
    """Tests for the validate_citations convenience function."""

    def test_validate_citations_function(self):
        """Test the validate_citations convenience function."""
        response = "This is about data governance [1]."
        citations = [
            Citation(
                document_id="doc1",
                filename="governance.pdf",
                content_preview="Data governance involves policies and procedures.",
            )
        ]

        report = validate_citations(response, citations)
        assert report is not None
        assert len(report.validations) >= 1


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_content_preview(self):
        """Test validation with empty content preview."""
        validator = CitationValidator()
        citations = [
            Citation(
                document_id="doc1",
                filename="empty.pdf",
                content_preview="",
            )
        ]
        extracted = [
            ExtractedCitation(
                marker_text="[1]",
                citation_indices=[1],
                claim_text="Some claim",
                char_start=0,
                char_end=3,
            )
        ]
        report = validator.validate("...", citations, extracted)
        # Should handle gracefully
        assert report is not None
        assert report.validations[0].result == ValidationResult.INVALID

    def test_none_content_preview(self):
        """Test validation with None content preview."""
        validator = CitationValidator()
        citations = [
            Citation(
                document_id="doc1",
                filename="none.pdf",
                content_preview=None,
            )
        ]
        extracted = [
            ExtractedCitation(
                marker_text="[1]",
                citation_indices=[1],
                claim_text="Some claim",
                char_start=0,
                char_end=3,
            )
        ]
        report = validator.validate("...", citations, extracted)
        # Should handle gracefully
        assert report is not None

    def test_no_extracted_citations(self):
        """Test validation with no extracted citations."""
        validator = CitationValidator()
        citations = [
            Citation(
                document_id="doc1",
                filename="test.pdf",
                content_preview="Some content",
            )
        ]
        report = validator.validate("Text without citations", citations, [])
        assert report.overall_confidence == 1.0
        assert report.unused_citations == [1]

    def test_stopword_heavy_claim(self):
        """Test that stopwords don't inflate keyword overlap."""
        validator = CitationValidator()
        citations = [
            Citation(
                document_id="doc1",
                filename="test.pdf",
                content_preview="Machine learning algorithms process data efficiently.",
            )
        ]
        extracted = [
            ExtractedCitation(
                marker_text="[1]",
                citation_indices=[1],
                # Claim with many stopwords but different content words
                claim_text="The data is in the system and it has been processed",
                char_start=0,
                char_end=3,
            )
        ]
        report = validator.validate("...", citations, extracted)
        # Should not validate as VALID just because of shared stopwords
        # "data" and "processed" match, but overall overlap should be moderate
        assert report.validations[0].keyword_overlap < 0.5
