"""Hybrid search combining semantic and keyword search.

Implements Reciprocal Rank Fusion (RRF) to combine results from
multiple retrieval sources for improved relevance.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ragd.config import RagdConfig, load_config
from ragd.embedding import get_embedder
from ragd.search.bm25 import BM25Index, BM25Result
from ragd.storage import BackendType, ChromaStore, VectorStore, create_vector_store

if TYPE_CHECKING:
    from ragd.storage.types import VectorSearchResult


class SearchMode(Enum):
    """Search mode selection."""

    HYBRID = "hybrid"
    SEMANTIC = "semantic"
    KEYWORD = "keyword"


@dataclass
class SourceLocation:
    """Location information for a search result."""

    page_number: int | None = None
    char_start: int | None = None
    char_end: int | None = None


@dataclass
class HybridSearchResult:
    """A single hybrid search result."""

    content: str
    combined_score: float
    semantic_score: float | None
    keyword_score: float | None
    semantic_rank: int | None
    keyword_rank: int | None
    rrf_score: float
    document_id: str
    document_name: str
    chunk_id: str
    chunk_index: int
    metadata: dict[str, Any] = field(default_factory=dict)
    location: SourceLocation | None = None


def reciprocal_rank_fusion(
    rankings: list[list[tuple[str, float]]],
    k: int = 60,
) -> list[tuple[str, float]]:
    """Combine multiple rankings using Reciprocal Rank Fusion.

    RRF formula: score(d) = sum(1 / (k + rank_i(d)))

    Args:
        rankings: List of rankings, each being [(id, score), ...]
        k: RRF constant (default 60)

    Returns:
        Combined ranking as [(id, rrf_score), ...] sorted by score
    """
    rrf_scores: dict[str, float] = {}

    for ranking in rankings:
        for rank, (item_id, _) in enumerate(ranking, start=1):
            if item_id not in rrf_scores:
                rrf_scores[item_id] = 0.0
            rrf_scores[item_id] += 1.0 / (k + rank)

    # Sort by RRF score descending
    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_items


class HybridSearcher:
    """Hybrid search engine combining semantic and keyword search."""

    def __init__(
        self,
        config: RagdConfig | None = None,
        chroma_store: ChromaStore | None = None,
        bm25_index: BM25Index | None = None,
        *,
        vector_store: VectorStore | None = None,
    ) -> None:
        """Initialise hybrid searcher.

        Args:
            config: Configuration (loads default if not provided)
            chroma_store: Optional pre-initialised ChromaStore (deprecated, use vector_store)
            bm25_index: Optional pre-initialised BM25Index
            vector_store: Optional pre-initialised VectorStore (preferred over chroma_store)
        """
        self.config = config or load_config()

        # Handle vector store initialisation
        # Priority: vector_store > chroma_store > factory create
        if vector_store is not None:
            self._vector_store = vector_store
        elif chroma_store is not None:
            # Deprecated path - wrap legacy ChromaStore
            warnings.warn(
                "chroma_store parameter is deprecated. Use vector_store instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            self._vector_store = chroma_store  # type: ignore[assignment]
        else:
            # Create via factory (default: ChromaDB)
            self._vector_store = create_vector_store(
                backend=BackendType.CHROMADB,
                persist_directory=self.config.chroma_path,
                dimension=self.config.embedding.dimension,
            )

        # Keep legacy reference for backwards compatibility
        self._chroma = self._vector_store  # type: ignore[assignment]

        self._bm25 = bm25_index or BM25Index(
            self.config.chroma_path / "bm25.db"
        )

        # Initialise embedder
        self._embedder = get_embedder(
            model_name=self.config.embedding.model,
            device=self.config.embedding.device,
            batch_size=self.config.embedding.batch_size,
        )

    def search(
        self,
        query: str,
        limit: int = 10,
        mode: SearchMode = SearchMode.HYBRID,
        min_score: float = 0.0,
        filters: dict[str, Any] | None = None,
        semantic_weight: float | None = None,
        keyword_weight: float | None = None,
        rrf_k: int | None = None,
    ) -> list[HybridSearchResult]:
        """Perform search based on mode.

        Args:
            query: Search query
            limit: Maximum results
            mode: Search mode (hybrid, semantic, keyword)
            min_score: Minimum combined score filter
            filters: Optional metadata filters (semantic only)
            semantic_weight: Override semantic weight (0-1)
            keyword_weight: Override keyword weight (0-1)
            rrf_k: Override RRF k constant

        Returns:
            List of HybridSearchResult sorted by relevance
        """
        if not query.strip():
            return []

        # Get config values with overrides
        sem_weight = semantic_weight if semantic_weight is not None else 0.7
        kw_weight = keyword_weight if keyword_weight is not None else 0.3
        k = rrf_k if rrf_k is not None else 60

        if mode == SearchMode.SEMANTIC:
            return self._semantic_search(query, limit, min_score, filters)
        elif mode == SearchMode.KEYWORD:
            return self._keyword_search(query, limit, min_score)
        else:
            return self._hybrid_search(
                query, limit, min_score, filters, sem_weight, kw_weight, k
            )

    def _semantic_search(
        self,
        query: str,
        limit: int,
        min_score: float,
        filters: dict[str, Any] | None,
    ) -> list[HybridSearchResult]:
        """Perform pure semantic search.

        Args:
            query: Search query
            limit: Maximum results
            min_score: Minimum score filter
            filters: Optional metadata filters

        Returns:
            List of results from semantic search only
        """
        # Generate query embedding
        query_embedding = self._embedder.embed_single(query)

        # Search vector store (returns VectorSearchResult or dict depending on backend)
        raw_results = self._vector_store.search(
            query_embedding=query_embedding,
            limit=limit,
            where=filters,
        )

        results = []
        for rank, raw in enumerate(raw_results, start=1):
            # Handle both VectorSearchResult objects and legacy dicts
            if hasattr(raw, "score"):
                # VectorSearchResult object
                score = raw.score
                content = raw.content
                metadata = raw.metadata
                chunk_id = raw.id
            else:
                # Legacy dict format
                score = raw.get("score", 0.0)
                content = raw.get("content", "")
                metadata = raw.get("metadata", {})
                chunk_id = raw.get("id", "")

            if score < min_score:
                continue

            location = SourceLocation(
                page_number=metadata.get("page_number"),
                char_start=metadata.get("start_char"),
                char_end=metadata.get("end_char"),
            )

            results.append(
                HybridSearchResult(
                    content=content,
                    combined_score=score,
                    semantic_score=score,
                    keyword_score=None,
                    semantic_rank=rank,
                    keyword_rank=None,
                    rrf_score=score,
                    document_id=metadata.get("document_id", ""),
                    document_name=metadata.get("filename", ""),
                    chunk_id=chunk_id,
                    chunk_index=metadata.get("chunk_index", 0),
                    metadata=metadata,
                    location=location,
                )
            )

        return results

    def _keyword_search(
        self,
        query: str,
        limit: int,
        min_score: float,
    ) -> list[HybridSearchResult]:
        """Perform pure keyword (BM25) search.

        Args:
            query: Search query
            limit: Maximum results
            min_score: Minimum score filter

        Returns:
            List of results from keyword search only
        """
        bm25_results = self._bm25.search(query, limit=limit)

        results = []
        for bm25_res in bm25_results:
            # Normalise BM25 score to 0-1 range (approximate)
            normalised_score = min(1.0, bm25_res.bm25_score / 10.0)
            if normalised_score < min_score:
                continue

            results.append(
                HybridSearchResult(
                    content=bm25_res.content,
                    combined_score=normalised_score,
                    semantic_score=None,
                    keyword_score=bm25_res.bm25_score,
                    semantic_rank=None,
                    keyword_rank=bm25_res.rank,
                    rrf_score=normalised_score,
                    document_id=bm25_res.document_id,
                    document_name="",  # Not available from BM25 alone
                    chunk_id=bm25_res.chunk_id,
                    chunk_index=0,  # Not available from BM25 alone
                    metadata={},
                    location=None,
                )
            )

        return results

    def _hybrid_search(
        self,
        query: str,
        limit: int,
        min_score: float,
        filters: dict[str, Any] | None,
        semantic_weight: float,
        keyword_weight: float,
        rrf_k: int,
    ) -> list[HybridSearchResult]:
        """Perform hybrid search combining semantic and keyword.

        Args:
            query: Search query
            limit: Maximum results
            min_score: Minimum combined score filter
            filters: Optional metadata filters
            semantic_weight: Weight for semantic results
            keyword_weight: Weight for keyword results
            rrf_k: RRF k constant

        Returns:
            List of results combined using RRF
        """
        # Fetch more results for fusion (we'll trim later)
        fetch_limit = limit * 3

        # Get semantic results
        query_embedding = self._embedder.embed_single(query)
        semantic_raw = self._vector_store.search(
            query_embedding=query_embedding,
            limit=fetch_limit,
            where=filters,
        )

        # Get keyword results
        keyword_raw = self._bm25.search(query, limit=fetch_limit)

        # Build rankings for RRF
        semantic_ranking: list[tuple[str, float]] = []
        keyword_ranking: list[tuple[str, float]] = []

        # Map chunk_id to full result data (using dict for flexibility)
        semantic_data: dict[str, dict[str, Any]] = {}
        keyword_data: dict[str, BM25Result] = {}

        for raw in semantic_raw:
            # Handle both VectorSearchResult objects and legacy dicts
            if hasattr(raw, "id"):
                chunk_id = raw.id
                score = raw.score
                content = raw.content
                metadata = raw.metadata
            else:
                chunk_id = raw.get("id", "")
                score = raw.get("score", 0.0)
                content = raw.get("content", "")
                metadata = raw.get("metadata", {})

            if chunk_id:
                semantic_ranking.append((chunk_id, score))
                semantic_data[chunk_id] = {
                    "id": chunk_id,
                    "score": score,
                    "content": content,
                    "metadata": metadata,
                }

        for bm25_res in keyword_raw:
            if bm25_res.chunk_id:
                keyword_ranking.append((bm25_res.chunk_id, bm25_res.bm25_score))
                keyword_data[bm25_res.chunk_id] = bm25_res

        # Apply RRF
        if not semantic_ranking and not keyword_ranking:
            return []

        rankings_to_fuse = []
        if semantic_ranking:
            rankings_to_fuse.append(semantic_ranking)
        if keyword_ranking:
            rankings_to_fuse.append(keyword_ranking)

        fused = reciprocal_rank_fusion(rankings_to_fuse, k=rrf_k)

        # Build final results
        results = []
        for chunk_id, rrf_score in fused[:limit]:
            # Get data from both sources
            sem_data = semantic_data.get(chunk_id)
            kw_data = keyword_data.get(chunk_id)

            # Calculate combined score
            sem_score = sem_data.get("score", 0.0) if sem_data else None
            kw_score = kw_data.bm25_score if kw_data else None

            # Weighted combination for display
            combined = 0.0
            if sem_score is not None:
                combined += semantic_weight * sem_score
            if kw_score is not None:
                # Normalise BM25 score
                norm_kw = min(1.0, kw_score / 10.0)
                combined += keyword_weight * norm_kw

            if combined < min_score and rrf_score < min_score:
                continue

            # Get content and metadata from either source
            if sem_data:
                content = sem_data.get("content", "")
                metadata = sem_data.get("metadata", {})
            elif kw_data:
                content = kw_data.content
                metadata = {}
            else:
                continue

            # Get ranks
            sem_rank = None
            kw_rank = None
            for i, (cid, _) in enumerate(semantic_ranking, 1):
                if cid == chunk_id:
                    sem_rank = i
                    break
            if kw_data:
                kw_rank = kw_data.rank

            location = SourceLocation(
                page_number=metadata.get("page_number"),
                char_start=metadata.get("start_char"),
                char_end=metadata.get("end_char"),
            ) if metadata else None

            results.append(
                HybridSearchResult(
                    content=content,
                    combined_score=combined,
                    semantic_score=sem_score,
                    keyword_score=kw_score,
                    semantic_rank=sem_rank,
                    keyword_rank=kw_rank,
                    rrf_score=rrf_score,
                    document_id=metadata.get("document_id", "") or (kw_data.document_id if kw_data else ""),
                    document_name=metadata.get("filename", ""),
                    chunk_id=chunk_id,
                    chunk_index=metadata.get("chunk_index", 0),
                    metadata=metadata,
                    location=location,
                )
            )

        return results

    def close(self) -> None:
        """Close resources."""
        self._bm25.close()


def hybrid_search(
    query: str,
    limit: int = 10,
    mode: str | SearchMode = SearchMode.HYBRID,
    min_score: float = 0.0,
    config: RagdConfig | None = None,
    filters: dict[str, Any] | None = None,
) -> list[HybridSearchResult]:
    """Convenience function for hybrid search.

    Args:
        query: Search query
        limit: Maximum results
        mode: Search mode (hybrid, semantic, keyword)
        min_score: Minimum score filter
        config: Configuration
        filters: Optional metadata filters

    Returns:
        List of HybridSearchResult
    """
    if isinstance(mode, str):
        mode = SearchMode(mode)

    searcher = HybridSearcher(config=config)
    try:
        return searcher.search(
            query=query,
            limit=limit,
            mode=mode,
            min_score=min_score,
            filters=filters,
        )
    finally:
        searcher.close()
