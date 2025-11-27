"""Vision module for multi-modal RAG support.

Provides image embedding and processing for visual content retrieval.
This module enables:
- Image extraction from documents
- Vision embeddings using ColPali/ColQwen
- Multi-modal search (text ↔ image)
"""

from ragd.vision.embedder import (
    ColPaliEmbedder,
    VisionEmbedder,
    check_vision_available,
    create_vision_embedder,
)
from ragd.vision.image import (
    ExtractedImage,
    ImageMetadata,
    check_image_extraction_available,
    check_ocr_available,
    extract_images_from_pdf,
    load_image_file,
    ocr_image_bytes,
    ocr_image_file,
)
from ragd.vision.pipeline import (
    ImageIndexResult,
    index_images_from_path,
    index_images_from_pdf,
    index_standalone_image,
)

__all__ = [
    # Embedders
    "VisionEmbedder",
    "ColPaliEmbedder",
    "check_vision_available",
    "create_vision_embedder",
    # Image processing
    "ExtractedImage",
    "ImageMetadata",
    "extract_images_from_pdf",
    "check_image_extraction_available",
    "load_image_file",
    # OCR
    "check_ocr_available",
    "ocr_image_file",
    "ocr_image_bytes",
    # Pipeline
    "ImageIndexResult",
    "index_images_from_pdf",
    "index_standalone_image",
    "index_images_from_path",
]
