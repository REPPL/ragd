"""Tests for OCR module."""

from __future__ import annotations

import tempfile
from pathlib import Path

import fitz
import pytest

from ragd.features import (
    EASYOCR_AVAILABLE,
    PADDLEOCR_AVAILABLE,
    DependencyError,
)
from ragd.ocr import (
    BoundingBox,
    DocumentOCRResult,
    OCRConfig,
    OCRResult,
    PageOCRResult,
    calculate_weighted_confidence,
    create_ocr_engine,
    filter_by_confidence,
    get_available_engine,
)


class TestBoundingBox:
    """Tests for BoundingBox dataclass."""

    def test_creation(self) -> None:
        """Test creating a BoundingBox."""
        bbox = BoundingBox(x1=10, y1=20, x2=100, y2=50)
        assert bbox.x1 == 10
        assert bbox.y1 == 20
        assert bbox.x2 == 100
        assert bbox.y2 == 50

    def test_from_quad(self) -> None:
        """Test creating from quadrilateral coordinates."""
        quad = [[10, 20], [100, 20], [100, 50], [10, 50]]
        bbox = BoundingBox.from_quad(quad)
        assert bbox.x1 == 10
        assert bbox.y1 == 20
        assert bbox.x2 == 100
        assert bbox.y2 == 50

    def test_from_quad_rotated(self) -> None:
        """Test from_quad handles rotated text."""
        # Slightly rotated quad
        quad = [[15, 20], [105, 25], [100, 55], [10, 50]]
        bbox = BoundingBox.from_quad(quad)
        assert bbox.x1 == 10
        assert bbox.y1 == 20
        assert bbox.x2 == 105
        assert bbox.y2 == 55


class TestOCRResult:
    """Tests for OCRResult dataclass."""

    def test_creation(self) -> None:
        """Test creating an OCRResult."""
        result = OCRResult(
            text="Hello World",
            confidence=0.95,
            engine="paddleocr",
        )
        assert result.text == "Hello World"
        assert result.confidence == 0.95
        assert result.engine == "paddleocr"

    def test_with_bbox(self) -> None:
        """Test OCRResult with bounding box."""
        bbox = BoundingBox(x1=0, y1=0, x2=100, y2=20)
        result = OCRResult(
            text="Test",
            confidence=0.8,
            bbox=bbox,
            line_number=0,
        )
        assert result.bbox is not None
        assert result.line_number == 0

    def test_str_representation(self) -> None:
        """Test string representation."""
        result = OCRResult(text="Test text", confidence=0.85)
        s = str(result)
        assert "Test text" in s
        assert "0.85" in s


class TestPageOCRResult:
    """Tests for PageOCRResult dataclass."""

    def test_creation(self) -> None:
        """Test creating a PageOCRResult."""
        result = PageOCRResult(page_number=0)
        assert result.page_number == 0
        assert result.results == []
        assert result.full_text == ""

    def test_with_results(self) -> None:
        """Test PageOCRResult with OCR results."""
        results = [
            OCRResult(text="Line 1", confidence=0.9),
            OCRResult(text="Line 2", confidence=0.8),
        ]
        page = PageOCRResult(
            page_number=0,
            results=results,
            processing_time_ms=100,
            engine_used="paddleocr",
        )
        assert page.text_count == 2
        assert page.full_text == "Line 1\nLine 2"
        assert page.average_confidence == pytest.approx(0.85)

    def test_average_confidence_empty(self) -> None:
        """Test average confidence with no results."""
        page = PageOCRResult(page_number=0)
        assert page.average_confidence == 0.0

    def test_str_representation(self) -> None:
        """Test string representation."""
        results = [OCRResult(text="Test", confidence=0.9)]
        page = PageOCRResult(
            page_number=1,
            results=results,
            processing_time_ms=50,
        )
        s = str(page)
        assert "Page 1" in s
        assert "1 segments" in s
        assert "50ms" in s


class TestDocumentOCRResult:
    """Tests for DocumentOCRResult dataclass."""

    def test_creation(self) -> None:
        """Test creating a DocumentOCRResult."""
        result = DocumentOCRResult()
        assert result.pages == []
        assert result.page_count == 0

    def test_with_pages(self) -> None:
        """Test DocumentOCRResult with pages."""
        pages = [
            PageOCRResult(
                page_number=0,
                results=[OCRResult(text="Page 1 text", confidence=0.9)],
            ),
            PageOCRResult(
                page_number=1,
                results=[OCRResult(text="Page 2 text", confidence=0.8)],
            ),
        ]
        doc = DocumentOCRResult(
            pages=pages,
            total_processing_time_ms=200,
            primary_engine="PaddleOCR",
        )
        assert doc.page_count == 2
        assert "Page 1 text" in doc.full_text
        assert "Page 2 text" in doc.full_text
        assert doc.average_confidence == pytest.approx(0.85)

    def test_quality_assessment_excellent(self) -> None:
        """Test quality assessment for excellent results."""
        pages = [
            PageOCRResult(
                page_number=0,
                results=[OCRResult(text="Test", confidence=0.95)],
            )
        ]
        doc = DocumentOCRResult(pages=pages)
        assert doc.get_quality_assessment() == "excellent"

    def test_quality_assessment_good(self) -> None:
        """Test quality assessment for good results."""
        pages = [
            PageOCRResult(
                page_number=0,
                results=[OCRResult(text="Test", confidence=0.75)],
            )
        ]
        doc = DocumentOCRResult(pages=pages)
        assert doc.get_quality_assessment() == "good"

    def test_quality_assessment_fair(self) -> None:
        """Test quality assessment for fair results."""
        pages = [
            PageOCRResult(
                page_number=0,
                results=[OCRResult(text="Test", confidence=0.55)],
            )
        ]
        doc = DocumentOCRResult(pages=pages)
        assert "fair" in doc.get_quality_assessment()

    def test_quality_assessment_poor(self) -> None:
        """Test quality assessment for poor results."""
        pages = [
            PageOCRResult(
                page_number=0,
                results=[OCRResult(text="Test", confidence=0.3)],
            )
        ]
        doc = DocumentOCRResult(pages=pages)
        assert "poor" in doc.get_quality_assessment()


class TestOCRConfig:
    """Tests for OCRConfig dataclass."""

    def test_defaults(self) -> None:
        """Test default configuration."""
        config = OCRConfig()
        assert config.min_confidence == 0.3
        assert config.use_gpu is False
        assert config.language == "en"
        assert config.fallback_enabled is True
        assert config.dpi == 300

    def test_custom_values(self) -> None:
        """Test custom configuration."""
        config = OCRConfig(
            min_confidence=0.5,
            use_gpu=True,
            language="ch",
            dpi=600,
        )
        assert config.min_confidence == 0.5
        assert config.use_gpu is True
        assert config.language == "ch"
        assert config.dpi == 600


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_filter_by_confidence(self) -> None:
        """Test filtering results by confidence."""
        results = [
            OCRResult(text="High conf", confidence=0.9),
            OCRResult(text="Low conf", confidence=0.3),
            OCRResult(text="Medium conf", confidence=0.6),
        ]
        filtered = filter_by_confidence(results, min_confidence=0.5)
        assert len(filtered) == 2
        assert all(r.confidence >= 0.5 for r in filtered)

    def test_filter_by_confidence_empty(self) -> None:
        """Test filtering empty list."""
        filtered = filter_by_confidence([], min_confidence=0.5)
        assert filtered == []

    def test_calculate_weighted_confidence(self) -> None:
        """Test weighted confidence calculation."""
        results = [
            OCRResult(text="Short", confidence=0.5),
            OCRResult(text="Much longer text here", confidence=0.9),
        ]
        weighted = calculate_weighted_confidence(results)
        # Longer text should have more weight
        assert weighted > 0.7

    def test_calculate_weighted_confidence_empty(self) -> None:
        """Test weighted confidence with empty list."""
        assert calculate_weighted_confidence([]) == 0.0


class TestOCREngineCreation:
    """Tests for OCR engine creation."""

    def test_get_available_engine(self) -> None:
        """Test getting available engine."""
        engine = get_available_engine()
        if PADDLEOCR_AVAILABLE or EASYOCR_AVAILABLE:
            assert engine is not None
        else:
            assert engine is None

    @pytest.mark.skipif(
        not PADDLEOCR_AVAILABLE and not EASYOCR_AVAILABLE,
        reason="No OCR engine available",
    )
    def test_create_ocr_engine_auto(self) -> None:
        """Test auto engine creation."""
        engine = create_ocr_engine("auto")
        assert engine is not None

    @pytest.mark.skipif(not PADDLEOCR_AVAILABLE, reason="PaddleOCR not installed")
    def test_create_ocr_engine_paddleocr(self) -> None:
        """Test PaddleOCR engine creation."""
        engine = create_ocr_engine("paddleocr")
        assert engine.name == "PaddleOCR"

    @pytest.mark.skipif(not EASYOCR_AVAILABLE, reason="EasyOCR not installed")
    def test_create_ocr_engine_easyocr(self) -> None:
        """Test EasyOCR engine creation."""
        engine = create_ocr_engine("easyocr")
        assert engine.name == "EasyOCR"

    def test_create_ocr_engine_unknown(self) -> None:
        """Test unknown engine raises error."""
        with pytest.raises(ValueError, match="Unknown OCR engine"):
            create_ocr_engine("unknown_engine")

    @pytest.mark.skipif(
        PADDLEOCR_AVAILABLE or EASYOCR_AVAILABLE,
        reason="OCR engine is available",
    )
    def test_create_ocr_engine_none_available(self) -> None:
        """Test error when no engine available."""
        with pytest.raises(DependencyError):
            create_ocr_engine("auto")


class TestPaddleOCREngine:
    """Tests for PaddleOCR engine."""

    @pytest.mark.skipif(not PADDLEOCR_AVAILABLE, reason="PaddleOCR not installed")
    def test_init(self) -> None:
        """Test engine initialisation."""
        from ragd.ocr import PaddleOCREngine

        engine = PaddleOCREngine()
        assert engine.name == "PaddleOCR"
        assert engine.supports_gpu is True

    @pytest.mark.skipif(PADDLEOCR_AVAILABLE, reason="PaddleOCR is installed")
    def test_init_not_installed(self) -> None:
        """Test error when PaddleOCR not installed."""
        from ragd.ocr import PaddleOCREngine

        with pytest.raises(DependencyError):
            PaddleOCREngine()


class TestEasyOCREngine:
    """Tests for EasyOCR engine."""

    @pytest.mark.skipif(not EASYOCR_AVAILABLE, reason="EasyOCR not installed")
    def test_init(self) -> None:
        """Test engine initialisation."""
        from ragd.ocr import EasyOCREngine

        engine = EasyOCREngine()
        assert engine.name == "EasyOCR"
        assert engine.supports_gpu is True

    @pytest.mark.skipif(EASYOCR_AVAILABLE, reason="EasyOCR is installed")
    def test_init_not_installed(self) -> None:
        """Test error when EasyOCR not installed."""
        from ragd.ocr import EasyOCREngine

        with pytest.raises(DependencyError):
            EasyOCREngine()


class TestOCRPipeline:
    """Tests for OCR pipeline."""

    @pytest.mark.skipif(
        not PADDLEOCR_AVAILABLE and not EASYOCR_AVAILABLE,
        reason="No OCR engine available",
    )
    def test_init(self) -> None:
        """Test pipeline initialisation."""
        from ragd.ocr import OCRPipeline

        pipeline = OCRPipeline()
        assert pipeline.primary_engine in ["PaddleOCR", "EasyOCR"]

    @pytest.mark.skipif(
        not PADDLEOCR_AVAILABLE and not EASYOCR_AVAILABLE,
        reason="No OCR engine available",
    )
    def test_get_available_engines(self) -> None:
        """Test getting available engines."""
        from ragd.ocr import OCRPipeline

        pipeline = OCRPipeline()
        engines = pipeline.get_available_engines()
        assert len(engines) > 0

    @pytest.mark.skipif(
        PADDLEOCR_AVAILABLE or EASYOCR_AVAILABLE,
        reason="OCR engine is available",
    )
    def test_init_no_engine(self) -> None:
        """Test error when no engine available."""
        from ragd.ocr import OCRPipeline

        with pytest.raises(DependencyError):
            OCRPipeline()

    @pytest.fixture
    def sample_pdf(self, tmp_path: Path) -> Path:
        """Create a sample PDF for testing."""
        pdf_path = tmp_path / "sample.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Sample text for OCR testing", fontsize=12)
        doc.save(str(pdf_path))
        doc.close()
        return pdf_path

    @pytest.mark.skipif(
        not PADDLEOCR_AVAILABLE and not EASYOCR_AVAILABLE,
        reason="No OCR engine available",
    )
    def test_process_nonexistent_pdf(self) -> None:
        """Test processing non-existent PDF raises error."""
        from ragd.ocr import OCRPipeline

        pipeline = OCRPipeline()
        with pytest.raises(FileNotFoundError):
            pipeline.process_pdf(Path("/nonexistent/file.pdf"))
