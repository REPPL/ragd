"""Vision embedding for multi-modal RAG.

Provides vision embedding using ColPali/ColQwen models for image retrieval.
These models generate embeddings suitable for text-to-image and image-to-image search.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class ImageLike(Protocol):
    """Protocol for image-like objects."""

    def tobytes(self) -> bytes:
        """Return image as bytes."""
        ...


@dataclass
class VisionEmbeddingResult:
    """Result of vision embedding generation."""

    embedding: list[float]
    model: str
    dimension: int
    processing_time_ms: float | None = None


class VisionEmbedder(ABC):
    """Abstract base class for vision embedders."""

    @abstractmethod
    def embed_image(self, image: bytes | ImageLike | Path) -> list[float]:
        """Generate embedding for an image.

        Args:
            image: Image as bytes, PIL Image, or path to image file

        Returns:
            Embedding vector as list of floats
        """
        pass

    @abstractmethod
    def embed_images(self, images: list[bytes | ImageLike | Path]) -> list[list[float]]:
        """Generate embeddings for multiple images.

        Args:
            images: List of images (bytes, PIL Images, or paths)

        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
    def embed_text_for_image_search(self, text: str) -> list[float]:
        """Generate text embedding for image search.

        This generates a text embedding in the same space as image embeddings,
        enabling text-to-image retrieval.

        Args:
            text: Query text

        Returns:
            Embedding vector compatible with image embeddings
        """
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return embedding dimension."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return model name."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if embedder is available."""
        pass


class ColPaliEmbedder(VisionEmbedder):
    """Vision embedder using ColPali/ColQwen models.

    ColPali (Contextual Late interaction model for images) generates
    embeddings that support:
    - Text-to-image search
    - Image-to-image similarity
    - Cross-modal retrieval

    Default model: vidore/colpali-v1.0 (128-dim embeddings)
    Alternative: vidore/colqwen2-v1.0 (larger, more accurate)
    """

    # Known ColPali models and their dimensions
    KNOWN_MODELS = {
        "vidore/colpali-v1.0": 128,
        "vidore/colpali-v1.1": 128,
        "vidore/colqwen2-v1.0": 128,
        "vidore/colqwen2-v1.0-b8": 128,
    }

    def __init__(
        self,
        model_name: str = "vidore/colpali-v1.0",
        device: str | None = None,
        batch_size: int = 4,
    ) -> None:
        """Initialise ColPali embedder.

        Args:
            model_name: Hugging Face model name
            device: Device to use (cuda, mps, cpu, or None for auto)
            batch_size: Batch size for embedding multiple images
        """
        self._model_name = model_name
        self._device = device
        self._batch_size = batch_size
        self._model: Any = None
        self._processor: Any = None
        self._dimension = self.KNOWN_MODELS.get(model_name, 128)

    def _ensure_model(self) -> None:
        """Lazy load the model and processor."""
        if self._model is not None:
            return

        try:
            import torch
            from colpali_engine.models import ColPali, ColPaliProcessor

            self._processor = ColPaliProcessor.from_pretrained(self._model_name)
            self._model = ColPali.from_pretrained(
                self._model_name,
                torch_dtype=torch.bfloat16,
            )

            # Move to device
            if self._device:
                self._model = self._model.to(self._device)
            elif torch.cuda.is_available():
                self._model = self._model.to("cuda")
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self._model = self._model.to("mps")

            self._model.eval()

        except ImportError as e:
            raise ImportError(
                "ColPali requires colpali-engine. "
                "Install with: pip install colpali-engine"
            ) from e

    def _load_image(self, image: bytes | ImageLike | Path) -> Any:
        """Load image from various sources.

        Args:
            image: Image as bytes, PIL Image, or path

        Returns:
            PIL Image object
        """
        from PIL import Image

        if isinstance(image, Path):
            return Image.open(image)
        elif isinstance(image, bytes):
            import io
            return Image.open(io.BytesIO(image))
        else:
            # Assume PIL Image or compatible
            return image

    def embed_image(self, image: bytes | ImageLike | Path) -> list[float]:
        """Generate embedding for an image.

        Args:
            image: Image as bytes, PIL Image, or path to image file

        Returns:
            Embedding vector as list of floats
        """
        return self.embed_images([image])[0]

    def embed_images(self, images: list[bytes | ImageLike | Path]) -> list[list[float]]:
        """Generate embeddings for multiple images.

        Args:
            images: List of images (bytes, PIL Images, or paths)

        Returns:
            List of embedding vectors
        """
        if not images:
            return []

        import torch

        self._ensure_model()

        # Load all images
        pil_images = [self._load_image(img) for img in images]

        embeddings = []
        for i in range(0, len(pil_images), self._batch_size):
            batch = pil_images[i : i + self._batch_size]

            # Process batch
            batch_images = self._processor.process_images(batch)
            batch_images = {k: v.to(self._model.device) for k, v in batch_images.items()}

            with torch.no_grad():
                image_embeddings = self._model(**batch_images)

            # Convert to list format
            for emb in image_embeddings:
                # Mean pool across sequence dimension
                pooled = emb.mean(dim=0)
                embeddings.append(pooled.cpu().float().numpy().tolist())

        return embeddings

    def embed_text_for_image_search(self, text: str) -> list[float]:
        """Generate text embedding for image search.

        Args:
            text: Query text

        Returns:
            Embedding vector compatible with image embeddings
        """
        return self.embed_texts_for_image_search([text])[0]

    def embed_texts_for_image_search(self, texts: list[str]) -> list[list[float]]:
        """Generate text embeddings for image search.

        Args:
            texts: List of query texts

        Returns:
            List of embedding vectors compatible with image embeddings
        """
        if not texts:
            return []

        import torch

        self._ensure_model()

        embeddings = []
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]

            # Process batch
            batch_queries = self._processor.process_queries(batch)
            batch_queries = {k: v.to(self._model.device) for k, v in batch_queries.items()}

            with torch.no_grad():
                query_embeddings = self._model(**batch_queries)

            # Convert to list format
            for emb in query_embeddings:
                # Mean pool across sequence dimension
                pooled = emb.mean(dim=0)
                embeddings.append(pooled.cpu().float().numpy().tolist())

        return embeddings

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        return self._dimension

    @property
    def model_name(self) -> str:
        """Return model name."""
        return self._model_name

    def is_available(self) -> bool:
        """Check if ColPali is available.

        Returns:
            True if colpali-engine is installed
        """
        try:
            import colpali_engine
            return True
        except ImportError:
            return False


def check_vision_available() -> tuple[bool, str]:
    """Check if vision embedding dependencies are available.

    Returns:
        Tuple of (available: bool, message: str)
    """
    try:
        import colpali_engine
        import torch
        from PIL import Image

        return True, "Vision embedding is available"

    except ImportError as e:
        missing = str(e).split("'")[1] if "'" in str(e) else "colpali-engine"
        return False, (
            f"Missing dependency: {missing}. "
            "Install with: pip install colpali-engine Pillow torch"
        )


def create_vision_embedder(
    model_name: str = "vidore/colpali-v1.0",
    device: str | None = None,
) -> ColPaliEmbedder | None:
    """Create a vision embedder if dependencies are available.

    Args:
        model_name: Model to use
        device: Device to use

    Returns:
        ColPaliEmbedder or None if dependencies missing
    """
    available, message = check_vision_available()
    if not available:
        logger.info("Vision embedding unavailable: %s", message)
        return None

    return ColPaliEmbedder(model_name=model_name, device=device)
