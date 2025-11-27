"""Vision ingestion pipeline for multi-modal RAG.

This module provides image extraction and embedding during document indexing,
enabling text-to-image and image-to-image search capabilities.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from ragd.config import RagdConfig
from ragd.storage.images import (
    ImageRecord,
    ImageStore,
    generate_image_content_hash,
    generate_image_id,
)
from ragd.vision.embedder import VisionEmbedder, create_vision_embedder
from ragd.vision.image import (
    ExtractedImage,
    check_image_extraction_available,
    extract_images_from_pdf,
    load_image_file,
)

logger = logging.getLogger(__name__)


@dataclass
class ImageIndexResult:
    """Result of indexing images from a document."""

    document_id: str
    image_count: int
    success: bool
    skipped_count: int = 0
    error: str | None = None
    image_ids: list[str] | None = None
    ocr_text: str | None = None  # Extracted OCR text (if performed)
    ocr_confidence: float = 0.0  # Average OCR confidence


def index_images_from_pdf(
    pdf_path: Path,
    document_id: str,
    store: ImageStore,
    config: RagdConfig,
    embedder: VisionEmbedder | None = None,
    skip_duplicates: bool = True,
    save_images: bool = True,
) -> ImageIndexResult:
    """Extract and index images from a PDF document.

    Args:
        pdf_path: Path to PDF file
        document_id: Parent document ID
        store: Image store
        config: Configuration
        embedder: Vision embedder (created if not provided)
        skip_duplicates: Skip already-indexed images
        save_images: Save image files to disk

    Returns:
        ImageIndexResult with status
    """
    # Check if multi-modal is enabled
    if not config.multi_modal.enabled:
        return ImageIndexResult(
            document_id=document_id,
            image_count=0,
            success=True,
            error="Multi-modal support disabled in config",
        )

    # Check dependencies
    available, message = check_image_extraction_available()
    if not available:
        return ImageIndexResult(
            document_id=document_id,
            image_count=0,
            success=False,
            error=message,
        )

    # Extract images from PDF
    try:
        extracted = extract_images_from_pdf(
            pdf_path,
            min_width=config.multi_modal.min_image_width,
            min_height=config.multi_modal.min_image_height,
            document_id=document_id,
        )
    except Exception as e:
        logger.error("Failed to extract images from %s: %s", pdf_path, e)
        return ImageIndexResult(
            document_id=document_id,
            image_count=0,
            success=False,
            error=str(e),
        )

    if not extracted:
        logger.debug("No images found in %s", pdf_path)
        return ImageIndexResult(
            document_id=document_id,
            image_count=0,
            success=True,
        )

    # Get or create vision embedder
    if embedder is None:
        embedder = create_vision_embedder(
            model_name=config.multi_modal.vision_model,
            device=None,  # Auto-detect
        )

    if embedder is None:
        return ImageIndexResult(
            document_id=document_id,
            image_count=0,
            success=False,
            error="Vision embedder not available",
        )

    # Process images
    indexed_count = 0
    skipped_count = 0
    image_ids = []

    for extracted_img in extracted:
        # Check for duplicates
        content_hash = generate_image_content_hash(extracted_img.data)
        if skip_duplicates and store.image_exists(content_hash):
            skipped_count += 1
            continue

        # Generate image ID
        image_id = generate_image_id(
            extracted_img.data,
            document_id=document_id,
            page_number=extracted_img.metadata.page_number or 0,
        )

        # Generate embedding
        try:
            embedding = embedder.embed_image(extracted_img.data)
        except Exception as e:
            logger.warning("Failed to embed image %s: %s", image_id, e)
            continue

        # Save image to disk (if enabled)
        if save_images:
            images_dir = config.images_path
            images_dir.mkdir(parents=True, exist_ok=True)
            image_path = images_dir / f"{image_id}.{extracted_img.metadata.format}"
            extracted_img.save(image_path)

        # Create record
        record = ImageRecord(
            image_id=image_id,
            document_id=document_id,
            source_path=str(pdf_path),
            width=extracted_img.metadata.width,
            height=extracted_img.metadata.height,
            format=extracted_img.metadata.format,
            size_bytes=extracted_img.metadata.size_bytes,
            page_number=extracted_img.metadata.page_number,
            indexed_at=datetime.now().isoformat(),
            content_hash=content_hash,
            caption=extracted_img.caption,
            metadata={
                "colorspace": extracted_img.metadata.colorspace,
                "bits_per_component": extracted_img.metadata.bits_per_component,
                "vision_model": embedder.model_name,
                "vision_dimension": embedder.dimension,
            },
        )

        # Store in ChromaDB
        store.add_image(image_id, embedding, record)
        image_ids.append(image_id)
        indexed_count += 1

    logger.info(
        "Indexed %d images from %s (skipped %d duplicates)",
        indexed_count,
        pdf_path.name,
        skipped_count,
    )

    return ImageIndexResult(
        document_id=document_id,
        image_count=indexed_count,
        success=True,
        skipped_count=skipped_count,
        image_ids=image_ids,
    )


def index_standalone_image(
    image_path: Path,
    store: ImageStore,
    config: RagdConfig,
    embedder: VisionEmbedder | None = None,
    skip_duplicates: bool = True,
    document_id: str = "",
    perform_ocr: bool = False,
    ocr_lang: str = "en",
) -> ImageIndexResult:
    """Index a standalone image file.

    Args:
        image_path: Path to image file
        store: Image store
        config: Configuration
        embedder: Vision embedder (created if not provided)
        skip_duplicates: Skip if already indexed
        document_id: Optional document ID to link to
        perform_ocr: Extract text from image using OCR
        ocr_lang: Language code for OCR

    Returns:
        ImageIndexResult with status (includes ocr_text if OCR performed)
    """
    if not config.multi_modal.enabled:
        return ImageIndexResult(
            document_id=document_id,
            image_count=0,
            success=True,
            error="Multi-modal support disabled in config",
        )

    # Load image
    try:
        extracted = load_image_file(image_path)
    except Exception as e:
        return ImageIndexResult(
            document_id=document_id,
            image_count=0,
            success=False,
            error=str(e),
        )

    # Check size filters
    if (
        extracted.metadata.width < config.multi_modal.min_image_width
        or extracted.metadata.height < config.multi_modal.min_image_height
    ):
        return ImageIndexResult(
            document_id=document_id,
            image_count=0,
            success=True,
            skipped_count=1,
            error="Image too small",
        )

    # Check for duplicates
    content_hash = generate_image_content_hash(extracted.data)
    if skip_duplicates and store.image_exists(content_hash):
        return ImageIndexResult(
            document_id=document_id,
            image_count=0,
            success=True,
            skipped_count=1,
        )

    # Get or create embedder
    if embedder is None:
        embedder = create_vision_embedder(
            model_name=config.multi_modal.vision_model,
        )

    if embedder is None:
        return ImageIndexResult(
            document_id=document_id,
            image_count=0,
            success=False,
            error="Vision embedder not available",
        )

    # Generate image ID
    image_id = generate_image_id(extracted.data)

    # Generate embedding
    try:
        embedding = embedder.embed_image(extracted.data)
    except Exception as e:
        return ImageIndexResult(
            document_id=document_id,
            image_count=0,
            success=False,
            error=f"Embedding failed: {e}",
        )

    # Optionally perform OCR
    ocr_text: str | None = None
    ocr_confidence: float = 0.0

    if perform_ocr:
        try:
            from ragd.vision.image import check_ocr_available, ocr_image_file

            available, _ = check_ocr_available()
            if available:
                ocr_text, ocr_confidence = ocr_image_file(
                    image_path,
                    lang=ocr_lang,
                )
                logger.debug(
                    "OCR extracted %d chars from %s (confidence: %.2f)",
                    len(ocr_text),
                    image_path.name,
                    ocr_confidence,
                )
        except Exception as e:
            logger.warning("OCR failed for %s: %s", image_path.name, e)

    # Create record
    record_metadata = {
        "vision_model": embedder.model_name,
        "vision_dimension": embedder.dimension,
    }
    if ocr_text:
        record_metadata["ocr_text"] = ocr_text[:1000]  # Truncate for metadata
        record_metadata["ocr_confidence"] = ocr_confidence

    record = ImageRecord(
        image_id=image_id,
        document_id=document_id,
        source_path=str(image_path),
        width=extracted.metadata.width,
        height=extracted.metadata.height,
        format=extracted.metadata.format,
        size_bytes=extracted.metadata.size_bytes,
        page_number=None,
        indexed_at=datetime.now().isoformat(),
        content_hash=content_hash,
        metadata=record_metadata,
    )

    # Store
    store.add_image(image_id, embedding, record)

    return ImageIndexResult(
        document_id=document_id,
        image_count=1,
        success=True,
        image_ids=[image_id],
        ocr_text=ocr_text,
        ocr_confidence=ocr_confidence,
    )


def index_images_from_path(
    path: Path,
    config: RagdConfig,
    recursive: bool = True,
    skip_duplicates: bool = True,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> list[ImageIndexResult]:
    """Index images from a path (files or directories).

    Handles both standalone images and images embedded in PDFs.

    Args:
        path: File or directory path
        config: Configuration
        recursive: Search directories recursively
        skip_duplicates: Skip already-indexed images
        progress_callback: Progress callback (current, total, filename)

    Returns:
        List of ImageIndexResult for each processed item
    """
    if not config.multi_modal.enabled:
        return []

    # Initialise stores and embedder
    store = ImageStore(config.chroma_path, dimension=config.multi_modal.vision_dimension)
    embedder = create_vision_embedder(
        model_name=config.multi_modal.vision_model,
    )

    if embedder is None:
        logger.warning("Vision embedder not available")
        return []

    # Discover files
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"}
    pdf_extension = ".pdf"

    results = []

    if path.is_file():
        files = [path]
    else:
        if recursive:
            files = list(path.rglob("*"))
        else:
            files = list(path.glob("*"))
        files = [f for f in files if f.is_file()]

    # Separate PDFs and images
    pdf_files = [f for f in files if f.suffix.lower() == pdf_extension]
    image_files = [f for f in files if f.suffix.lower() in image_extensions]

    total = len(pdf_files) + len(image_files)
    current = 0

    # Process PDFs (extract images)
    for pdf_path in pdf_files:
        current += 1
        if progress_callback:
            progress_callback(current, total, pdf_path.name)

        # Generate document ID for linking
        from ragd.storage.chromadb import generate_document_id

        document_id = generate_document_id(pdf_path)

        result = index_images_from_pdf(
            pdf_path,
            document_id=document_id,
            store=store,
            config=config,
            embedder=embedder,
            skip_duplicates=skip_duplicates,
        )
        results.append(result)

    # Process standalone images
    for image_path in image_files:
        current += 1
        if progress_callback:
            progress_callback(current, total, image_path.name)

        result = index_standalone_image(
            image_path,
            store=store,
            config=config,
            embedder=embedder,
            skip_duplicates=skip_duplicates,
        )
        results.append(result)

    return results
