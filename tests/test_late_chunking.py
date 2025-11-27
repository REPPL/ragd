"""Tests for late chunking embedder (F-011).

Tests the late chunking implementation for context-aware embeddings.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ragd.embedding.late_chunking import (
    ChunkBoundary,
    LateChunkingEmbedder,
    check_late_chunking_available,
    create_late_chunking_embedder,
)


class TestChunkBoundary:
    """Tests for ChunkBoundary dataclass."""

    def test_boundary_creation(self):
        """Test creating a chunk boundary."""
        boundary = ChunkBoundary(
            start=0,
            end=100,
            content="This is the chunk content.",
        )
        assert boundary.start == 0
        assert boundary.end == 100
        assert boundary.content == "This is the chunk content."

    def test_boundary_with_unicode(self):
        """Test boundary with unicode content."""
        boundary = ChunkBoundary(
            start=50,
            end=150,
            content="Unicode content: cafe \u2192 \u2615",
        )
        assert "\u2615" in boundary.content


class TestLateChunkingEmbedder:
    """Tests for LateChunkingEmbedder."""

    def test_embedder_initialisation(self):
        """Test embedder initialisation with defaults."""
        embedder = LateChunkingEmbedder()
        assert embedder._model_name == "jinaai/jina-embeddings-v2-small-en"
        assert embedder._device is None
        assert embedder._model is None

    def test_embedder_custom_model(self):
        """Test embedder with custom model."""
        embedder = LateChunkingEmbedder(
            model_name="custom-model",
            device="cpu",
            trust_remote_code=False,
        )
        assert embedder._model_name == "custom-model"
        assert embedder._device == "cpu"
        assert embedder._trust_remote_code is False

    def test_is_available_checks_imports(self):
        """Test is_available checks for required imports."""
        embedder = LateChunkingEmbedder()
        # is_available should return True if transformers and torch are installed
        # This test just verifies the method exists and returns a bool
        result = embedder.is_available()
        assert isinstance(result, bool)

    def test_embed_empty_list(self):
        """Test embedding empty list returns empty list."""
        embedder = LateChunkingEmbedder()
        result = embedder.embed([])
        assert result == []

    def test_embed_document_chunks_empty(self):
        """Test embedding empty chunks list."""
        embedder = LateChunkingEmbedder()
        result = embedder.embed_document_chunks("Some text", [])
        assert result == []


class TestCheckLateChunkingAvailable:
    """Tests for check_late_chunking_available function."""

    def test_returns_tuple(self):
        """Test function returns a tuple of (bool, str)."""
        result = check_late_chunking_available()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)

    def test_message_indicates_status(self):
        """Test message indicates availability status."""
        available, message = check_late_chunking_available()
        if available:
            assert "available" in message.lower()
        else:
            assert "missing" in message.lower() or "install" in message.lower()


class TestCreateLateChunkingEmbedder:
    """Tests for create_late_chunking_embedder factory."""

    def test_returns_embedder_or_none(self):
        """Test factory returns embedder or None based on availability."""
        result = create_late_chunking_embedder()
        # Should be LateChunkingEmbedder if deps available, None otherwise
        if result is not None:
            assert isinstance(result, LateChunkingEmbedder)

    def test_passes_model_name(self):
        """Test factory passes model name to embedder."""
        with patch(
            "ragd.embedding.late_chunking.check_late_chunking_available"
        ) as mock_check:
            mock_check.return_value = (True, "Available")
            result = create_late_chunking_embedder(
                model_name="custom-model",
                device="cpu",
            )
            if result is not None:
                assert result._model_name == "custom-model"
                assert result._device == "cpu"


class TestLateChunkingEmbedderIntegration:
    """Integration tests for late chunking embedder.

    These tests require transformers and torch to be installed.
    They are skipped if dependencies are not available.
    """

    @pytest.fixture
    def embedder(self):
        """Create embedder if available."""
        available, _ = check_late_chunking_available()
        if not available:
            pytest.skip("Late chunking dependencies not available")
        # Use a small, fast model for testing
        return create_late_chunking_embedder(device="cpu")

    def test_embed_single_text(self, embedder):
        """Test embedding a single text."""
        if embedder is None:
            pytest.skip("Embedder not available")
        result = embedder.embed(["This is a test sentence."])
        assert len(result) == 1
        assert len(result[0]) > 0  # Has some dimensions
        assert all(isinstance(v, float) for v in result[0])

    def test_embed_multiple_texts(self, embedder):
        """Test embedding multiple texts."""
        if embedder is None:
            pytest.skip("Embedder not available")
        texts = [
            "First text for embedding.",
            "Second text, completely different.",
            "Third text with more content.",
        ]
        result = embedder.embed(texts)
        assert len(result) == 3
        # All embeddings should have same dimension
        dim = len(result[0])
        assert all(len(e) == dim for e in result)

    def test_dimension_property(self, embedder):
        """Test dimension property returns correct size."""
        if embedder is None:
            pytest.skip("Embedder not available")
        dim = embedder.dimension
        assert isinstance(dim, int)
        assert dim > 0

    def test_model_name_property(self, embedder):
        """Test model_name property."""
        if embedder is None:
            pytest.skip("Embedder not available")
        assert embedder.model_name == "jinaai/jina-embeddings-v2-small-en"


class TestLateChunkingLogic:
    """Tests for late chunking specific logic.

    These tests mock the model to test the chunking logic without
    requiring actual model inference.
    """

    def test_char_to_token_boundaries_mapping(self):
        """Test character to token boundary mapping logic."""
        # This is a conceptual test - actual mapping requires tokenizer
        # We test that the method exists and has correct signature
        embedder = LateChunkingEmbedder()
        assert hasattr(embedder, "_char_to_token_boundaries")

    def test_chunk_boundaries_structure(self):
        """Test that ChunkBoundary has all required fields."""
        boundary = ChunkBoundary(start=0, end=10, content="test")
        assert hasattr(boundary, "start")
        assert hasattr(boundary, "end")
        assert hasattr(boundary, "content")

    def test_max_context_tokens_constant(self):
        """Test DEFAULT_MAX_CONTEXT_TOKENS is defined."""
        assert hasattr(LateChunkingEmbedder, "DEFAULT_MAX_CONTEXT_TOKENS")
        assert LateChunkingEmbedder.DEFAULT_MAX_CONTEXT_TOKENS == 8192

    def test_long_context_models_defined(self):
        """Test known long-context models are defined."""
        models = LateChunkingEmbedder.LONG_CONTEXT_MODELS
        assert isinstance(models, dict)
        assert "jinaai/jina-embeddings-v2-base-en" in models
        assert "jinaai/jina-embeddings-v2-small-en" in models
