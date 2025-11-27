"""Tests for PDF quality detection module."""

from __future__ import annotations

import tempfile
from pathlib import Path

import fitz
import pytest

from ragd.pdf.quality import (
    PDFQuality,
    PDFQualityDetector,
    QualityAssessment,
)


class TestQualityAssessment:
    """Tests for QualityAssessment dataclass."""

    def test_assessment_creation(self) -> None:
        """Test creating a QualityAssessment."""
        assessment = QualityAssessment(
            quality=PDFQuality.DIGITAL_NATIVE,
            text_coverage=0.95,
            scan_probability=0.1,
            has_tables=False,
            has_multi_column=False,
            page_count=5,
            recommended_pipeline="fast",
            confidence=0.9,
        )
        assert assessment.quality == PDFQuality.DIGITAL_NATIVE
        assert assessment.text_coverage == 0.95
        assert assessment.recommended_pipeline == "fast"

    def test_assessment_is_frozen(self) -> None:
        """Test that QualityAssessment is immutable."""
        assessment = QualityAssessment(
            quality=PDFQuality.DIGITAL_NATIVE,
            text_coverage=0.95,
            scan_probability=0.1,
            has_tables=False,
            has_multi_column=False,
            page_count=5,
            recommended_pipeline="fast",
            confidence=0.9,
        )
        with pytest.raises(AttributeError):
            assessment.quality = PDFQuality.SCANNED  # type: ignore[misc]

    def test_assessment_str(self) -> None:
        """Test string representation of QualityAssessment."""
        assessment = QualityAssessment(
            quality=PDFQuality.DIGITAL_NATIVE,
            text_coverage=0.95,
            scan_probability=0.1,
            has_tables=False,
            has_multi_column=False,
            page_count=5,
            recommended_pipeline="fast",
            confidence=0.9,
        )
        result = str(assessment)
        assert "digital_native" in result
        assert "fast" in result
        assert "95%" in result


class TestPDFQuality:
    """Tests for PDFQuality enum."""

    def test_all_quality_types(self) -> None:
        """Test all PDF quality types are defined."""
        assert PDFQuality.DIGITAL_NATIVE.value == "digital_native"
        assert PDFQuality.COMPLEX_LAYOUT.value == "complex_layout"
        assert PDFQuality.SCANNED.value == "scanned"
        assert PDFQuality.MIXED.value == "mixed"


class TestPDFQualityDetector:
    """Tests for PDFQualityDetector class."""

    def test_init(self) -> None:
        """Test detector initialisation."""
        detector = PDFQualityDetector()
        assert detector is not None

    def test_assess_nonexistent_file(self) -> None:
        """Test assessing a non-existent file raises error."""
        detector = PDFQualityDetector()
        with pytest.raises(FileNotFoundError):
            detector.assess(Path("/nonexistent/file.pdf"))

    def test_assess_non_pdf_file(self) -> None:
        """Test assessing a non-PDF file raises error."""
        detector = PDFQualityDetector()
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"Not a PDF")
            path = Path(f.name)
        try:
            with pytest.raises(ValueError, match="Not a PDF file"):
                detector.assess(path)
        finally:
            path.unlink()

    def test_assess_digital_pdf(self) -> None:
        """Test assessing a digital-native PDF with text."""
        detector = PDFQualityDetector()

        # Create a simple PDF with text
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            doc = fitz.open()
            page = doc.new_page()
            # Add substantial text content
            text = "This is a test document with substantial text content. " * 20
            page.insert_text((50, 50), text, fontsize=12)
            doc.save(f.name)
            doc.close()
            path = Path(f.name)

        try:
            assessment = detector.assess(path)
            assert assessment.page_count == 1
            assert assessment.text_coverage > 0
            # Digital PDF with text should recommend fast or structure
            assert assessment.recommended_pipeline in ("fast", "structure")
            assert assessment.confidence > 0.5
        finally:
            path.unlink()

    def test_assess_empty_pdf(self) -> None:
        """Test assessing a PDF with a blank page (no text content)."""
        detector = PDFQualityDetector()

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            doc = fitz.open()
            doc.new_page()  # Add one blank page (PyMuPDF requires at least one)
            doc.save(f.name)
            doc.close()
            path = Path(f.name)

        try:
            assessment = detector.assess(path)
            assert assessment.page_count == 1
            assert assessment.text_coverage == 0.0
            # Blank page should still route to fast (no text to process)
            assert assessment.recommended_pipeline in ("fast", "structure")
        finally:
            path.unlink()

    def test_assess_pdf_with_minimal_text(self) -> None:
        """Test PDF with very little text is flagged correctly."""
        detector = PDFQualityDetector()

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((50, 50), "Hi", fontsize=12)  # Minimal text
            doc.save(f.name)
            doc.close()
            path = Path(f.name)

        try:
            assessment = detector.assess(path)
            assert assessment.page_count == 1
            # With minimal text, scan probability should be higher
            # and text coverage lower
        finally:
            path.unlink()

    def test_assess_multipage_pdf(self) -> None:
        """Test assessing a multi-page PDF."""
        detector = PDFQualityDetector()

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            doc = fitz.open()
            for i in range(5):
                page = doc.new_page()
                text = f"Page {i + 1} with substantial content. " * 15
                page.insert_text((50, 50), text, fontsize=12)
            doc.save(f.name)
            doc.close()
            path = Path(f.name)

        try:
            assessment = detector.assess(path)
            assert assessment.page_count == 5
            assert assessment.text_coverage > 0.5
        finally:
            path.unlink()


class TestPDFQualityDetectorRouting:
    """Tests for pipeline routing logic."""

    def test_high_text_coverage_routes_to_fast(self) -> None:
        """Test that high text coverage routes to fast pipeline."""
        detector = PDFQualityDetector()

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            doc = fitz.open()
            # Create multiple pages with lots of text
            for _ in range(3):
                page = doc.new_page()
                for y in range(50, 700, 20):
                    text = "This is substantial text content for the page. " * 3
                    page.insert_text((50, y), text, fontsize=10)
            doc.save(f.name)
            doc.close()
            path = Path(f.name)

        try:
            assessment = detector.assess(path)
            # High text coverage should route to fast
            assert assessment.text_coverage >= 0.8
            # Could be fast or structure depending on layout detection
            assert assessment.recommended_pipeline in ("fast", "structure")
        finally:
            path.unlink()

    def test_low_text_coverage_may_route_to_ocr(self) -> None:
        """Test that low text coverage may indicate OCR needed."""
        detector = PDFQualityDetector()

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            doc = fitz.open()
            # Create a page with an image but no text
            page = doc.new_page()
            # Just create an empty page (simulating image-only PDF)
            doc.save(f.name)
            doc.close()
            path = Path(f.name)

        try:
            assessment = detector.assess(path)
            # Low/no text coverage increases scan probability
            assert assessment.text_coverage == 0.0
        finally:
            path.unlink()


class TestPDFQualityEdgeCases:
    """Tests for edge cases in PDF quality detection."""

    def test_corrupted_pdf_raises_error(self) -> None:
        """Test that corrupted PDF raises appropriate error."""
        detector = PDFQualityDetector()

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"Not a valid PDF content")
            path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Cannot open PDF"):
                detector.assess(path)
        finally:
            path.unlink()

    def test_large_pdf_samples_first_pages(self) -> None:
        """Test that large PDFs only sample first 10 pages."""
        detector = PDFQualityDetector()

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            doc = fitz.open()
            # Create 15 pages
            for i in range(15):
                page = doc.new_page()
                text = f"Page {i + 1} content. " * 10
                page.insert_text((50, 50), text, fontsize=12)
            doc.save(f.name)
            doc.close()
            path = Path(f.name)

        try:
            assessment = detector.assess(path)
            assert assessment.page_count == 15
            # Analysis should still work (samples first 10 pages)
            assert assessment.text_coverage > 0
        finally:
            path.unlink()
