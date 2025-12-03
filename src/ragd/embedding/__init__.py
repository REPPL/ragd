"""Embedding generation for ragd."""

from ragd.embedding.embedder import (
    Embedder,
    SentenceTransformerEmbedder,
    get_embedder,
    is_model_cached,
    download_model,
)
from ragd.embedding.late_chunking import (
    ChunkBoundary,
    LateChunkingEmbedder,
    check_late_chunking_available,
    create_late_chunking_embedder,
)

__all__ = [
    "Embedder",
    "SentenceTransformerEmbedder",
    "get_embedder",
    "is_model_cached",
    "download_model",
    "ChunkBoundary",
    "LateChunkingEmbedder",
    "check_late_chunking_available",
    "create_late_chunking_embedder",
]
