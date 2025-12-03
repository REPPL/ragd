"""Tests for extraction quality scoring module."""

import tempfile
from pathlib import Path

import pytest

from ragd.quality.metrics import (
    QualityMetrics,
    compute_completeness,
    compute_character_quality,
    compute_structure_score,
    compute_image_handling,
    compute_table_handling,
    compute_overall_score,
)
from ragd.quality.scorer import (
    QualityScorer,
    score_document,
    score_extraction,
    DocumentQuality,
)


# --- QualityMetrics tests ---


def test_quality_metrics_defaults() -> None:
    """Test QualityMetrics default values."""
    metrics = QualityMetrics()
    assert metrics.completeness == 0.0
    assert metrics.character_quality == 0.0
    assert metrics.structure == 0.0
    assert metrics.images == 0.0
    assert metrics.tables == 0.0
    assert metrics.overall == 0.0
    assert metrics.computed_at is not None
    assert metrics.details == {}


def test_quality_metrics_to_dict() -> None:
    """Test QualityMetrics serialisation."""
    metrics = QualityMetrics(
        completeness=0.8,
        character_quality=0.9,
        structure=0.7,
        images=0.6,
        tables=0.5,
        overall=0.75,
    )
    data = metrics.to_dict()
    assert data["completeness"] == 0.8
    assert data["character_quality"] == 0.9
    assert data["structure"] == 0.7
    assert data["images"] == 0.6
    assert data["tables"] == 0.5
    assert data["overall"] == 0.75


def test_quality_metrics_from_dict() -> None:
    """Test QualityMetrics deserialisation."""
    data = {
        "completeness": 0.8,
        "character_quality": 0.9,
        "structure": 0.7,
        "images": 0.6,
        "tables": 0.5,
        "overall": 0.75,
    }
    metrics = QualityMetrics.from_dict(data)
    assert metrics.completeness == 0.8
    assert metrics.overall == 0.75


# --- Completeness tests ---


def test_compute_completeness_empty_file() -> None:
    """Test completeness for empty file."""
    score, details = compute_completeness("", 0, "txt")
    assert score == 0.0
    assert "reason" in details


def test_compute_completeness_good_ratio() -> None:
    """Test completeness with good text ratio."""
    text = "x" * 800  # 800 chars
    file_size = 1000  # 1KB file
    score, details = compute_completeness(text, file_size, "txt")
    # txt expects high ratio (0.8-1.0), 0.8 ratio should score well
    assert score >= 0.7
    assert "text_ratio" in details


def test_compute_completeness_low_ratio() -> None:
    """Test completeness with very low text ratio (likely image PDF)."""
    text = "x" * 100  # Only 100 chars
    file_size = 1000000  # 1MB file (image-heavy PDF)
    score, details = compute_completeness(text, file_size, "pdf")
    assert score < 0.5
    assert "assessment" in details


def test_compute_completeness_pdf_expected_ratio() -> None:
    """Test completeness for PDF with expected ratio."""
    text = "x" * 50000  # 50K chars
    file_size = 500000  # 500KB file
    # PDF ratio: 50K/500K = 0.1, within expected range
    score, details = compute_completeness(text, file_size, "pdf")
    assert score >= 0.7


# --- Character quality tests ---


def test_compute_character_quality_clean_text() -> None:
    """Test character quality with clean ASCII text."""
    text = "This is clean English text without any encoding issues."
    score, details = compute_character_quality(text)
    assert score >= 0.95
    assert details["problem_chars"] == 0


def test_compute_character_quality_with_mojibake() -> None:
    """Test character quality with mojibake characters."""
    # Simulate double-encoded UTF-8
    text = "This text has â€™ encoding issues â€œ here"
    score, details = compute_character_quality(text)
    assert score < 0.9
    assert details["problem_chars"] > 0


def test_compute_character_quality_replacement_chars() -> None:
    """Test character quality with replacement characters."""
    text = "Text with \ufffd replacement \ufffd characters"
    score, details = compute_character_quality(text)
    assert score < 0.95


def test_compute_character_quality_empty() -> None:
    """Test character quality with empty text."""
    score, details = compute_character_quality("")
    assert score == 0.0
    assert "reason" in details


# --- Structure tests ---


def test_compute_structure_markdown() -> None:
    """Test structure detection in markdown text."""
    text = """# Heading 1

Some paragraph text here.

## Heading 2

- List item 1
- List item 2
- List item 3

More **bold** and *italic* text.

[A link](https://example.com)

```python
code block
```
"""
    score, details = compute_structure_score(text, "md")
    assert score >= 0.7
    assert details["elements_found"]["headings"] >= 2
    assert details["elements_found"]["lists"] >= 3


def test_compute_structure_plain_text() -> None:
    """Test structure for plain text (no markdown expected)."""
    text = "Just some plain text.\n\nAnother paragraph."
    score, details = compute_structure_score(text, "txt")
    # Plain text isn't expected to have markdown structure
    assert "Plain text" in details["assessment"]


def test_compute_structure_no_structure() -> None:
    """Test structure when no formatting is present."""
    text = "x" * 1000  # Long text with no structure
    score, details = compute_structure_score(text, "html")
    assert score < 0.5
    assert "No structure" in details.get("assessment", "")


# --- Image handling tests ---


def test_compute_image_handling_with_placeholders() -> None:
    """Test image handling with proper placeholders."""
    text = """Some text here.

[Image: Diagram showing system architecture]

More text.

[Figure 1: Results chart]

Conclusion.
"""
    score, details = compute_image_handling(text, "pdf")
    assert score >= 0.7
    assert details["patterns_found"]["placeholder"] >= 2


def test_compute_image_handling_markdown_images() -> None:
    """Test image handling with markdown image syntax."""
    text = """
![Alt text for image](image.png)

Some description.

![Another image](diagram.jpg)
"""
    score, details = compute_image_handling(text, "md")
    assert details["patterns_found"]["markdown_image"] >= 2


def test_compute_image_handling_plain_text() -> None:
    """Test image handling for plain text (N/A)."""
    text = "Just plain text."
    score, details = compute_image_handling(text, "txt")
    assert score == 1.0  # N/A is perfect
    assert "not applicable" in details["assessment"]


# --- Table handling tests ---


def test_compute_table_handling_markdown_table() -> None:
    """Test table handling with markdown tables."""
    text = """
Some text.

| Column A | Column B | Column C |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |

More text.
"""
    score, details = compute_table_handling(text, "md")
    assert score >= 0.9
    assert details["has_markdown_table"] is True


def test_compute_table_handling_placeholder() -> None:
    """Test table handling with placeholders."""
    text = """
Some text.

[Table 1: Summary of results]

More text.
"""
    score, details = compute_table_handling(text, "pdf")
    assert score >= 0.6
    assert details["has_placeholder"] is True


def test_compute_table_handling_plain_text() -> None:
    """Test table handling for plain text (N/A)."""
    text = "Just plain text."
    score, details = compute_table_handling(text, "txt")
    assert score == 1.0  # N/A is perfect


# --- Overall score tests ---


def test_compute_overall_score_weighted() -> None:
    """Test weighted overall score calculation."""
    metrics = QualityMetrics(
        completeness=1.0,
        character_quality=1.0,
        structure=1.0,
        images=1.0,
        tables=1.0,
    )
    overall = compute_overall_score(metrics)
    assert overall == 1.0


def test_compute_overall_score_partial() -> None:
    """Test overall score with partial scores."""
    metrics = QualityMetrics(
        completeness=0.8,
        character_quality=0.9,
        structure=0.7,
        images=0.6,
        tables=0.5,
    )
    overall = compute_overall_score(metrics)
    # Should be weighted average: 0.8*0.30 + 0.9*0.25 + 0.7*0.20 + 0.6*0.15 + 0.5*0.10
    expected = 0.24 + 0.225 + 0.14 + 0.09 + 0.05  # = 0.745
    assert abs(overall - expected) < 0.01


# --- Scorer tests ---


def test_score_extraction_basic() -> None:
    """Test score_extraction convenience function."""
    text = "# Test Document\n\nSome good content here with proper structure."
    result = score_extraction(
        text=text,
        file_size=len(text),
        file_type="md",
        document_id="test-123",
        filename="test.md",
    )
    assert result.success is True
    assert result.document_id == "test-123"
    assert result.metrics.overall > 0


def test_score_extraction_empty() -> None:
    """Test score_extraction with empty text.

    Empty text is technically a valid (but very low quality) extraction.
    The metrics will all be 0.0 or near 0.0.
    """
    result = score_extraction(
        text="",
        file_size=1000,
        file_type="pdf",
    )
    # Empty text results in 0.0 metrics but is technically "successful"
    assert result.success is True
    assert result.metrics.overall == 0.0
    assert result.metrics.completeness == 0.0


def test_score_document_txt_file() -> None:
    """Test scoring an actual text file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("This is a test document.\n\nIt has multiple paragraphs.\n\nAnd some content.")
        f.flush()
        path = Path(f.name)

    try:
        result = score_document(path)
        assert result.success is True
        assert result.file_type == "txt"
        assert result.metrics.overall > 0
    finally:
        path.unlink()


def test_score_document_nonexistent() -> None:
    """Test scoring a nonexistent file."""
    path = Path("/nonexistent/file.txt")
    result = score_document(path)
    assert result.success is False


def test_document_quality_dataclass() -> None:
    """Test DocumentQuality dataclass."""
    metrics = QualityMetrics(overall=0.8)
    quality = DocumentQuality(
        document_id="test-123",
        path="/path/to/doc.pdf",
        filename="doc.pdf",
        file_type="pdf",
        metrics=metrics,
        success=True,
    )
    assert quality.document_id == "test-123"
    assert quality.metrics.overall == 0.8
    assert quality.error is None
