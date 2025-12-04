"""Tests for PDF layout intelligence (F-099)."""

import tempfile
from pathlib import Path

import pytest
import fitz  # PyMuPDF

from ragd.ingestion.pdf_layout import (
    LayoutConfig,
    LayoutRegion,
    PageLayout,
    PDFLayoutExtractor,
    analyse_pdf_layout,
    detect_columns,
    reorder_by_reading_order,
)


class TestLayoutConfig:
    """Tests for LayoutConfig."""

    def test_default_config(self):
        """Should have sensible defaults."""
        config = LayoutConfig()
        assert config.layout_analysis is True
        assert config.extract_forms is True
        assert config.extract_annotations is True
        assert config.preserve_tables is True

    def test_custom_config(self):
        """Should accept custom values."""
        config = LayoutConfig(
            layout_analysis=False,
            extract_forms=False,
        )
        assert config.layout_analysis is False
        assert config.extract_forms is False


class TestLayoutRegion:
    """Tests for LayoutRegion."""

    def test_create_region(self):
        """Should create a region."""
        region = LayoutRegion(
            x0=0, y0=0, x1=100, y1=50,
            text="Test content",
            region_type="text",
        )
        assert region.width == 100
        assert region.height == 50
        assert region.center_x == 50


class TestPageLayout:
    """Tests for PageLayout."""

    def test_create_page_layout(self):
        """Should create page layout."""
        layout = PageLayout(
            page_number=1,
            width=612,
            height=792,
        )
        assert layout.page_number == 1
        assert layout.columns == 1
        assert layout.has_tables is False


class TestColumnDetection:
    """Tests for column detection."""

    def test_single_column(self):
        """Should detect single column."""
        blocks = [
            {"bbox": (50, 100, 550, 200)},
            {"bbox": (50, 220, 550, 320)},
            {"bbox": (50, 340, 550, 440)},
        ]
        columns = detect_columns(blocks, 612)
        assert columns == 1

    def test_two_columns(self):
        """Should detect two columns."""
        blocks = [
            # Left column
            {"bbox": (50, 100, 250, 200)},
            {"bbox": (50, 220, 250, 320)},
            # Right column
            {"bbox": (350, 100, 550, 200)},
            {"bbox": (350, 220, 550, 320)},
        ]
        columns = detect_columns(blocks, 612)
        assert columns == 2

    def test_empty_blocks(self):
        """Should handle empty blocks."""
        columns = detect_columns([], 612)
        assert columns == 1


class TestReadingOrder:
    """Tests for reading order reordering."""

    def test_single_column_order(self):
        """Should order single column top-to-bottom."""
        blocks = [
            {"bbox": (50, 300, 200, 400)},
            {"bbox": (50, 100, 200, 200)},
            {"bbox": (50, 500, 200, 600)},
        ]
        reordered = reorder_by_reading_order(blocks, 1)
        # Should be sorted by y-coordinate
        assert reordered[0]["bbox"][1] == 100
        assert reordered[1]["bbox"][1] == 300
        assert reordered[2]["bbox"][1] == 500

    def test_two_column_order(self):
        """Should read left column then right column."""
        blocks = [
            # Right column first (to test reordering)
            {"bbox": (400, 100, 550, 200)},
            {"bbox": (400, 300, 550, 400)},
            # Left column
            {"bbox": (50, 100, 200, 200)},
            {"bbox": (50, 300, 200, 400)},
        ]
        reordered = reorder_by_reading_order(blocks, 2)
        # Left column should come first
        assert reordered[0]["bbox"][0] == 50
        assert reordered[1]["bbox"][0] == 50
        # Then right column
        assert reordered[2]["bbox"][0] == 400
        assert reordered[3]["bbox"][0] == 400


class TestPDFLayoutExtractor:
    """Tests for PDFLayoutExtractor."""

    @pytest.fixture
    def simple_pdf(self):
        """Create a simple PDF file."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            doc = fitz.open()
            page = doc.new_page()

            # Add some text
            text_point = fitz.Point(72, 72)
            page.insert_text(text_point, "Hello World")
            page.insert_text(fitz.Point(72, 100), "This is test content.")

            doc.save(f.name)
            doc.close()
            path = Path(f.name)

        yield path
        path.unlink()

    def test_extract_simple_pdf(self, simple_pdf):
        """Should extract text from simple PDF."""
        extractor = PDFLayoutExtractor()
        result = extractor.extract(simple_pdf)

        assert result.success is True
        assert "Hello World" in result.text
        assert result.extraction_method == "pymupdf_layout"

    def test_extract_with_layout_disabled(self, simple_pdf):
        """Should work with layout analysis disabled."""
        config = LayoutConfig(layout_analysis=False)
        extractor = PDFLayoutExtractor(config=config)
        result = extractor.extract(simple_pdf)

        assert result.success is True
        assert len(result.text) > 0

    def test_extract_nonexistent_file(self):
        """Should handle nonexistent files."""
        extractor = PDFLayoutExtractor()
        result = extractor.extract(Path("/nonexistent/file.pdf"))

        assert result.success is False
        assert result.error is not None

    def test_metadata_includes_layout_info(self, simple_pdf):
        """Should include layout info in metadata."""
        extractor = PDFLayoutExtractor()
        result = extractor.extract(simple_pdf)

        assert result.success is True
        assert "pages" in result.metadata
        assert "columns_detected" in result.metadata


class TestAnalysePDFLayout:
    """Tests for analyse_pdf_layout function."""

    @pytest.fixture
    def multi_page_pdf(self):
        """Create a multi-page PDF."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            doc = fitz.open()

            # Page 1
            page1 = doc.new_page()
            page1.insert_text(fitz.Point(72, 72), "Page One Content")

            # Page 2
            page2 = doc.new_page()
            page2.insert_text(fitz.Point(72, 72), "Page Two Content")

            doc.save(f.name)
            doc.close()
            path = Path(f.name)

        yield path
        path.unlink()

    def test_analyse_multi_page(self, multi_page_pdf):
        """Should analyse multiple pages."""
        result = analyse_pdf_layout(multi_page_pdf)

        assert result.success is True
        assert len(result.pages) == 2
        assert result.pages[0].page_number == 1
        assert result.pages[1].page_number == 2

    def test_analyse_returns_metadata(self, multi_page_pdf):
        """Should return comprehensive metadata."""
        result = analyse_pdf_layout(multi_page_pdf)

        assert result.success is True
        assert result.metadata["pages"] == 2
        assert "columns_detected" in result.metadata
        assert "has_forms" in result.metadata
        assert "has_annotations" in result.metadata
