"""FAISS adapter implementing the VectorStore protocol.

This adapter provides high-performance vector search using Facebook's FAISS
library, with SQLite-backed metadata storage for filtering support.
"""

from __future__ import annotations

import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from ragd.storage.metadata.sqlite_store import SQLiteMetadataStore
from ragd.storage.types import (
    BackendHealth,
    BackendType,
    HealthStatus,
    StorageStats,
    VectorSearchResult,
)

logger = logging.getLogger(__name__)


class FAISSAdapter:
    """FAISS adapter implementing VectorStore protocol.

    This adapter provides high-performance vector search with:
    - Auto index type selection based on collection size
    - SQLite-backed metadata for ChromaDB-style filtering
    - L2 distance normalised to 0-1 similarity scores

    FAISS uses L2 (Euclidean) distance which ranges from 0 (identical) to infinity.
    We normalise to similarity score: score = 1.0 / (1.0 + distance)

    Index Types (auto-selected based on size):
    - Flat: < 10K vectors (exact search)
    - IVFFlat: 10K-100K vectors (approximate, requires training)
    - IVFPQ: 100K-1M vectors (compressed, requires training)
    - HNSW: > 1M vectors (graph-based, no training)
    """

    INDEX_FILE = "faiss.index"
    ID_MAP_FILE = "faiss_ids.pkl"

    # Size thresholds for index type selection
    FLAT_THRESHOLD = 10_000
    IVFFLAT_THRESHOLD = 100_000
    IVFPQ_THRESHOLD = 1_000_000

    def __init__(
        self,
        persist_directory: Path,
        dimension: int = 384,
        index_type: str | None = None,
        nlist: int = 100,
        nprobe: int = 10,
        **kwargs: object,
    ) -> None:
        """Initialise FAISS adapter.

        Args:
            persist_directory: Directory for persistent storage
            dimension: Embedding dimension (default 384 for MiniLM)
            index_type: Override index type (Flat, IVFFlat, IVFPQ, HNSW)
            nlist: Number of clusters for IVF indices
            nprobe: Number of clusters to search
            **kwargs: Additional options
        """
        try:
            import faiss  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "FAISS not installed. Install with: pip install ragd[faiss]"
            ) from e

        self._persist_directory = persist_directory
        self._dimension = dimension
        self._index_type_override = index_type
        self._nlist = nlist
        self._nprobe = nprobe

        persist_directory.mkdir(parents=True, exist_ok=True)

        # Paths
        self._index_path = persist_directory / self.INDEX_FILE
        self._id_map_path = persist_directory / self.ID_MAP_FILE
        self._metadata_path = persist_directory / "metadata.db"

        # Initialise metadata store
        self._metadata = SQLiteMetadataStore(self._metadata_path)

        # ID mapping: chunk_id → faiss_id (position in index)
        self._id_to_faiss: dict[str, int] = {}
        self._faiss_to_id: dict[int, str] = {}
        self._next_id = 0

        # Initialise or load index
        self._index = self._load_or_create_index()

        logger.debug(
            "FAISS adapter initialised: %s, dimension=%d, vectors=%d",
            persist_directory,
            dimension,
            self._index.ntotal,
        )

    def _load_or_create_index(self) -> Any:
        """Load existing index or create new one."""
        import faiss

        if self._index_path.exists():
            # Load existing index
            index = faiss.read_index(str(self._index_path))

            # Load ID mappings
            if self._id_map_path.exists():
                with open(self._id_map_path, "rb") as f:
                    data = pickle.load(f)
                    self._id_to_faiss = data.get("id_to_faiss", {})
                    self._faiss_to_id = data.get("faiss_to_id", {})
                    self._next_id = data.get("next_id", 0)

            logger.debug("Loaded existing FAISS index with %d vectors", index.ntotal)
            return index

        # Create new index
        return self._create_index(0)

    def _create_index(self, expected_size: int) -> Any:
        """Create appropriate index based on expected size."""
        import faiss

        # Determine index type
        if self._index_type_override:
            index_type = self._index_type_override
        elif expected_size < self.FLAT_THRESHOLD:
            index_type = "Flat"
        elif expected_size < self.IVFFLAT_THRESHOLD:
            index_type = "IVFFlat"
        elif expected_size < self.IVFPQ_THRESHOLD:
            index_type = "IVFPQ"
        else:
            index_type = "HNSW"

        logger.debug("Creating FAISS index type: %s", index_type)

        if index_type == "Flat":
            # Exact L2 search
            return faiss.IndexFlatL2(self._dimension)

        elif index_type == "IVFFlat":
            # Inverted file with flat storage
            quantizer = faiss.IndexFlatL2(self._dimension)
            index = faiss.IndexIVFFlat(quantizer, self._dimension, self._nlist)
            return index

        elif index_type == "IVFPQ":
            # Inverted file with product quantisation
            quantizer = faiss.IndexFlatL2(self._dimension)
            # m = number of subvectors, nbits = bits per code
            m = 8 if self._dimension >= 8 else self._dimension
            index = faiss.IndexIVFPQ(quantizer, self._dimension, self._nlist, m, 8)
            return index

        elif index_type == "HNSW":
            # Hierarchical Navigable Small World graph
            M = 32  # Number of connections per layer
            index = faiss.IndexHNSWFlat(self._dimension, M)
            return index

        else:
            raise ValueError(f"Unknown index type: {index_type}")

    @property
    def name(self) -> str:
        """Return the backend name."""
        return "faiss"

    @property
    def backend_type(self) -> BackendType:
        """Return the backend type enum."""
        return BackendType.FAISS

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return self._dimension

    @property
    def supports_metadata_filtering(self) -> bool:
        """FAISS supports metadata filtering via SQLite proxy."""
        return True

    def add(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        contents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Add vectors to the store.

        Args:
            ids: Unique identifiers for each vector
            embeddings: Embedding vectors
            contents: Text content for each vector
            metadatas: Metadata dictionaries for each vector

        Raises:
            ValueError: If dimension mismatch
        """
        import faiss

        if not ids:
            return

        # Validate dimension
        for i, emb in enumerate(embeddings):
            if len(emb) != self._dimension:
                raise ValueError(
                    f"Embedding {i} dimension {len(emb)} != expected {self._dimension}"
                )

        # Convert to numpy array
        vectors = np.array(embeddings, dtype=np.float32)

        # Check if index needs training
        if hasattr(self._index, "is_trained") and not self._index.is_trained:
            if vectors.shape[0] >= self._nlist:
                logger.debug("Training FAISS index with %d vectors", vectors.shape[0])
                self._index.train(vectors)
            else:
                # Not enough vectors to train - use flat index temporarily
                logger.warning(
                    "Not enough vectors (%d) to train IVF index (need %d), "
                    "using flat index",
                    vectors.shape[0],
                    self._nlist,
                )
                self._index = faiss.IndexFlatL2(self._dimension)

        # Add vectors to FAISS
        self._index.add(vectors)

        # Update ID mappings and metadata
        metadata_batch = []
        for i, (chunk_id, content, metadata) in enumerate(
            zip(ids, contents, metadatas)
        ):
            faiss_id = self._next_id + i
            self._id_to_faiss[chunk_id] = faiss_id
            self._faiss_to_id[faiss_id] = chunk_id

            # Get document_id from metadata
            document_id = metadata.get("document_id", "")

            metadata_batch.append(
                (faiss_id, chunk_id, document_id, content, metadata)
            )

        self._next_id += len(ids)

        # Add to metadata store
        self._metadata.add_batch(metadata_batch)

        logger.debug("Added %d vectors to FAISS", len(ids))

    def search(
        self,
        query_embedding: list[float],
        limit: int = 10,
        where: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """Search for similar vectors.

        Args:
            query_embedding: Query vector
            limit: Maximum number of results
            where: Optional filter conditions

        Returns:
            List of VectorSearchResult with normalised scores (0-1)
        """
        if self._index.ntotal == 0:
            return []

        # Set nprobe for IVF indices
        if hasattr(self._index, "nprobe"):
            self._index.nprobe = self._nprobe

        # Convert query to numpy
        query = np.array([query_embedding], dtype=np.float32)

        # If we have a filter, use two-stage search
        if where:
            return self._filtered_search(query, limit, where)

        # Direct search
        distances, indices = self._index.search(query, limit)

        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue

            # Get metadata
            meta_data = self._metadata.get_by_vector_id(int(idx))
            if meta_data is None:
                continue

            # Normalise L2 distance to score (0-1)
            # distance=0 → score=1.0 (identical)
            # distance→∞ → score→0.0
            score = 1.0 / (1.0 + float(dist))

            results.append(
                VectorSearchResult(
                    id=meta_data["chunk_id"],
                    content=meta_data["content"],
                    score=score,
                    metadata=meta_data["metadata"],
                    raw_distance=float(dist),
                )
            )

        return results

    def _filtered_search(
        self,
        query: np.ndarray,
        limit: int,
        where: dict[str, Any],
    ) -> list[VectorSearchResult]:
        """Two-stage filtered search.

        1. Get matching vector IDs from metadata filter
        2. Search only those vectors
        """
        import faiss

        # Get matching vector IDs
        matching_ids = self._metadata.filter(where)

        if not matching_ids:
            return []

        # For small result sets, do exact search on matching IDs
        if len(matching_ids) <= limit * 10:
            # Get all matching vectors and compute distances
            results = []

            for faiss_id in matching_ids:
                meta_data = self._metadata.get_by_vector_id(faiss_id)
                if meta_data is None:
                    continue

                # Reconstruct vector from index (if possible)
                try:
                    vector = np.zeros((1, self._dimension), dtype=np.float32)
                    self._index.reconstruct(faiss_id, vector[0])
                    dist = float(np.sum((query[0] - vector[0]) ** 2))
                except RuntimeError:
                    # Index doesn't support reconstruction
                    # Fall back to searching with ID selector
                    break

                score = 1.0 / (1.0 + dist)
                results.append(
                    VectorSearchResult(
                        id=meta_data["chunk_id"],
                        content=meta_data["content"],
                        score=score,
                        metadata=meta_data["metadata"],
                        raw_distance=dist,
                    )
                )

            # Sort by score descending
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:limit]

        # For large result sets, use IDSelector if available
        try:
            id_array = np.array(matching_ids, dtype=np.int64)
            selector = faiss.IDSelectorArray(id_array)

            # Create search parameters with selector
            params = faiss.SearchParametersIVF()
            params.sel = selector

            distances, indices = self._index.search(
                query, min(limit, len(matching_ids)), params=params
            )

        except (AttributeError, TypeError):
            # Fallback: search all, filter results
            distances, indices = self._index.search(query, self._index.ntotal)

            matching_set = set(matching_ids)
            filtered = [
                (d, i)
                for d, i in zip(distances[0], indices[0])
                if i in matching_set
            ][:limit]

            if filtered:
                distances = np.array([[d for d, _ in filtered]])
                indices = np.array([[i for _, i in filtered]])
            else:
                return []

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue

            meta_data = self._metadata.get_by_vector_id(int(idx))
            if meta_data is None:
                continue

            score = 1.0 / (1.0 + float(dist))

            results.append(
                VectorSearchResult(
                    id=meta_data["chunk_id"],
                    content=meta_data["content"],
                    score=score,
                    metadata=meta_data["metadata"],
                    raw_distance=float(dist),
                )
            )

        return results

    def get(self, ids: list[str]) -> list[VectorSearchResult | None]:
        """Retrieve vectors by ID.

        Args:
            ids: List of vector IDs to retrieve

        Returns:
            List of results (None for missing IDs)
        """
        results: list[VectorSearchResult | None] = []

        for chunk_id in ids:
            meta_data = self._metadata.get(chunk_id)
            if meta_data is None:
                results.append(None)
            else:
                results.append(
                    VectorSearchResult(
                        id=chunk_id,
                        content=meta_data["content"],
                        score=1.0,  # Exact match
                        metadata=meta_data["metadata"],
                    )
                )

        return results

    def delete(self, ids: list[str]) -> int:
        """Delete vectors by ID.

        Note: FAISS doesn't support true deletion. We mark as deleted
        in metadata and rebuild index periodically.

        Args:
            ids: List of vector IDs to delete

        Returns:
            Number of vectors deleted (from metadata)
        """
        # Delete from metadata
        count = self._metadata.delete(ids)

        # Remove from ID mappings
        for chunk_id in ids:
            faiss_id = self._id_to_faiss.pop(chunk_id, None)
            if faiss_id is not None:
                self._faiss_to_id.pop(faiss_id, None)

        logger.debug("Deleted %d vectors from FAISS metadata", count)
        return count

    def exists(self, id: str) -> bool:
        """Check if a vector exists.

        Args:
            id: Vector ID to check

        Returns:
            True if vector exists
        """
        return self._metadata.get(id) is not None

    def count(self) -> int:
        """Return total number of vectors in store."""
        return self._metadata.count()

    def get_stats(self) -> StorageStats:
        """Get storage statistics.

        Returns:
            StorageStats with counts and backend info
        """
        # Get index size
        index_size = None
        if self._index_path.exists():
            index_size = self._index_path.stat().st_size

        return StorageStats(
            document_count=len(self._metadata.get_all_document_ids()),
            chunk_count=self._metadata.count(),
            backend=BackendType.FAISS,
            dimension=self._dimension,
            index_size_bytes=index_size,
        )

    def health_check(self) -> BackendHealth:
        """Perform health check on FAISS.

        Returns:
            BackendHealth with status and diagnostics
        """
        import time

        start = time.perf_counter()

        try:
            # Check index is accessible
            count = self._index.ntotal
            latency = (time.perf_counter() - start) * 1000

            # Determine index type
            index_type = type(self._index).__name__

            return BackendHealth(
                backend=BackendType.FAISS,
                status=HealthStatus.HEALTHY,
                message=f"OK ({count} vectors, {index_type})",
                details={
                    "vector_count": count,
                    "index_type": index_type,
                    "persist_directory": str(self._persist_directory),
                    "dimension": self._dimension,
                },
                latency_ms=latency,
            )

        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return BackendHealth(
                backend=BackendType.FAISS,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                latency_ms=latency,
            )

    def persist(self) -> None:
        """Persist index and mappings to disk."""
        import faiss

        # Save FAISS index
        faiss.write_index(self._index, str(self._index_path))

        # Save ID mappings
        with open(self._id_map_path, "wb") as f:
            pickle.dump(
                {
                    "id_to_faiss": self._id_to_faiss,
                    "faiss_to_id": self._faiss_to_id,
                    "next_id": self._next_id,
                },
                f,
            )

        logger.debug("Persisted FAISS index and mappings")

    def reset(self) -> None:
        """Delete all data. Warning: Destructive operation."""
        import faiss

        # Remove files
        if self._index_path.exists():
            self._index_path.unlink()
        if self._id_map_path.exists():
            self._id_map_path.unlink()
        if self._metadata_path.exists():
            self._metadata_path.unlink()

        # Reset state
        self._id_to_faiss = {}
        self._faiss_to_id = {}
        self._next_id = 0
        self._index = faiss.IndexFlatL2(self._dimension)

        # Reinitialise metadata
        self._metadata = SQLiteMetadataStore(self._metadata_path)

        logger.info("FAISS reset complete")

    def close(self) -> None:
        """Clean up resources."""
        self.persist()
        self._metadata.close()
