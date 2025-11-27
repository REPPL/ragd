"""Tests for vision module."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ragd.vision.image import (
    ExtractedImage,
    ImageMetadata,
    check_image_extraction_available,
)


class TestImageMetadata:
    """Tests for ImageMetadata dataclass."""

    def test_default_values(self) -> None:
        """Test default values."""
        metadata = ImageMetadata(
            width=800,
            height=600,
            format="png",
            size_bytes=1024,
        )
        assert metadata.width == 800
        assert metadata.height == 600
        assert metadata.format == "png"
        assert metadata.size_bytes == 1024
        assert metadata.page_number is None
        assert metadata.colorspace == ""
        assert metadata.bits_per_component == 8

    def test_with_page_number(self) -> None:
        """Test with page number."""
        metadata = ImageMetadata(
            width=100,
            height=100,
            format="jpeg",
            size_bytes=512,
            page_number=3,
            xref=42,
        )
        assert metadata.page_number == 3
        assert metadata.xref == 42


class TestExtractedImage:
    """Tests for ExtractedImage dataclass."""

    def test_auto_generates_image_id(self) -> None:
        """Test that image_id is auto-generated from content hash."""
        image1 = ExtractedImage(
            data=b"test image data",
            metadata=ImageMetadata(100, 100, "png", 15),
        )
        image2 = ExtractedImage(
            data=b"test image data",
            metadata=ImageMetadata(100, 100, "png", 15),
        )
        image3 = ExtractedImage(
            data=b"different data",
            metadata=ImageMetadata(100, 100, "png", 14),
        )

        # Same data should produce same ID
        assert image1.image_id == image2.image_id
        # Different data should produce different ID
        assert image1.image_id != image3.image_id

    def test_aspect_ratio(self) -> None:
        """Test aspect ratio calculation."""
        # Landscape
        landscape = ExtractedImage(
            data=b"data",
            metadata=ImageMetadata(800, 600, "png", 10),
        )
        assert landscape.aspect_ratio == pytest.approx(800 / 600)
        assert landscape.is_landscape is True

        # Portrait
        portrait = ExtractedImage(
            data=b"data2",
            metadata=ImageMetadata(600, 800, "png", 10),
        )
        assert portrait.aspect_ratio == pytest.approx(600 / 800)
        assert portrait.is_landscape is False

        # Square
        square = ExtractedImage(
            data=b"data3",
            metadata=ImageMetadata(500, 500, "png", 10),
        )
        assert square.aspect_ratio == 1.0
        assert square.is_landscape is False  # width == height, not > height

    def test_megapixels(self) -> None:
        """Test megapixels calculation."""
        image = ExtractedImage(
            data=b"data",
            metadata=ImageMetadata(2000, 1500, "png", 100),
        )
        assert image.megapixels == 3.0

    def test_save_image(self, tmp_path: Path) -> None:
        """Test saving image to file."""
        image = ExtractedImage(
            data=b"PNG image data here",
            metadata=ImageMetadata(100, 100, "png", 18),
        )

        output_path = tmp_path / "subdir" / "test.png"
        image.save(output_path)

        assert output_path.exists()
        assert output_path.read_bytes() == b"PNG image data here"


class TestColPaliEmbedder:
    """Tests for ColPaliEmbedder."""

    def test_known_models_defined(self) -> None:
        """Test that known models are defined."""
        from ragd.vision.embedder import ColPaliEmbedder

        models = ColPaliEmbedder.KNOWN_MODELS
        assert "vidore/colpali-v1.0" in models
        assert "vidore/colqwen2-v1.0" in models

    def test_init_with_defaults(self) -> None:
        """Test initialisation with defaults."""
        from ragd.vision.embedder import ColPaliEmbedder

        embedder = ColPaliEmbedder()
        assert embedder.model_name == "vidore/colpali-v1.0"
        assert embedder.dimension == 128

    def test_init_with_custom_model(self) -> None:
        """Test initialisation with custom model."""
        from ragd.vision.embedder import ColPaliEmbedder

        embedder = ColPaliEmbedder(model_name="vidore/colqwen2-v1.0", device="cpu")
        assert embedder.model_name == "vidore/colqwen2-v1.0"
        assert embedder.dimension == 128

    @patch("ragd.vision.embedder.ColPaliEmbedder._ensure_model")
    def test_embed_images_empty_list(self, mock_ensure: MagicMock) -> None:
        """Test embedding empty list returns empty list."""
        from ragd.vision.embedder import ColPaliEmbedder

        embedder = ColPaliEmbedder()
        result = embedder.embed_images([])
        assert result == []

    @patch("ragd.vision.embedder.ColPaliEmbedder._ensure_model")
    def test_embed_texts_empty_list(self, mock_ensure: MagicMock) -> None:
        """Test embedding empty text list returns empty list."""
        from ragd.vision.embedder import ColPaliEmbedder

        embedder = ColPaliEmbedder()
        result = embedder.embed_texts_for_image_search([])
        assert result == []


class TestVisionAvailability:
    """Tests for availability checks."""

    def test_check_vision_available_structure(self) -> None:
        """Test check_vision_available returns correct structure."""
        from ragd.vision.embedder import check_vision_available

        available, message = check_vision_available()
        assert isinstance(available, bool)
        assert isinstance(message, str)

    def test_check_image_extraction_available_structure(self) -> None:
        """Test check_image_extraction_available returns correct structure."""
        available, message = check_image_extraction_available()
        assert isinstance(available, bool)
        assert isinstance(message, str)

    @patch.dict("sys.modules", {"colpali_engine": None})
    def test_create_vision_embedder_returns_none_when_unavailable(self) -> None:
        """Test create_vision_embedder returns None when deps missing."""
        from ragd.vision.embedder import create_vision_embedder

        with patch("ragd.vision.embedder.check_vision_available") as mock_check:
            mock_check.return_value = (False, "Missing dependency")
            result = create_vision_embedder()
            assert result is None


class TestMultiModalConfig:
    """Tests for MultiModalConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        from ragd.config import MultiModalConfig

        config = MultiModalConfig()
        assert config.enabled is False
        assert config.vision_model == "vidore/colpali-v1.0"
        assert config.vision_dimension == 128
        assert config.extract_images is True
        assert config.min_image_width == 100
        assert config.min_image_height == 100
        assert config.generate_captions is False

    def test_ragd_config_includes_multi_modal(self) -> None:
        """Test RagdConfig includes multi_modal."""
        from ragd.config import RagdConfig

        config = RagdConfig()
        assert hasattr(config, "multi_modal")
        assert config.multi_modal.enabled is False

    def test_images_path_property(self) -> None:
        """Test images_path property."""
        from ragd.config import RagdConfig

        config = RagdConfig()
        assert config.images_path == config.storage.data_dir / "images"


class TestImageExtractionWithPyMuPDF:
    """Tests for image extraction (skip if PyMuPDF not available)."""

    @pytest.fixture
    def sample_pdf_with_image(self, tmp_path: Path) -> Path | None:
        """Create a sample PDF with an embedded image.

        Returns None if PyMuPDF is not available.
        """
        try:
            import fitz
        except ImportError:
            pytest.skip("PyMuPDF not installed")

        # Create a simple PDF with a small image
        doc = fitz.open()
        page = doc.new_page()

        # Create a simple colored rectangle as "image"
        rect = fitz.Rect(100, 100, 300, 200)
        page.draw_rect(rect, color=(1, 0, 0), fill=(0, 0, 1))

        pdf_path = tmp_path / "test.pdf"
        doc.save(pdf_path)
        doc.close()

        return pdf_path

    def test_extract_images_from_pdf_file_not_found(self, tmp_path: Path) -> None:
        """Test extraction from non-existent file raises error."""
        from ragd.vision.image import extract_images_from_pdf

        try:
            import fitz
        except ImportError:
            pytest.skip("PyMuPDF not installed")

        with pytest.raises(FileNotFoundError):
            extract_images_from_pdf(tmp_path / "nonexistent.pdf")


class TestOCRFunctions:
    """Tests for OCR functions."""

    def test_check_ocr_available_structure(self) -> None:
        """Test check_ocr_available returns correct structure."""
        from ragd.vision.image import check_ocr_available

        available, message = check_ocr_available()
        assert isinstance(available, bool)
        assert isinstance(message, str)

    def test_ocr_image_file_not_found(self, tmp_path: Path) -> None:
        """Test OCR raises FileNotFoundError for missing file."""
        from ragd.vision.image import check_ocr_available, ocr_image_file

        available, _ = check_ocr_available()
        if not available:
            pytest.skip("OCR dependencies not installed")

        with pytest.raises(FileNotFoundError):
            ocr_image_file(tmp_path / "nonexistent.png")


class TestVisionModuleImports:
    """Tests for module imports."""

    def test_vision_module_imports(self) -> None:
        """Test vision module can be imported."""
        from ragd import vision

        assert hasattr(vision, "ColPaliEmbedder")
        assert hasattr(vision, "VisionEmbedder")
        assert hasattr(vision, "ExtractedImage")
        assert hasattr(vision, "ImageMetadata")

    def test_ocr_exports(self) -> None:
        """Test OCR functions are exported."""
        from ragd import vision

        assert hasattr(vision, "check_ocr_available")
        assert hasattr(vision, "ocr_image_file")
        assert hasattr(vision, "ocr_image_bytes")

    def test_embedder_submodule_imports(self) -> None:
        """Test embedder submodule imports."""
        from ragd.vision.embedder import (
            ColPaliEmbedder,
            VisionEmbedder,
            check_vision_available,
            create_vision_embedder,
        )

        assert ColPaliEmbedder is not None
        assert VisionEmbedder is not None
        assert callable(check_vision_available)
        assert callable(create_vision_embedder)

    def test_image_submodule_imports(self) -> None:
        """Test image submodule imports."""
        from ragd.vision.image import (
            ExtractedImage,
            ImageMetadata,
            check_image_extraction_available,
        )

        assert ExtractedImage is not None
        assert ImageMetadata is not None
        assert callable(check_image_extraction_available)
