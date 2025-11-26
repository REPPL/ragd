"""Embedding generation using sentence-transformers.

This module provides embedding generation for text chunks using local models.
"""

from __future__ import annotations

from typing import Protocol

from sentence_transformers import SentenceTransformer


class Embedder(Protocol):
    """Protocol for embedding generators."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        ...

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        ...

    @property
    def model_name(self) -> str:
        """Return model name."""
        ...


class SentenceTransformerEmbedder:
    """Embedding generator using sentence-transformers."""

    # Model dimensions
    MODEL_DIMENSIONS: dict[str, int] = {
        "all-MiniLM-L6-v2": 384,
        "all-mpnet-base-v2": 768,
        "multi-qa-MiniLM-L6-cos-v1": 384,
        "paraphrase-MiniLM-L6-v2": 384,
    }

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str | None = None,
        batch_size: int = 32,
    ) -> None:
        """Initialise sentence transformer embedder.

        Args:
            model_name: Name of the sentence-transformers model
            device: Device to use (cuda, mps, cpu, or None for auto)
            batch_size: Batch size for embedding
        """
        self._model_name = model_name
        self._batch_size = batch_size
        self._model: SentenceTransformer | None = None
        self._device = device

    def _ensure_model(self) -> SentenceTransformer:
        """Lazy load the model.

        Returns:
            Loaded SentenceTransformer model
        """
        if self._model is None:
            self._model = SentenceTransformer(self._model_name, device=self._device)
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors as lists of floats
        """
        if not texts:
            return []

        model = self._ensure_model()
        embeddings = model.encode(
            texts,
            batch_size=self._batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        return [embedding.tolist() for embedding in embeddings]

    def embed_single(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        result = self.embed([text])
        return result[0] if result else []

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        if self._model_name in self.MODEL_DIMENSIONS:
            return self.MODEL_DIMENSIONS[self._model_name]
        # Load model to get dimension
        model = self._ensure_model()
        return model.get_sentence_embedding_dimension()

    @property
    def model_name(self) -> str:
        """Return model name."""
        return self._model_name

    def is_loaded(self) -> bool:
        """Check if model is loaded.

        Returns:
            True if model is loaded
        """
        return self._model is not None


# Global embedder instance (lazy initialised)
_embedder: SentenceTransformerEmbedder | None = None


def get_embedder(
    model_name: str = "all-MiniLM-L6-v2",
    device: str | None = None,
    batch_size: int = 32,
) -> SentenceTransformerEmbedder:
    """Get or create an embedder instance.

    Args:
        model_name: Model name to use
        device: Device to use
        batch_size: Batch size

    Returns:
        Embedder instance
    """
    global _embedder

    if _embedder is None or _embedder.model_name != model_name:
        _embedder = SentenceTransformerEmbedder(
            model_name=model_name,
            device=device,
            batch_size=batch_size,
        )

    return _embedder
