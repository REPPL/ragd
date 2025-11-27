"""Multi-modal search for text-to-image and image-to-image retrieval.

This module provides search functionality for images using vision embeddings,
enabling natural language queries to find relevant images.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ragd.config import RagdConfig, load_config
from ragd.storage.images import ImageStore
from ragd.vision.embedder import VisionEmbedder, create_vision_embedder

logger = logging.getLogger(__name__)


@dataclass
class ImageSearchResult:
    """A single image search result."""

    image_id: str
    score: float
    document_id: str
    source_path: str
    width: int
    height: int
    format: str
    page_number: int | None = None
    caption: str = ""
    ocr_text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def aspect_ratio(self) -> float:
        """Calculate aspect ratio."""
        if self.height == 0:
            return 0.0
        return self.width / self.height

    @property
    def is_landscape(self) -> bool:
        """Check if image is landscape."""
        return self.aspect_ratio > 1.0


def search_images(
    query: str,
    limit: int = 10,
    min_score: float = 0.0,
    config: RagdConfig | None = None,
    document_id: str | None = None,
    embedder: VisionEmbedder | None = None,
) -> list[ImageSearchResult]:
    """Search images using a text query.

    Uses vision embeddings to find images that match the text description.
    This enables natural language search over image collections.

    Args:
        query: Search query string (natural language description)
        limit: Maximum number of results
        min_score: Minimum similarity score (0-1)
        config: Configuration (loads default if not provided)
        document_id: Optional filter by document ID
        embedder: Vision embedder (created if not provided)

    Returns:
        List of ImageSearchResult objects sorted by relevance
    """
    if not query.strip():
        return []

    if config is None:
        config = load_config()

    # Check if multi-modal is enabled
    if not config.multi_modal.enabled:
        logger.debug("Multi-modal search disabled in config")
        return []

    # Get or create vision embedder
    if embedder is None:
        embedder = create_vision_embedder(
            model_name=config.multi_modal.vision_model,
        )

    if embedder is None:
        logger.warning("Vision embedder not available for image search")
        return []

    # Initialise image store
    store = ImageStore(
        config.chroma_path,
        dimension=config.multi_modal.vision_dimension,
    )

    # Generate text embedding for image search
    query_embedding = embedder.embed_text_for_image_search(query)

    # Build filter
    where = None
    if document_id:
        where = {"document_id": document_id}

    # Search in image store
    raw_results = store.search(
        query_embedding=query_embedding,
        limit=limit,
        where=where,
    )

    # Convert to ImageSearchResult objects
    results = []
    for raw in raw_results:
        score = raw.get("score", 0.0)

        # Skip low-scoring results
        if score < min_score:
            continue

        metadata = raw.get("metadata", {})

        result = ImageSearchResult(
            image_id=raw.get("image_id", ""),
            score=score,
            document_id=metadata.get("document_id", ""),
            source_path=metadata.get("source_path", ""),
            width=metadata.get("width", 0),
            height=metadata.get("height", 0),
            format=metadata.get("format", ""),
            page_number=metadata.get("page_number") or None,
            caption=metadata.get("caption", ""),
            ocr_text=metadata.get("ocr_text", ""),
            metadata=metadata,
        )
        results.append(result)

    return results


def search_similar_images(
    image_path: Path,
    limit: int = 10,
    min_score: float = 0.0,
    config: RagdConfig | None = None,
    exclude_self: bool = True,
    embedder: VisionEmbedder | None = None,
) -> list[ImageSearchResult]:
    """Search for images similar to a given image.

    Uses vision embeddings to find visually similar images.

    Args:
        image_path: Path to query image
        limit: Maximum number of results
        min_score: Minimum similarity score (0-1)
        config: Configuration (loads default if not provided)
        exclude_self: Exclude the query image from results
        embedder: Vision embedder (created if not provided)

    Returns:
        List of ImageSearchResult objects sorted by similarity
    """
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    if config is None:
        config = load_config()

    if not config.multi_modal.enabled:
        logger.debug("Multi-modal search disabled in config")
        return []

    # Get or create vision embedder
    if embedder is None:
        embedder = create_vision_embedder(
            model_name=config.multi_modal.vision_model,
        )

    if embedder is None:
        logger.warning("Vision embedder not available for image search")
        return []

    # Initialise image store
    store = ImageStore(
        config.chroma_path,
        dimension=config.multi_modal.vision_dimension,
    )

    # Generate image embedding
    query_embedding = embedder.embed_image(image_path)

    # Fetch extra results if excluding self
    fetch_limit = limit + 1 if exclude_self else limit

    # Search in image store
    raw_results = store.search(
        query_embedding=query_embedding,
        limit=fetch_limit,
    )

    # Convert to ImageSearchResult objects
    results = []
    query_path_str = str(image_path.resolve())

    for raw in raw_results:
        score = raw.get("score", 0.0)
        metadata = raw.get("metadata", {})

        # Skip self if requested
        if exclude_self:
            result_path = metadata.get("source_path", "")
            if result_path == query_path_str:
                continue

        # Skip low-scoring results
        if score < min_score:
            continue

        result = ImageSearchResult(
            image_id=raw.get("image_id", ""),
            score=score,
            document_id=metadata.get("document_id", ""),
            source_path=metadata.get("source_path", ""),
            width=metadata.get("width", 0),
            height=metadata.get("height", 0),
            format=metadata.get("format", ""),
            page_number=metadata.get("page_number") or None,
            caption=metadata.get("caption", ""),
            ocr_text=metadata.get("ocr_text", ""),
            metadata=metadata,
        )
        results.append(result)

        # Stop at limit
        if len(results) >= limit:
            break

    return results


def search_images_by_bytes(
    image_data: bytes,
    limit: int = 10,
    min_score: float = 0.0,
    config: RagdConfig | None = None,
    embedder: VisionEmbedder | None = None,
) -> list[ImageSearchResult]:
    """Search for images similar to given image bytes.

    Args:
        image_data: Image as bytes
        limit: Maximum number of results
        min_score: Minimum similarity score (0-1)
        config: Configuration (loads default if not provided)
        embedder: Vision embedder (created if not provided)

    Returns:
        List of ImageSearchResult objects sorted by similarity
    """
    if config is None:
        config = load_config()

    if not config.multi_modal.enabled:
        return []

    # Get or create vision embedder
    if embedder is None:
        embedder = create_vision_embedder(
            model_name=config.multi_modal.vision_model,
        )

    if embedder is None:
        return []

    # Initialise image store
    store = ImageStore(
        config.chroma_path,
        dimension=config.multi_modal.vision_dimension,
    )

    # Generate image embedding
    query_embedding = embedder.embed_image(image_data)

    # Search in image store
    raw_results = store.search(
        query_embedding=query_embedding,
        limit=limit,
    )

    # Convert to ImageSearchResult objects
    results = []
    for raw in raw_results:
        score = raw.get("score", 0.0)

        if score < min_score:
            continue

        metadata = raw.get("metadata", {})

        result = ImageSearchResult(
            image_id=raw.get("image_id", ""),
            score=score,
            document_id=metadata.get("document_id", ""),
            source_path=metadata.get("source_path", ""),
            width=metadata.get("width", 0),
            height=metadata.get("height", 0),
            format=metadata.get("format", ""),
            page_number=metadata.get("page_number") or None,
            caption=metadata.get("caption", ""),
            metadata=metadata,
        )
        results.append(result)

    return results


def check_multimodal_search_available(config: RagdConfig | None = None) -> tuple[bool, str]:
    """Check if multi-modal search is available.

    Args:
        config: Configuration to check

    Returns:
        Tuple of (available: bool, message: str)
    """
    if config is None:
        config = load_config()

    if not config.multi_modal.enabled:
        return False, "Multi-modal support is disabled in configuration"

    from ragd.vision.embedder import check_vision_available

    available, message = check_vision_available()
    if not available:
        return False, f"Vision embedder not available: {message}"

    return True, "Multi-modal search is available"
