"""Image storage backend for multi-modal RAG.

This module provides ChromaDB storage for image embeddings, kept separate from
text embeddings due to different dimensions (128-dim vision vs 384-dim text).
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Lazy import chromadb - it's heavy (~3-5 seconds)
# Imported inside ImageStore.__init__ when actually needed
if TYPE_CHECKING:
    import chromadb

logger = logging.getLogger(__name__)


@dataclass
class ImageRecord:
    """Record of an indexed image."""

    image_id: str
    document_id: str  # Parent document (if extracted from PDF)
    source_path: str
    width: int
    height: int
    format: str
    size_bytes: int
    page_number: int | None = None  # For PDF-extracted images
    indexed_at: str = ""
    content_hash: str = ""
    caption: str = ""  # Optional AI-generated caption
    metadata: dict[str, Any] = field(default_factory=dict)


class ImageStore:
    """ChromaDB storage for image embeddings.

    Uses a separate collection from text embeddings because:
    - Different embedding dimensions (vision: 128, text: 384)
    - Different search semantics (text-to-image vs text-to-text)
    - Separate scaling and optimisation needs
    """

    COLLECTION_NAME = "ragd_images"
    METADATA_COLLECTION = "ragd_image_metadata"

    def __init__(self, persist_directory: Path, dimension: int = 128) -> None:
        """Initialise image store.

        Args:
            persist_directory: Directory for persistent storage
            dimension: Embedding dimension (default 128 for ColPali)
        """
        # Lazy import chromadb - it's heavy (~3-5 seconds first time)
        logger.info("Initialising image storage...")
        import chromadb
        from chromadb.config import Settings

        self.persist_directory = persist_directory
        self.dimension = dimension
        persist_directory.mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=str(persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # Main collection for image embeddings
        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        # Metadata collection for image records
        self._metadata = self._client.get_or_create_collection(
            name=self.METADATA_COLLECTION,
        )

    def add_image(
        self,
        image_id: str,
        embedding: list[float],
        record: ImageRecord,
    ) -> None:
        """Add an image with its embedding.

        Args:
            image_id: Unique image identifier
            embedding: Vision embedding vector
            record: Image metadata record
        """
        # Validate embedding dimension
        if len(embedding) != self.dimension:
            logger.warning(
                "Embedding dimension mismatch: expected %d, got %d",
                self.dimension,
                len(embedding),
            )

        # Add embedding to main collection
        self._collection.add(
            ids=[image_id],
            embeddings=[embedding],
            metadatas=[
                {
                    "document_id": record.document_id,
                    "source_path": record.source_path,
                    "width": record.width,
                    "height": record.height,
                    "format": record.format,
                    "page_number": record.page_number or 0,
                    "caption": record.caption,
                }
            ],
        )

        # Store full record in metadata collection
        self._metadata.add(
            ids=[image_id],
            documents=[record.source_path],
            metadatas=[
                {
                    "document_id": record.document_id,
                    "width": record.width,
                    "height": record.height,
                    "format": record.format,
                    "size_bytes": record.size_bytes,
                    "page_number": record.page_number or 0,
                    "indexed_at": record.indexed_at,
                    "content_hash": record.content_hash,
                    "caption": record.caption,
                }
            ],
        )

    def add_images(
        self,
        images: list[tuple[str, list[float], ImageRecord]],
    ) -> int:
        """Add multiple images with their embeddings.

        Args:
            images: List of (image_id, embedding, record) tuples

        Returns:
            Number of images added
        """
        if not images:
            return 0

        ids = [img[0] for img in images]
        embeddings = [img[1] for img in images]
        records = [img[2] for img in images]

        # Add to main collection
        metadatas = [
            {
                "document_id": r.document_id,
                "source_path": r.source_path,
                "width": r.width,
                "height": r.height,
                "format": r.format,
                "page_number": r.page_number or 0,
                "caption": r.caption,
            }
            for r in records
        ]

        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        # Add to metadata collection
        meta_metadatas = [
            {
                "document_id": r.document_id,
                "width": r.width,
                "height": r.height,
                "format": r.format,
                "size_bytes": r.size_bytes,
                "page_number": r.page_number or 0,
                "indexed_at": r.indexed_at,
                "content_hash": r.content_hash,
                "caption": r.caption,
            }
            for r in records
        ]

        self._metadata.add(
            ids=ids,
            documents=[r.source_path for r in records],
            metadatas=meta_metadatas,
        )

        return len(images)

    def search(
        self,
        query_embedding: list[float],
        limit: int = 10,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar images.

        Args:
            query_embedding: Query vector (from text or image)
            limit: Maximum results to return
            where: Optional filter conditions

        Returns:
            List of results with metadata and scores
        """
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where,
            include=["metadatas", "distances"],
        )

        output = []
        if results["ids"] and results["ids"][0]:
            for i, image_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0.0
                # Convert distance to similarity score (cosine)
                score = 1.0 - distance

                output.append(
                    {
                        "image_id": image_id,
                        "metadata": metadata,
                        "score": score,
                    }
                )

        return output

    def get_image(self, image_id: str) -> ImageRecord | None:
        """Get image record by ID.

        Args:
            image_id: Image identifier

        Returns:
            ImageRecord if found, None otherwise
        """
        result = self._metadata.get(
            ids=[image_id],
            include=["metadatas", "documents"],
        )

        if not result["ids"]:
            return None

        metadata = result["metadatas"][0] if result["metadatas"] else {}
        source_path = result["documents"][0] if result["documents"] else ""

        return ImageRecord(
            image_id=image_id,
            document_id=metadata.get("document_id", ""),
            source_path=source_path,
            width=metadata.get("width", 0),
            height=metadata.get("height", 0),
            format=metadata.get("format", ""),
            size_bytes=metadata.get("size_bytes", 0),
            page_number=metadata.get("page_number") or None,
            indexed_at=metadata.get("indexed_at", ""),
            content_hash=metadata.get("content_hash", ""),
            caption=metadata.get("caption", ""),
        )

    def get_images_for_document(self, document_id: str) -> list[ImageRecord]:
        """Get all images extracted from a document.

        Args:
            document_id: Document identifier

        Returns:
            List of ImageRecords
        """
        result = self._metadata.get(
            where={"document_id": document_id},
            include=["metadatas", "documents"],
        )

        records = []
        for i, image_id in enumerate(result["ids"]):
            metadata = result["metadatas"][i] if result["metadatas"] else {}
            source_path = result["documents"][i] if result["documents"] else ""

            records.append(
                ImageRecord(
                    image_id=image_id,
                    document_id=document_id,
                    source_path=source_path,
                    width=metadata.get("width", 0),
                    height=metadata.get("height", 0),
                    format=metadata.get("format", ""),
                    size_bytes=metadata.get("size_bytes", 0),
                    page_number=metadata.get("page_number") or None,
                    indexed_at=metadata.get("indexed_at", ""),
                    content_hash=metadata.get("content_hash", ""),
                    caption=metadata.get("caption", ""),
                )
            )

        return records

    def image_exists(self, content_hash: str) -> bool:
        """Check if an image with given hash already exists.

        Args:
            content_hash: Content hash to check

        Returns:
            True if image exists
        """
        result = self._metadata.get(
            where={"content_hash": content_hash},
            include=["metadatas"],
        )
        return bool(result["ids"])

    def delete_image(self, image_id: str) -> bool:
        """Delete an image.

        Args:
            image_id: Image to delete

        Returns:
            True if deleted, False if not found
        """
        record = self.get_image(image_id)
        if not record:
            return False

        self._collection.delete(ids=[image_id])
        self._metadata.delete(ids=[image_id])

        return True

    def delete_images_for_document(self, document_id: str) -> int:
        """Delete all images for a document.

        Args:
            document_id: Document whose images to delete

        Returns:
            Number of images deleted
        """
        images = self.get_images_for_document(document_id)
        if not images:
            return 0

        image_ids = [img.image_id for img in images]

        self._collection.delete(ids=image_ids)
        self._metadata.delete(ids=image_ids)

        return len(image_ids)

    def list_images(self, limit: int = 100) -> list[ImageRecord]:
        """List indexed images.

        Args:
            limit: Maximum images to return

        Returns:
            List of image records
        """
        result = self._metadata.get(
            include=["metadatas", "documents"],
            limit=limit,
        )

        records = []
        for i, image_id in enumerate(result["ids"]):
            metadata = result["metadatas"][i] if result["metadatas"] else {}
            source_path = result["documents"][i] if result["documents"] else ""

            records.append(
                ImageRecord(
                    image_id=image_id,
                    document_id=metadata.get("document_id", ""),
                    source_path=source_path,
                    width=metadata.get("width", 0),
                    height=metadata.get("height", 0),
                    format=metadata.get("format", ""),
                    size_bytes=metadata.get("size_bytes", 0),
                    page_number=metadata.get("page_number") or None,
                    indexed_at=metadata.get("indexed_at", ""),
                    content_hash=metadata.get("content_hash", ""),
                    caption=metadata.get("caption", ""),
                )
            )

        return records

    def get_stats(self) -> dict[str, int]:
        """Get storage statistics.

        Returns:
            Dictionary with image count
        """
        return {
            "image_count": self._collection.count(),
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


def generate_image_id(data: bytes, document_id: str = "", page_number: int = 0) -> str:
    """Generate a unique image ID from content hash.

    Args:
        data: Image bytes
        document_id: Parent document ID (for uniqueness within document)
        page_number: Page number (for PDF-extracted images)

    Returns:
        Unique identifier string
    """
    content_hash = hashlib.sha256(data).hexdigest()[:16]
    if document_id:
        return f"{document_id}_img_{page_number}_{content_hash[:8]}"
    return f"img_{content_hash}"


def generate_image_content_hash(data: bytes) -> str:
    """Generate a content hash for image deduplication.

    Args:
        data: Image bytes

    Returns:
        Hash string
    """
    return hashlib.sha256(data).hexdigest()[:32]
