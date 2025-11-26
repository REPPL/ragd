"""Tests for embedding generation module."""

import pytest

from ragd.embedding.embedder import (
    SentenceTransformerEmbedder,
    get_embedder,
)


class TestSentenceTransformerEmbedder:
    """Tests for SentenceTransformerEmbedder."""

    def test_init(self) -> None:
        """Test embedder initialisation."""
        embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
        assert embedder.model_name == "all-MiniLM-L6-v2"
        assert not embedder.is_loaded()

    def test_dimension(self) -> None:
        """Test dimension property."""
        embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
        assert embedder.dimension == 384

    def test_embed_single(self) -> None:
        """Test single text embedding."""
        embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
        embedding = embedder.embed_single("Hello world")
        assert len(embedding) == 384
        assert all(isinstance(v, float) for v in embedding)

    def test_embed_multiple(self) -> None:
        """Test multiple text embedding."""
        embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
        texts = ["Hello", "World", "Test"]
        embeddings = embedder.embed(texts)
        assert len(embeddings) == 3
        assert all(len(e) == 384 for e in embeddings)

    def test_embed_empty_list(self) -> None:
        """Test embedding empty list."""
        embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
        embeddings = embedder.embed([])
        assert embeddings == []

    def test_is_loaded_after_embed(self) -> None:
        """Test model is loaded after embedding."""
        embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
        assert not embedder.is_loaded()
        embedder.embed(["test"])
        assert embedder.is_loaded()


class TestGetEmbedder:
    """Tests for get_embedder function."""

    def test_get_embedder_returns_instance(self) -> None:
        """Test get_embedder returns an embedder."""
        embedder = get_embedder()
        assert isinstance(embedder, SentenceTransformerEmbedder)

    def test_get_embedder_with_model(self) -> None:
        """Test get_embedder with specific model."""
        embedder = get_embedder(model_name="all-MiniLM-L6-v2")
        assert embedder.model_name == "all-MiniLM-L6-v2"
