"""Tests for multi-modal search module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ragd.config import MultiModalConfig, RagdConfig
from ragd.search.multimodal import (
    ImageSearchResult,
    check_multimodal_search_available,
    search_images,
    search_images_by_bytes,
    search_similar_images,
)


class TestImageSearchResult:
    """Tests for ImageSearchResult dataclass."""

    def test_basic_result(self) -> None:
        """Test basic result creation."""
        result = ImageSearchResult(
            image_id="img_123",
            score=0.95,
            document_id="doc_abc",
            source_path="/path/to/doc.pdf",
            width=800,
            height=600,
            format="png",
        )
        assert result.image_id == "img_123"
        assert result.score == 0.95
        assert result.document_id == "doc_abc"

    def test_aspect_ratio_landscape(self) -> None:
        """Test aspect ratio for landscape image."""
        result = ImageSearchResult(
            image_id="img_1",
            score=0.9,
            document_id="doc_1",
            source_path="/path",
            width=800,
            height=600,
            format="png",
        )
        assert result.aspect_ratio == pytest.approx(800 / 600)
        assert result.is_landscape is True

    def test_aspect_ratio_portrait(self) -> None:
        """Test aspect ratio for portrait image."""
        result = ImageSearchResult(
            image_id="img_1",
            score=0.9,
            document_id="doc_1",
            source_path="/path",
            width=600,
            height=800,
            format="png",
        )
        assert result.aspect_ratio == pytest.approx(600 / 800)
        assert result.is_landscape is False

    def test_aspect_ratio_zero_height(self) -> None:
        """Test aspect ratio with zero height."""
        result = ImageSearchResult(
            image_id="img_1",
            score=0.9,
            document_id="doc_1",
            source_path="/path",
            width=100,
            height=0,
            format="png",
        )
        assert result.aspect_ratio == 0.0

    def test_optional_fields(self) -> None:
        """Test optional fields."""
        result = ImageSearchResult(
            image_id="img_1",
            score=0.9,
            document_id="doc_1",
            source_path="/path",
            width=100,
            height=100,
            format="png",
            page_number=5,
            caption="A test image",
            ocr_text="Extracted text",
        )
        assert result.page_number == 5
        assert result.caption == "A test image"
        assert result.ocr_text == "Extracted text"


class TestSearchImages:
    """Tests for search_images function."""

    @pytest.fixture
    def mock_config_disabled(self, tmp_path: Path) -> RagdConfig:
        """Create config with multi-modal disabled."""
        config = RagdConfig()
        config.storage.data_dir = tmp_path
        config.multi_modal = MultiModalConfig(enabled=False)
        return config

    @pytest.fixture
    def mock_config_enabled(self, tmp_path: Path) -> RagdConfig:
        """Create config with multi-modal enabled."""
        config = RagdConfig()
        config.storage.data_dir = tmp_path
        config.multi_modal = MultiModalConfig(
            enabled=True,
            vision_model="vidore/colpali-v1.0",
            vision_dimension=128,
        )
        return config

    def test_empty_query_returns_empty(self, mock_config_enabled: RagdConfig) -> None:
        """Test empty query returns empty list."""
        results = search_images("", config=mock_config_enabled)
        assert results == []

        results = search_images("   ", config=mock_config_enabled)
        assert results == []

    def test_disabled_config_returns_empty(self, mock_config_disabled: RagdConfig) -> None:
        """Test disabled config returns empty list."""
        results = search_images("test query", config=mock_config_disabled)
        assert results == []

    @patch("ragd.search.multimodal.create_vision_embedder")
    def test_no_embedder_returns_empty(
        self,
        mock_embedder: MagicMock,
        mock_config_enabled: RagdConfig,
    ) -> None:
        """Test missing embedder returns empty list."""
        mock_embedder.return_value = None

        results = search_images("test query", config=mock_config_enabled)
        assert results == []

    @patch("ragd.search.multimodal.ImageStore")
    @patch("ragd.search.multimodal.create_vision_embedder")
    def test_search_with_results(
        self,
        mock_embedder_factory: MagicMock,
        mock_store_class: MagicMock,
        mock_config_enabled: RagdConfig,
    ) -> None:
        """Test search returns results."""
        # Setup mock embedder
        mock_embedder = MagicMock()
        mock_embedder.embed_text_for_image_search.return_value = [0.1] * 128
        mock_embedder_factory.return_value = mock_embedder

        # Setup mock store
        mock_store = MagicMock()
        mock_store.search.return_value = [
            {
                "image_id": "img_1",
                "score": 0.95,
                "metadata": {
                    "document_id": "doc_1",
                    "source_path": "/path/doc.pdf",
                    "width": 800,
                    "height": 600,
                    "format": "png",
                    "page_number": 1,
                },
            },
            {
                "image_id": "img_2",
                "score": 0.85,
                "metadata": {
                    "document_id": "doc_1",
                    "source_path": "/path/doc.pdf",
                    "width": 640,
                    "height": 480,
                    "format": "jpeg",
                    "page_number": 2,
                },
            },
        ]
        mock_store_class.return_value = mock_store

        results = search_images("diagram of architecture", config=mock_config_enabled)

        assert len(results) == 2
        assert results[0].image_id == "img_1"
        assert results[0].score == 0.95
        assert results[1].image_id == "img_2"
        assert results[1].score == 0.85

    @patch("ragd.search.multimodal.ImageStore")
    @patch("ragd.search.multimodal.create_vision_embedder")
    def test_search_with_min_score(
        self,
        mock_embedder_factory: MagicMock,
        mock_store_class: MagicMock,
        mock_config_enabled: RagdConfig,
    ) -> None:
        """Test search filters by min_score."""
        # Setup mock embedder
        mock_embedder = MagicMock()
        mock_embedder.embed_text_for_image_search.return_value = [0.1] * 128
        mock_embedder_factory.return_value = mock_embedder

        # Setup mock store with low-scoring results
        mock_store = MagicMock()
        mock_store.search.return_value = [
            {
                "image_id": "img_1",
                "score": 0.95,
                "metadata": {"document_id": "doc_1", "source_path": "/path", "width": 100, "height": 100, "format": "png"},
            },
            {
                "image_id": "img_2",
                "score": 0.3,  # Below min_score
                "metadata": {"document_id": "doc_1", "source_path": "/path", "width": 100, "height": 100, "format": "png"},
            },
        ]
        mock_store_class.return_value = mock_store

        results = search_images("test", min_score=0.5, config=mock_config_enabled)

        assert len(results) == 1
        assert results[0].image_id == "img_1"


class TestSearchSimilarImages:
    """Tests for search_similar_images function."""

    @pytest.fixture
    def mock_config_enabled(self, tmp_path: Path) -> RagdConfig:
        """Create config with multi-modal enabled."""
        config = RagdConfig()
        config.storage.data_dir = tmp_path
        config.multi_modal = MultiModalConfig(
            enabled=True,
            vision_dimension=128,
        )
        return config

    def test_file_not_found(self, mock_config_enabled: RagdConfig, tmp_path: Path) -> None:
        """Test FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            search_similar_images(tmp_path / "nonexistent.png", config=mock_config_enabled)

    def test_disabled_config_returns_empty(self, tmp_path: Path) -> None:
        """Test disabled config returns empty list."""
        config = RagdConfig()
        config.multi_modal = MultiModalConfig(enabled=False)

        image_path = tmp_path / "test.png"
        image_path.touch()

        results = search_similar_images(image_path, config=config)
        assert results == []


class TestCheckMultimodalSearchAvailable:
    """Tests for check_multimodal_search_available function."""

    def test_disabled_config(self, tmp_path: Path) -> None:
        """Test disabled config returns False."""
        config = RagdConfig()
        config.multi_modal = MultiModalConfig(enabled=False)

        available, message = check_multimodal_search_available(config)
        assert available is False
        assert "disabled" in message.lower()

    @patch("ragd.vision.embedder.check_vision_available")
    def test_missing_vision_deps(self, mock_check: MagicMock, tmp_path: Path) -> None:
        """Test missing vision dependencies."""
        config = RagdConfig()
        config.storage.data_dir = tmp_path
        config.multi_modal = MultiModalConfig(enabled=True)

        mock_check.return_value = (False, "Missing colpali-engine")

        available, message = check_multimodal_search_available(config)
        assert available is False
        assert "colpali" in message.lower()

    @patch("ragd.vision.embedder.check_vision_available")
    def test_available(self, mock_check: MagicMock, tmp_path: Path) -> None:
        """Test available returns True."""
        config = RagdConfig()
        config.storage.data_dir = tmp_path
        config.multi_modal = MultiModalConfig(enabled=True)

        mock_check.return_value = (True, "OK")

        available, message = check_multimodal_search_available(config)
        assert available is True
        assert "available" in message.lower()


class TestSearchImportExports:
    """Tests for search module exports."""

    def test_multimodal_exports(self) -> None:
        """Test multi-modal functions are exported."""
        from ragd import search

        assert hasattr(search, "ImageSearchResult")
        assert hasattr(search, "search_images")
        assert hasattr(search, "search_similar_images")
        assert hasattr(search, "search_images_by_bytes")
        assert hasattr(search, "check_multimodal_search_available")
