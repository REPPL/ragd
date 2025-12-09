"""ChromaDB storage backend for ragd.

This module provides a wrapper around ChromaDB for storing and retrieving
document embeddings with metadata.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Lazy import chromadb - it's heavy (~3-5 seconds)
# Imported inside ChromaStore.__init__ when actually needed
if TYPE_CHECKING:
    import chromadb

logger = logging.getLogger(__name__)


@dataclass
class DocumentRecord:
    """Record of an indexed document."""

    document_id: str
    path: str
    filename: str
    file_type: str
    file_size: int
    chunk_count: int
    indexed_at: str
    content_hash: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ChromaStore:
    """ChromaDB storage wrapper for ragd.

    Provides high-level operations for storing documents, chunks, and
    embeddings in ChromaDB.
    """

    COLLECTION_NAME = "ragd_documents"
    METADATA_COLLECTION = "ragd_metadata"

    def __init__(self, persist_directory: Path) -> None:
        """Initialise ChromaDB store.

        Args:
            persist_directory: Directory for persistent storage
        """
        # Lazy import chromadb - it's heavy (~3-5 seconds first time)
        logger.info("Initialising vector database...")
        import chromadb
        from chromadb.config import Settings

        self.persist_directory = persist_directory
        persist_directory.mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=str(persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # Main collection for document chunks
        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        # Metadata collection for document records
        self._metadata = self._client.get_or_create_collection(
            name=self.METADATA_COLLECTION,
        )

    def add_document(
        self,
        document_id: str,
        chunks: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
        document_record: DocumentRecord,
    ) -> None:
        """Add a document with its chunks and embeddings.

        Args:
            document_id: Unique document identifier
            chunks: List of text chunks
            embeddings: List of embedding vectors
            metadatas: List of metadata dicts for each chunk
            document_record: Document metadata record
        """
        if not chunks:
            return

        # Generate unique IDs for each chunk
        chunk_ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]

        # Add chunk metadata
        for metadata in metadatas:
            metadata["document_id"] = document_id

        # Add chunks to main collection
        self._collection.add(
            ids=chunk_ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        # Store document record in metadata collection
        self._metadata.add(
            ids=[document_id],
            documents=[document_record.path],
            metadatas=[
                {
                    "filename": document_record.filename,
                    "file_type": document_record.file_type,
                    "file_size": document_record.file_size,
                    "chunk_count": document_record.chunk_count,
                    "indexed_at": document_record.indexed_at,
                    "content_hash": document_record.content_hash,
                }
            ],
        )

    def search(
        self,
        query_embedding: list[float],
        limit: int = 10,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar chunks.

        Args:
            query_embedding: Query vector
            limit: Maximum results to return
            where: Optional filter conditions

        Returns:
            List of results with content, metadata, and scores
        """
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        # Convert to list of result dicts
        output = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0.0
                # Convert distance to similarity score (cosine)
                score = 1.0 - distance

                output.append(
                    {
                        "content": doc,
                        "metadata": metadata,
                        "score": score,
                        "id": results["ids"][0][i] if results["ids"] else "",
                    }
                )

        return output

    def get_document(self, document_id: str) -> DocumentRecord | None:
        """Get document record by ID.

        Args:
            document_id: Document identifier

        Returns:
            DocumentRecord if found, None otherwise
        """
        result = self._metadata.get(ids=[document_id], include=["metadatas"])

        if not result["ids"]:
            return None

        metadata = result["metadatas"][0] if result["metadatas"] else {}
        return DocumentRecord(
            document_id=document_id,
            path=result.get("documents", [""])[0] if result.get("documents") else "",
            filename=metadata.get("filename", ""),
            file_type=metadata.get("file_type", ""),
            file_size=metadata.get("file_size", 0),
            chunk_count=metadata.get("chunk_count", 0),
            indexed_at=metadata.get("indexed_at", ""),
            content_hash=metadata.get("content_hash", ""),
        )

    def document_exists(self, content_hash: str) -> bool:
        """Check if a document with given hash already exists.

        Args:
            content_hash: Content hash to check

        Returns:
            True if document exists
        """
        result = self._metadata.get(
            where={"content_hash": content_hash},
            include=["metadatas"],
        )
        return bool(result["ids"])

    def delete_document(self, document_id: str) -> bool:
        """Delete a document and its chunks.

        Args:
            document_id: Document to delete

        Returns:
            True if deleted, False if not found
        """
        # Check if exists
        doc = self.get_document(document_id)
        if not doc:
            return False

        # Delete chunks
        self._collection.delete(where={"document_id": document_id})

        # Delete metadata
        self._metadata.delete(ids=[document_id])

        return True

    def list_documents(self) -> list[DocumentRecord]:
        """List all indexed documents.

        Returns:
            List of document records
        """
        result = self._metadata.get(include=["metadatas", "documents"])

        documents = []
        for i, doc_id in enumerate(result["ids"]):
            metadata = result["metadatas"][i] if result["metadatas"] else {}
            path = result["documents"][i] if result["documents"] else ""
            documents.append(
                DocumentRecord(
                    document_id=doc_id,
                    path=path,
                    filename=metadata.get("filename", ""),
                    file_type=metadata.get("file_type", ""),
                    file_size=metadata.get("file_size", 0),
                    chunk_count=metadata.get("chunk_count", 0),
                    indexed_at=metadata.get("indexed_at", ""),
                    content_hash=metadata.get("content_hash", ""),
                )
            )

        return documents

    def get_stats(self) -> dict[str, int]:
        """Get storage statistics.

        Returns:
            Dictionary with document and chunk counts
        """
        return {
            "document_count": self._metadata.count(),
            "chunk_count": self._collection.count(),
        }

    def reset(self) -> None:
        """Reset all collections. Warning: This deletes all data."""
        self._client.delete_collection(self.COLLECTION_NAME)
        self._client.delete_collection(self.METADATA_COLLECTION)

        # Recreate collections
        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        self._metadata = self._client.get_or_create_collection(
            name=self.METADATA_COLLECTION,
        )


def generate_document_id(path: Path) -> str:
    """Generate a unique document ID from path.

    Args:
        path: Document file path

    Returns:
        Unique identifier string
    """
    return hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:16]


def generate_content_hash(content: str) -> str:
    """Generate a content hash for deduplication.

    Args:
        content: Document content

    Returns:
        Hash string
    """
    return hashlib.sha256(content.encode()).hexdigest()[:32]
