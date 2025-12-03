"""Protocol definitions for vector store backends.

This module defines the interface contract that all vector store backends
must implement. Using protocols enables type-safe polymorphism while
allowing flexibility in backend implementations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ragd.storage.types import (
        BackendHealth,
        BackendType,
        StorageStats,
        VectorSearchResult,
    )


@runtime_checkable
class VectorStore(Protocol):
    """Protocol for vector store backends.

    All vector store implementations MUST implement this protocol.
    The protocol defines the minimum interface required for ragd
    to interact with any vector database backend.

    CRITICAL: Score Normalisation
    -----------------------------
    All search results MUST return scores in the range [0, 1] where:
    - 1.0 = identical/perfect match
    - 0.0 = completely dissimilar

    This normalisation is required because:
    1. Agentic RAG uses score thresholds (e.g., 0.8 for "excellent")
    2. Different backends use different distance metrics
    3. Consistent scores enable backend-agnostic quality assessment

    Normalisation formulas:
    - ChromaDB (cosine distance 0-2): score = 1.0 - (distance / 2.0)
    - FAISS L2 (distance 0-∞): score = 1.0 / (1.0 + distance)
    - FAISS IP (inner product): already 0-1 for normalised vectors
    """

    @property
    def name(self) -> str:
        """Return the backend name (e.g., 'chromadb', 'faiss')."""
        ...

    @property
    def backend_type(self) -> BackendType:
        """Return the backend type enum."""
        ...

    @property
    def dimension(self) -> int:
        """Return the embedding dimension (e.g., 384 for MiniLM)."""
        ...

    @property
    def supports_metadata_filtering(self) -> bool:
        """Return True if backend supports native metadata filtering."""
        ...

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
            embeddings: Embedding vectors (must match store dimension)
            contents: Text content for each vector
            metadatas: Metadata dictionaries for each vector

        Raises:
            ValueError: If dimension mismatch or duplicate IDs
        """
        ...

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
            where: Optional filter conditions (backend-specific)

        Returns:
            List of VectorSearchResult with normalised scores (0-1)
        """
        ...

    def get(self, ids: list[str]) -> list[VectorSearchResult | None]:
        """Retrieve vectors by ID.

        Args:
            ids: List of vector IDs to retrieve

        Returns:
            List of results (None for missing IDs)
        """
        ...

    def delete(self, ids: list[str]) -> int:
        """Delete vectors by ID.

        Args:
            ids: List of vector IDs to delete

        Returns:
            Number of vectors actually deleted
        """
        ...

    def exists(self, id: str) -> bool:
        """Check if a vector exists.

        Args:
            id: Vector ID to check

        Returns:
            True if vector exists
        """
        ...

    def count(self) -> int:
        """Return total number of vectors in store."""
        ...

    def get_stats(self) -> StorageStats:
        """Get storage statistics.

        Returns:
            StorageStats with counts and backend info
        """
        ...

    def health_check(self) -> BackendHealth:
        """Perform health check on the backend.

        Returns:
            BackendHealth with status and diagnostics
        """
        ...

    def persist(self) -> None:
        """Persist any pending changes to disk.

        Some backends (like FAISS) require explicit persist calls.
        Others (like ChromaDB) may auto-persist.
        """
        ...

    def reset(self) -> None:
        """Delete all data. Warning: Destructive operation."""
        ...

    def close(self) -> None:
        """Clean up resources and close connections."""
        ...


@runtime_checkable
class MetadataProxy(Protocol):
    """Protocol for metadata storage proxy.

    Used by backends that don't support native metadata storage
    (e.g., FAISS). Provides a SQLite-backed metadata layer.
    """

    def add(
        self,
        vector_id: int,
        chunk_id: str,
        document_id: str,
        content: str,
        metadata: dict[str, Any],
    ) -> None:
        """Add metadata for a vector.

        Args:
            vector_id: Backend's internal vector ID (e.g., FAISS index)
            chunk_id: Unique chunk identifier
            document_id: Parent document identifier
            content: Text content
            metadata: Additional metadata
        """
        ...

    def get(self, chunk_id: str) -> dict[str, Any] | None:
        """Get metadata by chunk ID.

        Args:
            chunk_id: Chunk identifier

        Returns:
            Metadata dict if found, None otherwise
        """
        ...

    def get_by_vector_id(self, vector_id: int) -> dict[str, Any] | None:
        """Get metadata by backend vector ID.

        Args:
            vector_id: Backend's internal vector ID

        Returns:
            Metadata dict if found, None otherwise
        """
        ...

    def filter(self, where: dict[str, Any]) -> list[int]:
        """Find vector IDs matching filter criteria.

        Translates ChromaDB-style where filters to SQL queries.

        Args:
            where: Filter conditions (e.g., {"document_id": "doc123"})

        Returns:
            List of matching vector IDs
        """
        ...

    def delete(self, chunk_ids: list[str]) -> int:
        """Delete metadata by chunk IDs.

        Args:
            chunk_ids: List of chunk identifiers

        Returns:
            Number of records deleted
        """
        ...

    def delete_by_document(self, document_id: str) -> int:
        """Delete all metadata for a document.

        Args:
            document_id: Document identifier

        Returns:
            Number of records deleted
        """
        ...

    def count(self) -> int:
        """Return total number of metadata records."""
        ...

    def close(self) -> None:
        """Close database connection."""
        ...
