"""ChromaDB adapter implementing the VectorStore protocol.

This adapter wraps ChromaDB to provide a consistent interface with
other vector store backends. It handles score normalisation to ensure
scores are always in the 0-1 range.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Lazy import chromadb - it's heavy (~3-5 seconds)
# Imported inside ChromaDBAdapter.__init__ when actually needed
if TYPE_CHECKING:
    import chromadb

from ragd.storage.types import (
    BackendHealth,
    BackendType,
    HealthStatus,
    StorageStats,
    VectorSearchResult,
)

logger = logging.getLogger(__name__)


class ChromaDBAdapter:
    """ChromaDB adapter implementing VectorStore protocol.

    This adapter provides a consistent interface for ChromaDB while handling:
    - Score normalisation (cosine distance 0-2 → score 0-1)
    - Consistent error handling
    - Health checks

    ChromaDB uses cosine distance which ranges from 0 (identical) to 2 (opposite).
    We normalise to similarity score: score = 1.0 - (distance / 2.0)
    """

    COLLECTION_NAME = "ragd_documents"
    METADATA_COLLECTION = "ragd_metadata"

    def __init__(
        self,
        persist_directory: Path,
        dimension: int = 384,
        collection_name: str | None = None,
        **kwargs: object,
    ) -> None:
        """Initialise ChromaDB adapter.

        Args:
            persist_directory: Directory for persistent storage
            dimension: Embedding dimension (default 384 for MiniLM)
            collection_name: Optional custom collection name
            **kwargs: Additional ChromaDB options
        """
        # Lazy import chromadb - it's heavy (~3-5 seconds first time)
        logger.info("Initialising vector database...")
        import chromadb
        from chromadb.config import Settings

        self._persist_directory = persist_directory
        self._dimension = dimension
        self._collection_name = collection_name or self.COLLECTION_NAME

        persist_directory.mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=str(persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # Main collection for vectors
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        # Metadata collection for document records
        self._metadata_collection = self._client.get_or_create_collection(
            name=self.METADATA_COLLECTION,
        )

        logger.debug(
            "ChromaDB adapter initialised: %s, dimension=%d",
            persist_directory,
            dimension,
        )

    @property
    def name(self) -> str:
        """Return the backend name."""
        return "chromadb"

    @property
    def backend_type(self) -> BackendType:
        """Return the backend type enum."""
        return BackendType.CHROMADB

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return self._dimension

    @property
    def supports_metadata_filtering(self) -> bool:
        """ChromaDB supports native metadata filtering."""
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
        if not ids:
            return

        # Validate dimension
        for i, emb in enumerate(embeddings):
            if len(emb) != self._dimension:
                raise ValueError(
                    f"Embedding {i} dimension {len(emb)} != expected {self._dimension}"
                )

        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=contents,
            metadatas=metadatas,
        )

        logger.debug("Added %d vectors to ChromaDB", len(ids))

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
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        output: list[VectorSearchResult] = []

        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                distance = results["distances"][0][i] if results["distances"] else 0.0
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                chunk_id = results["ids"][0][i] if results["ids"] else ""

                # Normalise cosine distance (0-2) to score (0-1)
                # distance=0 → score=1.0 (identical)
                # distance=2 → score=0.0 (opposite)
                score = 1.0 - (distance / 2.0)

                # Clamp to valid range (handles floating point edge cases)
                score = max(0.0, min(1.0, score))

                output.append(
                    VectorSearchResult(
                        id=chunk_id,
                        content=doc,
                        score=score,
                        metadata=metadata,
                        raw_distance=distance,
                    )
                )

        return output

    def get(self, ids: list[str]) -> list[VectorSearchResult | None]:
        """Retrieve vectors by ID.

        Args:
            ids: List of vector IDs to retrieve

        Returns:
            List of results (None for missing IDs)
        """
        if not ids:
            return []

        results = self._collection.get(
            ids=ids,
            include=["documents", "metadatas"],
        )

        output: list[VectorSearchResult | None] = []

        # Build lookup from results
        result_map: dict[str, tuple[str, dict[str, Any]]] = {}
        for i, result_id in enumerate(results["ids"]):
            doc = results["documents"][i] if results["documents"] else ""
            meta = results["metadatas"][i] if results["metadatas"] else {}
            result_map[result_id] = (doc, meta)

        # Return in same order as requested
        for req_id in ids:
            if req_id in result_map:
                doc, meta = result_map[req_id]
                output.append(
                    VectorSearchResult(
                        id=req_id,
                        content=doc,
                        score=1.0,  # Exact match
                        metadata=meta,
                    )
                )
            else:
                output.append(None)

        return output

    def delete(self, ids: list[str]) -> int:
        """Delete vectors by ID.

        Args:
            ids: List of vector IDs to delete

        Returns:
            Number of vectors deleted
        """
        if not ids:
            return 0

        # Get count before
        existing = self._collection.get(ids=ids, include=[])
        count = len(existing["ids"])

        if count > 0:
            self._collection.delete(ids=existing["ids"])

        logger.debug("Deleted %d vectors from ChromaDB", count)
        return count

    def exists(self, id: str) -> bool:
        """Check if a vector exists.

        Args:
            id: Vector ID to check

        Returns:
            True if vector exists
        """
        result = self._collection.get(ids=[id], include=[])
        return len(result["ids"]) > 0

    def count(self) -> int:
        """Return total number of vectors in store."""
        return self._collection.count()

    def get_stats(self) -> StorageStats:
        """Get storage statistics.

        Returns:
            StorageStats with counts and backend info
        """
        return StorageStats(
            document_count=self._metadata_collection.count(),
            chunk_count=self._collection.count(),
            backend=BackendType.CHROMADB,
            dimension=self._dimension,
        )

    def health_check(self) -> BackendHealth:
        """Perform health check on ChromaDB.

        Returns:
            BackendHealth with status and diagnostics
        """
        import time

        start = time.perf_counter()

        try:
            # Check connectivity by counting
            count = self._collection.count()
            latency = (time.perf_counter() - start) * 1000

            return BackendHealth(
                backend=BackendType.CHROMADB,
                status=HealthStatus.HEALTHY,
                message=f"OK ({count} vectors)",
                details={
                    "vector_count": count,
                    "persist_directory": str(self._persist_directory),
                    "collection": self._collection_name,
                },
                latency_ms=latency,
            )

        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return BackendHealth(
                backend=BackendType.CHROMADB,
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                latency_ms=latency,
            )

    def persist(self) -> None:
        """Persist changes to disk.

        ChromaDB auto-persists, so this is a no-op but included for
        protocol compliance.
        """
        # ChromaDB PersistentClient auto-persists
        pass

    def reset(self) -> None:
        """Delete all data. Warning: Destructive operation."""
        self._client.delete_collection(self._collection_name)
        self._client.delete_collection(self.METADATA_COLLECTION)

        # Recreate collections
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self._metadata_collection = self._client.get_or_create_collection(
            name=self.METADATA_COLLECTION,
        )

        logger.info("ChromaDB reset complete")

    def close(self) -> None:
        """Clean up resources.

        ChromaDB PersistentClient doesn't require explicit closing,
        but included for protocol compliance.
        """
        pass

    # =========================================================================
    # Document-level operations (for compatibility with existing code)
    # =========================================================================

    def add_document_metadata(
        self,
        document_id: str,
        path: str,
        metadata: dict[str, Any],
    ) -> None:
        """Add document-level metadata.

        Args:
            document_id: Unique document identifier
            path: Document file path
            metadata: Document metadata
        """
        self._metadata_collection.add(
            ids=[document_id],
            documents=[path],
            metadatas=[metadata],
        )

    def get_document_metadata(self, document_id: str) -> dict[str, Any] | None:
        """Get document metadata by ID.

        Args:
            document_id: Document identifier

        Returns:
            Metadata dict if found, None otherwise
        """
        result = self._metadata_collection.get(
            ids=[document_id],
            include=["metadatas", "documents"],
        )

        if not result["ids"]:
            return None

        metadata = result["metadatas"][0] if result["metadatas"] else {}
        metadata["path"] = result["documents"][0] if result["documents"] else ""
        return metadata

    def delete_document(self, document_id: str) -> int:
        """Delete document and all its chunks.

        Args:
            document_id: Document to delete

        Returns:
            Number of chunks deleted
        """
        # Delete chunks
        chunk_results = self._collection.get(
            where={"document_id": document_id},
            include=[],
        )
        chunk_count = len(chunk_results["ids"])

        if chunk_count > 0:
            self._collection.delete(where={"document_id": document_id})

        # Delete document metadata
        self._metadata_collection.delete(ids=[document_id])

        logger.debug(
            "Deleted document %s with %d chunks",
            document_id,
            chunk_count,
        )
        return chunk_count

    def list_documents(self) -> list[dict[str, Any]]:
        """List all documents.

        Returns:
            List of document metadata dicts
        """
        result = self._metadata_collection.get(include=["metadatas", "documents"])

        documents = []
        for i, doc_id in enumerate(result["ids"]):
            metadata = result["metadatas"][i] if result["metadatas"] else {}
            metadata["document_id"] = doc_id
            metadata["path"] = result["documents"][i] if result["documents"] else ""
            documents.append(metadata)

        return documents

    def document_exists_by_hash(self, content_hash: str) -> bool:
        """Check if a document with given hash exists.

        Args:
            content_hash: Content hash to check

        Returns:
            True if document exists
        """
        result = self._metadata_collection.get(
            where={"content_hash": content_hash},
            include=[],
        )
        return len(result["ids"]) > 0
