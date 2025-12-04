"""Tests for operations quality scoring (F-115 simplified scoring)."""

import pytest

from ragd.operations.quality import (
    QualityFlag,
    QualityScore,
    score_extraction_confidence,
    score_text_completeness,
    score_formatting_quality,
    calculate_quality_score,
    format_quality_badge,
    format_quality_summary,
)


class TestQualityScore:
    """Tests for QualityScore dataclass."""

    def test_default_perfect_score(self):
        """Default score should be perfect (1.0)."""
        score = QualityScore()
        assert score.extraction_confidence == 1.0
        assert score.text_completeness == 1.0
        assert score.formatting_quality == 1.0
        assert score.overall == 1.0

    def test_overall_weighted_average(self):
        """Overall should be weighted average."""
        score = QualityScore(
            extraction_confidence=0.8,
            text_completeness=0.6,
            formatting_quality=0.5,
        )
        # 0.8 * 0.4 + 0.6 * 0.4 + 0.5 * 0.2 = 0.32 + 0.24 + 0.1 = 0.66
        assert abs(score.overall - 0.66) < 0.01

    def test_grade_a(self):
        """High scores should get grade A."""
        score = QualityScore(
            extraction_confidence=0.95,
            text_completeness=0.95,
            formatting_quality=0.9,
        )
        assert score.grade == "A"

    def test_grade_f(self):
        """Very low scores should get grade F."""
        score = QualityScore(
            extraction_confidence=0.4,
            text_completeness=0.4,
            formatting_quality=0.3,
        )
        assert score.grade == "F"

    def test_is_high_quality(self):
        """Should detect high quality."""
        high = QualityScore(
            extraction_confidence=0.9,
            text_completeness=0.9,
            formatting_quality=0.9,
        )
        assert high.is_high_quality is True

    def test_is_low_quality(self):
        """Should detect low quality."""
        low = QualityScore(
            extraction_confidence=0.4,
            text_completeness=0.4,
            formatting_quality=0.4,
        )
        assert low.is_low_quality is True

    def test_to_dict(self):
        """Should convert to dictionary."""
        score = QualityScore(
            extraction_confidence=0.8,
            text_completeness=0.7,
            formatting_quality=0.9,
            flags=[QualityFlag.NATIVE_TEXT],
        )

        d = score.to_dict()
        assert d["extraction_confidence"] == 0.8
        assert "native_text" in d["flags"]

    def test_from_dict(self):
        """Should create from dictionary."""
        data = {
            "extraction_confidence": 0.85,
            "text_completeness": 0.75,
            "formatting_quality": 0.65,
            "flags": ["ocr_required"],
        }

        score = QualityScore.from_dict(data)
        assert score.extraction_confidence == 0.85
        assert QualityFlag.OCR_REQUIRED in score.flags


class TestExtractionConfidenceScoring:
    """Tests for extraction confidence scoring."""

    def test_native_text_high_score(self):
        """Native text should score high."""
        score, flags = score_extraction_confidence(
            "This is clean native text.",
            is_ocr=False,
        )
        assert score == 1.0
        assert QualityFlag.NATIVE_TEXT in flags

    def test_ocr_lower_score(self):
        """OCR text should score lower."""
        score, flags = score_extraction_confidence(
            "This is OCR text.",
            is_ocr=True,
        )
        assert score < 1.0
        assert QualityFlag.OCR_REQUIRED in flags

    def test_ocr_with_confidence(self):
        """OCR confidence should be used."""
        score, flags = score_extraction_confidence(
            "OCR text with high confidence.",
            is_ocr=True,
            ocr_confidence=0.95,
        )
        assert score >= 0.9


class TestTextCompletenessScoring:
    """Tests for text completeness scoring."""

    def test_short_text_low_score(self):
        """Very short text should score low."""
        score, flags = score_text_completeness("Short")
        assert score < 0.5
        assert QualityFlag.INCOMPLETE in flags

    def test_long_text_high_score(self):
        """Long text should score high."""
        text = "This is a substantial piece of text. " * 20
        score, flags = score_text_completeness(text)
        assert score >= 0.8


class TestFormattingQualityScoring:
    """Tests for formatting quality scoring."""

    def test_structured_content_high_score(self):
        """Structured content should score high."""
        text = """# Heading

Paragraph one.

- List item one
- List item two"""
        score, flags = score_formatting_quality(text, has_structure=True)
        assert score >= 0.8
        assert QualityFlag.STRUCTURE_PRESERVED in flags

    def test_skipped_images_penalised(self):
        """Skipped images should lower score."""
        text = "Content with images"
        score, flags = score_formatting_quality(text, images_skipped=5)
        assert score < 0.8
        assert QualityFlag.IMAGES_SKIPPED in flags


class TestCalculateQualityScore:
    """Tests for comprehensive quality scoring."""

    def test_perfect_document(self):
        """Perfect document should score high."""
        text = """# Document Title

This is a well-structured document with plenty of content to ensure the text
completeness scoring is satisfied. The document contains multiple sections
with substantial paragraphs.

## Section One

First paragraph here with more detailed content. This section covers the
main topic with sufficient detail to demonstrate proper extraction.

- Point one with explanation
- Point two with explanation
- Point three with more content

## Section Two

Another section with additional content to meet the minimum threshold for
high quality document scoring. This ensures completeness is properly rated."""

        score = calculate_quality_score(
            text,
            is_ocr=False,
            has_structure=True,
        )

        assert score.overall >= 0.8
        assert score.grade in ["A", "B"]

    def test_poor_ocr_document(self):
        """Poor OCR document should score low."""
        text = "Sh0rt OCR t3xt"
        score = calculate_quality_score(
            text,
            is_ocr=True,
            ocr_confidence=0.5,
            has_missing_sections=True,
        )

        assert score.overall < 0.6
        assert QualityFlag.OCR_REQUIRED in score.flags


class TestFormatQualityBadge:
    """Tests for quality badge formatting."""

    def test_high_quality_green(self):
        """High quality should be green."""
        score = QualityScore(
            extraction_confidence=0.95,
            text_completeness=0.95,
            formatting_quality=0.9,
        )
        badge = format_quality_badge(score)
        assert "green" in badge
        assert "A" in badge


class TestFormatQualitySummary:
    """Tests for quality summary formatting."""

    def test_includes_grade(self):
        """Summary should include grade."""
        score = QualityScore()
        summary = format_quality_summary(score)
        assert "A" in summary
