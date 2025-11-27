"""Tests for vision pipeline module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ragd.config import MultiModalConfig, RagdConfig
from ragd.vision.pipeline import (
    ImageIndexResult,
    index_images_from_pdf,
    index_standalone_image,
)


class TestImageIndexResult:
    """Tests for ImageIndexResult dataclass."""

    def test_success_result(self) -> None:
        """Test successful result."""
        result = ImageIndexResult(
            document_id="doc_123",
            image_count=5,
            success=True,
            image_ids=["img_1", "img_2", "img_3", "img_4", "img_5"],
        )
        assert result.success is True
        assert result.image_count == 5
        assert len(result.image_ids or []) == 5

    def test_failure_result(self) -> None:
        """Test failure result."""
        result = ImageIndexResult(
            document_id="doc_123",
            image_count=0,
            success=False,
            error="Failed to extract images",
        )
        assert result.success is False
        assert result.error is not None

    def test_skipped_result(self) -> None:
        """Test result with skipped images."""
        result = ImageIndexResult(
            document_id="doc_123",
            image_count=3,
            success=True,
            skipped_count=2,
        )
        assert result.skipped_count == 2


class TestIndexImagesFromPdf:
    """Tests for index_images_from_pdf function."""

    @pytest.fixture
    def mock_config(self, tmp_path: Path) -> RagdConfig:
        """Create a mock config with multi-modal enabled."""
        config = RagdConfig()
        config.storage.data_dir = tmp_path
        config.multi_modal = MultiModalConfig(
            enabled=True,
            vision_model="vidore/colpali-v1.0",
            vision_dimension=128,
            min_image_width=50,
            min_image_height=50,
        )
        return config

    @pytest.fixture
    def mock_config_disabled(self, tmp_path: Path) -> RagdConfig:
        """Create a mock config with multi-modal disabled."""
        config = RagdConfig()
        config.storage.data_dir = tmp_path
        config.multi_modal = MultiModalConfig(enabled=False)
        return config

    def test_disabled_config_returns_early(
        self,
        mock_config_disabled: RagdConfig,
        tmp_path: Path,
    ) -> None:
        """Test that disabled config returns immediately."""
        from ragd.storage.images import ImageStore

        store = ImageStore(tmp_path / "chroma")
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        result = index_images_from_pdf(
            pdf_path,
            document_id="doc_123",
            store=store,
            config=mock_config_disabled,
        )

        assert result.success is True
        assert result.image_count == 0
        assert "disabled" in (result.error or "").lower()

    @patch("ragd.vision.pipeline.check_image_extraction_available")
    def test_missing_dependencies_returns_error(
        self,
        mock_check: MagicMock,
        mock_config: RagdConfig,
        tmp_path: Path,
    ) -> None:
        """Test missing dependencies returns error."""
        from ragd.storage.images import ImageStore

        mock_check.return_value = (False, "PyMuPDF not installed")

        store = ImageStore(tmp_path / "chroma")
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        result = index_images_from_pdf(
            pdf_path,
            document_id="doc_123",
            store=store,
            config=mock_config,
        )

        assert result.success is False
        assert "PyMuPDF" in (result.error or "")

    @patch("ragd.vision.pipeline.extract_images_from_pdf")
    @patch("ragd.vision.pipeline.check_image_extraction_available")
    def test_no_images_returns_empty(
        self,
        mock_check: MagicMock,
        mock_extract: MagicMock,
        mock_config: RagdConfig,
        tmp_path: Path,
    ) -> None:
        """Test PDF with no images returns empty result."""
        from ragd.storage.images import ImageStore

        mock_check.return_value = (True, "OK")
        mock_extract.return_value = []

        store = ImageStore(tmp_path / "chroma")
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        result = index_images_from_pdf(
            pdf_path,
            document_id="doc_123",
            store=store,
            config=mock_config,
        )

        assert result.success is True
        assert result.image_count == 0

    @patch("ragd.vision.pipeline.create_vision_embedder")
    @patch("ragd.vision.pipeline.extract_images_from_pdf")
    @patch("ragd.vision.pipeline.check_image_extraction_available")
    def test_no_embedder_returns_error(
        self,
        mock_check: MagicMock,
        mock_extract: MagicMock,
        mock_embedder: MagicMock,
        mock_config: RagdConfig,
        tmp_path: Path,
    ) -> None:
        """Test missing embedder returns error."""
        from ragd.storage.images import ImageStore
        from ragd.vision.image import ExtractedImage, ImageMetadata

        mock_check.return_value = (True, "OK")
        mock_extract.return_value = [
            ExtractedImage(
                data=b"fake image",
                metadata=ImageMetadata(100, 100, "png", 100),
            )
        ]
        mock_embedder.return_value = None

        store = ImageStore(tmp_path / "chroma")
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        result = index_images_from_pdf(
            pdf_path,
            document_id="doc_123",
            store=store,
            config=mock_config,
        )

        assert result.success is False
        assert "embedder" in (result.error or "").lower()


class TestIndexStandaloneImage:
    """Tests for index_standalone_image function."""

    @pytest.fixture
    def mock_config(self, tmp_path: Path) -> RagdConfig:
        """Create a mock config with multi-modal enabled."""
        config = RagdConfig()
        config.storage.data_dir = tmp_path
        config.multi_modal = MultiModalConfig(
            enabled=True,
            vision_model="vidore/colpali-v1.0",
            vision_dimension=128,
            min_image_width=50,
            min_image_height=50,
        )
        return config

    @pytest.fixture
    def mock_config_disabled(self, tmp_path: Path) -> RagdConfig:
        """Create config with multi-modal disabled."""
        config = RagdConfig()
        config.storage.data_dir = tmp_path
        config.multi_modal = MultiModalConfig(enabled=False)
        return config

    def test_disabled_config_returns_early(
        self,
        mock_config_disabled: RagdConfig,
        tmp_path: Path,
    ) -> None:
        """Test that disabled config returns immediately."""
        from ragd.storage.images import ImageStore

        store = ImageStore(tmp_path / "chroma")
        image_path = tmp_path / "test.png"
        image_path.touch()

        result = index_standalone_image(
            image_path,
            store=store,
            config=mock_config_disabled,
        )

        assert result.success is True
        assert result.image_count == 0
        assert "disabled" in (result.error or "").lower()

    @patch("ragd.vision.pipeline.load_image_file")
    def test_load_failure_returns_error(
        self,
        mock_load: MagicMock,
        mock_config: RagdConfig,
        tmp_path: Path,
    ) -> None:
        """Test load failure returns error."""
        from ragd.storage.images import ImageStore

        mock_load.side_effect = FileNotFoundError("File not found")

        store = ImageStore(tmp_path / "chroma")
        image_path = tmp_path / "missing.png"

        result = index_standalone_image(
            image_path,
            store=store,
            config=mock_config,
        )

        assert result.success is False
        assert "not found" in (result.error or "").lower()

    @patch("ragd.vision.pipeline.load_image_file")
    def test_small_image_filtered(
        self,
        mock_load: MagicMock,
        mock_config: RagdConfig,
        tmp_path: Path,
    ) -> None:
        """Test small images are filtered out."""
        from ragd.storage.images import ImageStore
        from ragd.vision.image import ExtractedImage, ImageMetadata

        # Image smaller than min size (50x50)
        mock_load.return_value = ExtractedImage(
            data=b"tiny",
            metadata=ImageMetadata(30, 30, "png", 10),
        )

        store = ImageStore(tmp_path / "chroma")
        image_path = tmp_path / "tiny.png"
        image_path.touch()

        result = index_standalone_image(
            image_path,
            store=store,
            config=mock_config,
        )

        assert result.success is True
        assert result.image_count == 0
        assert result.skipped_count == 1
        assert "small" in (result.error or "").lower()


class TestPipelineIntegration:
    """Integration tests for the vision pipeline."""

    @patch("ragd.vision.pipeline.create_vision_embedder")
    @patch("ragd.vision.pipeline.extract_images_from_pdf")
    @patch("ragd.vision.pipeline.check_image_extraction_available")
    def test_full_pdf_pipeline_with_mocks(
        self,
        mock_check: MagicMock,
        mock_extract: MagicMock,
        mock_embedder_factory: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test full pipeline with mocked dependencies."""
        from ragd.storage.images import ImageStore
        from ragd.vision.image import ExtractedImage, ImageMetadata

        # Setup mocks
        mock_check.return_value = (True, "OK")
        mock_extract.return_value = [
            ExtractedImage(
                data=b"image1 data",
                metadata=ImageMetadata(200, 150, "png", 1000, page_number=1),
            ),
            ExtractedImage(
                data=b"image2 data",
                metadata=ImageMetadata(300, 200, "jpeg", 2000, page_number=2),
            ),
        ]

        # Create mock embedder
        mock_embedder = MagicMock()
        mock_embedder.embed_image.return_value = [0.1] * 128
        mock_embedder.model_name = "test-model"
        mock_embedder.dimension = 128
        mock_embedder_factory.return_value = mock_embedder

        # Create config
        config = RagdConfig()
        config.storage.data_dir = tmp_path
        config.multi_modal = MultiModalConfig(
            enabled=True,
            vision_dimension=128,
        )

        store = ImageStore(tmp_path / "chroma")
        pdf_path = tmp_path / "test.pdf"
        pdf_path.touch()

        result = index_images_from_pdf(
            pdf_path,
            document_id="doc_test",
            store=store,
            config=config,
            embedder=mock_embedder,
        )

        assert result.success is True
        assert result.image_count == 2
        assert len(result.image_ids or []) == 2

        # Verify images are in store
        images = store.get_images_for_document("doc_test")
        assert len(images) == 2


class TestStandaloneImageOCR:
    """Tests for OCR in standalone image indexing."""

    @pytest.fixture
    def mock_config(self, tmp_path: Path) -> RagdConfig:
        """Create a mock config."""
        config = RagdConfig()
        config.storage.data_dir = tmp_path
        config.multi_modal = MultiModalConfig(
            enabled=True,
            vision_dimension=128,
        )
        return config

    @patch("ragd.vision.pipeline.create_vision_embedder")
    @patch("ragd.vision.pipeline.load_image_file")
    def test_index_with_ocr_disabled(
        self,
        mock_load: MagicMock,
        mock_embedder_factory: MagicMock,
        mock_config: RagdConfig,
        tmp_path: Path,
    ) -> None:
        """Test indexing without OCR."""
        from ragd.storage.images import ImageStore
        from ragd.vision.image import ExtractedImage, ImageMetadata

        # Setup mocks
        mock_load.return_value = ExtractedImage(
            data=b"test image",
            metadata=ImageMetadata(200, 150, "png", 100),
        )

        mock_embedder = MagicMock()
        mock_embedder.embed_image.return_value = [0.1] * 128
        mock_embedder.model_name = "test-model"
        mock_embedder.dimension = 128
        mock_embedder_factory.return_value = mock_embedder

        store = ImageStore(tmp_path / "chroma")
        image_path = tmp_path / "test.png"
        image_path.touch()

        result = index_standalone_image(
            image_path,
            store=store,
            config=mock_config,
            embedder=mock_embedder,
            perform_ocr=False,
        )

        assert result.success is True
        assert result.ocr_text is None
        assert result.ocr_confidence == 0.0

    @patch("ragd.vision.image.ocr_image_file")
    @patch("ragd.vision.image.check_ocr_available")
    @patch("ragd.vision.pipeline.create_vision_embedder")
    @patch("ragd.vision.pipeline.load_image_file")
    def test_index_with_ocr_enabled(
        self,
        mock_load: MagicMock,
        mock_embedder_factory: MagicMock,
        mock_ocr_check: MagicMock,
        mock_ocr: MagicMock,
        mock_config: RagdConfig,
        tmp_path: Path,
    ) -> None:
        """Test indexing with OCR."""
        from ragd.storage.images import ImageStore
        from ragd.vision.image import ExtractedImage, ImageMetadata

        # Setup mocks
        mock_load.return_value = ExtractedImage(
            data=b"test image",
            metadata=ImageMetadata(200, 150, "png", 100),
        )

        mock_embedder = MagicMock()
        mock_embedder.embed_image.return_value = [0.1] * 128
        mock_embedder.model_name = "test-model"
        mock_embedder.dimension = 128
        mock_embedder_factory.return_value = mock_embedder

        mock_ocr_check.return_value = (True, "OK")
        mock_ocr.return_value = ("Extracted text content", 0.95)

        store = ImageStore(tmp_path / "chroma")
        image_path = tmp_path / "test.png"
        image_path.touch()

        result = index_standalone_image(
            image_path,
            store=store,
            config=mock_config,
            embedder=mock_embedder,
            perform_ocr=True,
        )

        assert result.success is True
        assert result.ocr_text == "Extracted text content"
        assert result.ocr_confidence == 0.95
