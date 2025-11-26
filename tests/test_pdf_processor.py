"""Tests for PDF processor module."""

from __future__ import annotations

import tempfile
from pathlib import Path

import fitz
import pytest

from ragd.features import DOCLING_AVAILABLE, DependencyError, FeatureDetector
from ragd.pdf import (
    ExtractedContent,
    ExtractedTable,
    PDFPipelineFactory,
    PyMuPDFProcessor,
    extract_pdf,
)


class TestExtractedTable:
    """Tests for ExtractedTable dataclass."""

    def test_creation(self) -> None:
        """Test creating an ExtractedTable."""
        table = ExtractedTable(
            page_number=1,
            table_index=0,
            markdown="| A | B |\n|---|---|\n| 1 | 2 |",
            rows=2,
            cols=2,
            confidence=0.95,
        )
        assert table.page_number == 1
        assert table.rows == 2
        assert table.cols == 2

    def test_str_representation(self) -> None:
        """Test string representation."""
        table = ExtractedTable(
            page_number=1,
            table_index=0,
            markdown="",
            rows=3,
            cols=4,
        )
        result = str(table)
        assert "p1" in result
        assert "3x4" in result


class TestExtractedContent:
    """Tests for ExtractedContent dataclass."""

    def test_creation(self) -> None:
        """Test creating ExtractedContent."""
        content = ExtractedContent(
            text="Test content",
            pages=["Page 1", "Page 2"],
            processing_time_ms=100,
        )
        assert content.text == "Test content"
        assert content.page_count == 2
        assert content.table_count == 0

    def test_with_tables(self) -> None:
        """Test ExtractedContent with tables."""
        tables = [
            ExtractedTable(
                page_number=1,
                table_index=0,
                markdown="| A |",
                rows=1,
                cols=1,
            )
        ]
        content = ExtractedContent(text="", tables=tables)
        assert content.table_count == 1

    def test_str_representation(self) -> None:
        """Test string representation."""
        content = ExtractedContent(
            text="x" * 100,
            pages=["p1", "p2"],
            processing_time_ms=50,
        )
        result = str(content)
        assert "2 pages" in result
        assert "100 chars" in result
        assert "50ms" in result


class TestPyMuPDFProcessor:
    """Tests for PyMuPDFProcessor."""

    def test_init(self) -> None:
        """Test processor initialisation."""
        processor = PyMuPDFProcessor()
        assert processor.name == "PyMuPDF"
        assert processor.supports_tables is False
        assert processor.supports_layout is False

    def test_extract_nonexistent_file(self) -> None:
        """Test extracting from non-existent file raises error."""
        processor = PyMuPDFProcessor()
        with pytest.raises(FileNotFoundError):
            processor.extract(Path("/nonexistent/file.pdf"))

    def test_extract_non_pdf(self) -> None:
        """Test extracting from non-PDF file raises error."""
        processor = PyMuPDFProcessor()
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"Not a PDF")
            path = Path(f.name)
        try:
            with pytest.raises(ValueError, match="Not a PDF file"):
                processor.extract(path)
        finally:
            path.unlink()

    def test_extract_simple_pdf(self) -> None:
        """Test extracting from a simple PDF."""
        processor = PyMuPDFProcessor()

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((50, 50), "Hello World", fontsize=12)
            doc.save(f.name)
            doc.close()
            path = Path(f.name)

        try:
            content = processor.extract(path)
            assert content.success is True
            assert "Hello World" in content.text
            assert content.page_count == 1
            assert content.processor_name == "PyMuPDF"
            assert content.processing_time_ms >= 0  # Can be 0 for fast extractions
        finally:
            path.unlink()

    def test_extract_multipage_pdf(self) -> None:
        """Test extracting from multi-page PDF."""
        processor = PyMuPDFProcessor()

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            doc = fitz.open()
            for i in range(3):
                page = doc.new_page()
                page.insert_text((50, 50), f"Page {i + 1} content", fontsize=12)
            doc.save(f.name)
            doc.close()
            path = Path(f.name)

        try:
            content = processor.extract(path)
            assert content.success is True
            assert content.page_count == 3
            assert "Page 1" in content.pages[0]
            assert "Page 2" in content.pages[1]
            assert "Page 3" in content.pages[2]
        finally:
            path.unlink()

    def test_extract_pdf_with_metadata(self) -> None:
        """Test extracting PDF metadata."""
        processor = PyMuPDFProcessor()

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            doc = fitz.open()
            doc.set_metadata({
                "title": "Test Document",
                "author": "Test Author",
                "subject": "Test Subject",
            })
            page = doc.new_page()
            page.insert_text((50, 50), "Content", fontsize=12)
            doc.save(f.name)
            doc.close()
            path = Path(f.name)

        try:
            content = processor.extract(path)
            assert content.metadata.get("title") == "Test Document"
            assert content.metadata.get("author") == "Test Author"
        finally:
            path.unlink()

    def test_extract_corrupted_pdf(self) -> None:
        """Test extracting from corrupted PDF returns error."""
        processor = PyMuPDFProcessor()

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"Not a valid PDF content")
            path = Path(f.name)

        try:
            content = processor.extract(path)
            assert content.success is False
            assert content.error is not None
            assert "Cannot open PDF" in content.error
        finally:
            path.unlink()


class TestPDFPipelineFactory:
    """Tests for PDFPipelineFactory."""

    @pytest.fixture
    def factory(self) -> PDFPipelineFactory:
        """Create a pipeline factory."""
        return PDFPipelineFactory()

    @pytest.fixture
    def sample_pdf(self, tmp_path: Path) -> Path:
        """Create a sample PDF for testing."""
        pdf_path = tmp_path / "sample.pdf"
        doc = fitz.open()
        page = doc.new_page()
        text = "This is a test document with substantial content. " * 10
        page.insert_text((50, 50), text, fontsize=12)
        doc.save(str(pdf_path))
        doc.close()
        return pdf_path

    def test_get_processor_fast(self, factory: PDFPipelineFactory) -> None:
        """Test getting fast pipeline processor."""
        processor = factory._get_forced_processor("fast")
        assert isinstance(processor, PyMuPDFProcessor)

    def test_get_processor_nonexistent(self, factory: PDFPipelineFactory) -> None:
        """Test getting processor for non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            factory.get_processor(Path("/nonexistent/file.pdf"))

    def test_get_processor_auto(
        self,
        factory: PDFPipelineFactory,
        sample_pdf: Path,
    ) -> None:
        """Test automatic processor selection."""
        processor = factory.get_processor(sample_pdf)
        # Should select based on quality assessment
        assert processor is not None
        assert hasattr(processor, "extract")

    def test_force_pipeline_fast(
        self,
        factory: PDFPipelineFactory,
        sample_pdf: Path,
    ) -> None:
        """Test forcing fast pipeline."""
        processor = factory.get_processor(sample_pdf, force_pipeline="fast")
        assert isinstance(processor, PyMuPDFProcessor)

    @pytest.mark.skipif(not DOCLING_AVAILABLE, reason="Docling not installed")
    def test_force_pipeline_structure(
        self,
        factory: PDFPipelineFactory,
        sample_pdf: Path,
    ) -> None:
        """Test forcing structure pipeline (requires Docling)."""
        processor = factory.get_processor(sample_pdf, force_pipeline="structure")
        assert processor.name == "Docling"

    @pytest.mark.skipif(DOCLING_AVAILABLE, reason="Test for missing Docling")
    def test_force_structure_without_docling(
        self,
        factory: PDFPipelineFactory,
    ) -> None:
        """Test that forcing structure without Docling raises error."""
        with pytest.raises(DependencyError) as exc_info:
            factory._get_forced_processor("structure")
        assert "Docling" in str(exc_info.value)
        assert exc_info.value.install_command is not None

    def test_get_available_pipelines(self, factory: PDFPipelineFactory) -> None:
        """Test getting available pipelines."""
        available = factory.get_available_pipelines()
        assert "fast" in available  # Always available
        if DOCLING_AVAILABLE:
            assert "structure" in available

    def test_assess_and_extract(
        self,
        factory: PDFPipelineFactory,
        sample_pdf: Path,
    ) -> None:
        """Test combined assess and extract."""
        assessment, content = factory.assess_and_extract(sample_pdf)
        assert assessment is not None
        assert assessment.page_count == 1
        assert content is not None
        assert content.success is True


class TestExtractPDF:
    """Tests for extract_pdf convenience function."""

    def test_extract_pdf(self, tmp_path: Path) -> None:
        """Test extract_pdf convenience function."""
        pdf_path = tmp_path / "test.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Test content", fontsize=12)
        doc.save(str(pdf_path))
        doc.close()

        content = extract_pdf(pdf_path)
        assert content.success is True
        assert "Test content" in content.text

    def test_extract_pdf_force_fast(self, tmp_path: Path) -> None:
        """Test extract_pdf with forced pipeline."""
        pdf_path = tmp_path / "test.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Test", fontsize=12)
        doc.save(str(pdf_path))
        doc.close()

        content = extract_pdf(pdf_path, force_pipeline="fast")
        assert content.processor_name == "PyMuPDF"


class TestFeatureDetector:
    """Tests for FeatureDetector."""

    def test_feature_detector_creation(self) -> None:
        """Test creating feature detector."""
        detector = FeatureDetector()
        assert detector is not None

    def test_docling_status(self) -> None:
        """Test Docling feature status."""
        detector = FeatureDetector()
        status = detector.docling
        assert status.name == "Docling (PDF structure extraction)"
        assert status.available == DOCLING_AVAILABLE

    def test_all_features(self) -> None:
        """Test getting all features."""
        detector = FeatureDetector()
        features = detector.all_features()
        assert "docling" in features
        assert "ocr" in features
        assert "metadata" in features

    def test_available_features(self) -> None:
        """Test getting available features."""
        detector = FeatureDetector()
        available = detector.available_features()
        assert isinstance(available, list)

    def test_feature_status_bool(self) -> None:
        """Test FeatureStatus boolean conversion."""
        detector = FeatureDetector()
        # Should be able to use status in boolean context
        if detector.docling:
            assert detector.docling.available is True
        else:
            assert detector.docling.available is False


@pytest.mark.skipif(not DOCLING_AVAILABLE, reason="Docling not installed")
class TestDoclingProcessor:
    """Tests for DoclingProcessor (requires Docling)."""

    def test_import(self) -> None:
        """Test importing DoclingProcessor."""
        from ragd.pdf.docling import DoclingProcessor

        processor = DoclingProcessor()
        assert processor.name == "Docling"
        assert processor.supports_tables is True
        assert processor.supports_layout is True

    def test_extract_nonexistent(self) -> None:
        """Test extracting from non-existent file."""
        from ragd.pdf.docling import DoclingProcessor

        processor = DoclingProcessor()
        with pytest.raises(FileNotFoundError):
            processor.extract(Path("/nonexistent/file.pdf"))


class TestDoclingNotInstalled:
    """Tests for Docling when not installed."""

    @pytest.mark.skipif(DOCLING_AVAILABLE, reason="Docling is installed")
    def test_import_raises_error(self) -> None:
        """Test that creating DoclingProcessor raises error when not installed."""
        from ragd.pdf.docling import DoclingProcessor

        with pytest.raises(DependencyError) as exc_info:
            DoclingProcessor()
        assert "Docling" in str(exc_info.value)
        assert exc_info.value.install_command is not None
