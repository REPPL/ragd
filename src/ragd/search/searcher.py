"""Semantic search implementation for ragd.

This module provides search functionality over indexed documents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ragd.config import RagdConfig, load_config
from ragd.embedding import get_embedder
from ragd.storage import ChromaStore


@dataclass
class SourceLocation:
    """Location information for a search result."""

    page_number: int | None = None
    char_start: int | None = None
    char_end: int | None = None


@dataclass
class SearchResult:
    """A single search result."""

    content: str
    score: float
    document_id: str
    document_name: str
    chunk_index: int
    metadata: dict[str, Any] = field(default_factory=dict)
    location: SourceLocation | None = None


def search(
    query: str,
    limit: int = 10,
    min_score: float = 0.0,
    config: RagdConfig | None = None,
    filters: dict[str, Any] | None = None,
) -> list[SearchResult]:
    """Search indexed documents.

    Args:
        query: Search query string
        limit: Maximum number of results
        min_score: Minimum similarity score (0-1)
        config: Configuration (loads default if not provided)
        filters: Optional metadata filters

    Returns:
        List of SearchResult objects
    """
    if not query.strip():
        return []

    if config is None:
        config = load_config()

    # Initialise components
    embedder = get_embedder(
        model_name=config.embedding.model,
        device=config.embedding.device,
        batch_size=config.embedding.batch_size,
    )
    store = ChromaStore(config.chroma_path)

    # Generate query embedding
    query_embedding = embedder.embed_single(query)

    # Search in ChromaDB
    raw_results = store.search(
        query_embedding=query_embedding,
        limit=limit,
        where=filters,
    )

    # Convert to SearchResult objects
    results = []
    for raw in raw_results:
        score = raw.get("score", 0.0)

        # Skip low-scoring results
        if score < min_score:
            continue

        metadata = raw.get("metadata", {})

        # Build source location
        location = SourceLocation(
            page_number=metadata.get("page_number"),
            char_start=metadata.get("start_char"),
            char_end=metadata.get("end_char"),
        )

        result = SearchResult(
            content=raw.get("content", ""),
            score=score,
            document_id=metadata.get("document_id", ""),
            document_name=metadata.get("filename", ""),
            chunk_index=metadata.get("chunk_index", 0),
            metadata=metadata,
            location=location,
        )
        results.append(result)

    return results
