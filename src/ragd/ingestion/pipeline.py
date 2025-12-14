"""Document ingestion pipeline for ragd.

This module orchestrates the document indexing process:
extraction -> chunking -> embedding -> storage.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from ragd.config import RagdConfig, load_config
from ragd.embedding import ChunkBoundary, create_late_chunking_embedder, get_embedder
from ragd.ingestion.chunker import chunk_text
from ragd.ingestion.extractor import ExtractionResult, extract_text
from ragd.search.bm25 import BM25Index
from ragd.storage import ChromaStore, DocumentRecord
from ragd.storage.chromadb import generate_content_hash, generate_document_id
from ragd.text import normalise_text
from ragd.text.normalise import NormalisationSettings, source_type_from_file_type
from ragd.utils.paths import discover_files, get_file_type

logger = logging.getLogger(__name__)

# Minimum characters to consider extraction successful (below triggers OCR fallback)
MIN_EXTRACTION_CHARS = 50


class FailureCategory(Enum):
    """Categories for document extraction failures."""

    IMAGE_ONLY = "image_only"  # PDF has images but no text layer
    ENCRYPTED = "encrypted"  # PDF is password-protected
    MALFORMED = "malformed"  # PDF/file is corrupted or malformed
    JS_CONTENT = "js_content"  # HTML with JavaScript-rendered content
    EMPTY_FILE = "empty_file"  # File is empty or contains no content
    TEXT_TOO_SHORT = "text_too_short"  # Extracted text below minimum threshold
    UNKNOWN = "unknown"  # Unknown failure reason


# Remediation suggestions for each failure category
FAILURE_REMEDIATION = {
    FailureCategory.IMAGE_ONLY: "This PDF appears to be scanned/image-only. OCR was attempted but may have failed. Try 're-indexing after verifying PaddleOCR is installed.",
    FailureCategory.ENCRYPTED: "This PDF is password-protected. Remove the password protection before indexing.",
    FailureCategory.MALFORMED: "This file appears to be corrupted or malformed. Try re-downloading or re-exporting from the source application.",
    FailureCategory.JS_CONTENT: "This HTML page uses JavaScript to render content. Try saving as 'Complete webpage' or use a browser extension like SingleFile.",
    FailureCategory.EMPTY_FILE: "This file contains no extractable content.",
    FailureCategory.TEXT_TOO_SHORT: "Extracted text is too short to generate meaningful chunks. The document may be mostly images or contain very little text.",
    FailureCategory.UNKNOWN: "Unknown extraction failure. Check the error message for details.",
}


def classify_failure(
    path: Path,
    result: ExtractionResult,
    error_msg: str | None = None,
) -> tuple[FailureCategory, str]:
    """Classify a document extraction failure.

    Args:
        path: Path to the document
        result: Extraction result
        error_msg: Optional error message

    Returns:
        Tuple of (FailureCategory, remediation suggestion)
    """
    file_type = get_file_type(path)
    file_size = path.stat().st_size if path.exists() else 0
    error_lower = (error_msg or "").lower()
    extraction_method = result.extraction_method or ""

    # Empty file
    if file_size == 0:
        return FailureCategory.EMPTY_FILE, FAILURE_REMEDIATION[FailureCategory.EMPTY_FILE]

    # PDF-specific failures
    if file_type == "pdf":
        # Encrypted PDF
        if "encrypted" in error_lower or "password" in error_lower:
            return FailureCategory.ENCRYPTED, FAILURE_REMEDIATION[FailureCategory.ENCRYPTED]

        # Malformed PDF
        if any(x in error_lower for x in ["syntax error", "invalid", "corrupt", "could not parse"]):
            return FailureCategory.MALFORMED, FAILURE_REMEDIATION[FailureCategory.MALFORMED]

        # Image-only PDF (no text extracted, has size suggesting content)
        if file_size > 10000 and len(result.text.strip()) == 0:
            return FailureCategory.IMAGE_ONLY, FAILURE_REMEDIATION[FailureCategory.IMAGE_ONLY]

    # HTML-specific failures
    if file_type == "html":
        # Check for JavaScript-heavy content indicators
        if len(result.text.strip()) < 50 and file_size > 5000:
            return FailureCategory.JS_CONTENT, FAILURE_REMEDIATION[FailureCategory.JS_CONTENT]

    # Text too short for chunking
    if 0 < len(result.text.strip()) < MIN_EXTRACTION_CHARS:
        return FailureCategory.TEXT_TOO_SHORT, FAILURE_REMEDIATION[FailureCategory.TEXT_TOO_SHORT]

    # Unknown
    return FailureCategory.UNKNOWN, FAILURE_REMEDIATION[FailureCategory.UNKNOWN]


def _try_ocr_fallback(path: Path, original_result: ExtractionResult) -> ExtractionResult:
    """Try OCR extraction if standard extraction yielded insufficient text.

    Args:
        path: Path to document
        original_result: Result from standard extraction

    Returns:
        OCR result if successful and better, otherwise original result
    """
    # Only apply OCR fallback to PDFs
    file_type = get_file_type(path)
    if file_type != "pdf":
        return original_result

    try:
        from ragd.logging.structured import SuppressStdout
        from ragd.ocr.pipeline import OCRPipeline

        logger.info(
            "Text extraction yielded %d chars for %s, attempting OCR fallback",
            len(original_result.text.strip()),
            path.name,
        )

        # Suppress stdout/stderr from OCR libraries (PaddleOCR prints directly)
        with SuppressStdout():
            ocr_pipeline = OCRPipeline()
            ocr_result = ocr_pipeline.process_pdf(path)

        if ocr_result.full_text and len(ocr_result.full_text.strip()) > len(
            original_result.text.strip()
        ):
            logger.info(
                "OCR extracted %d chars (vs %d from standard), using OCR result",
                len(ocr_result.full_text.strip()),
                len(original_result.text.strip()),
            )
            return ExtractionResult(
                text=ocr_result.full_text,
                extraction_method=f"ocr_{ocr_result.primary_engine}",
                success=True,
                pages=ocr_result.page_count,
                metadata={
                    "ocr_confidence": ocr_result.average_confidence,
                    "ocr_quality": ocr_result.get_quality_assessment(),
                    "ocr_quality_warning": ocr_result.get_quality_warning(),
                    "fallback_from": original_result.extraction_method,
                },
            )

    except ImportError:
        logger.debug("OCR not available for fallback (paddleocr not installed)")
    except Exception as e:
        logger.warning("OCR fallback failed for %s: %s", path.name, e)

    return original_result


@dataclass
class IndexResult:
    """Result of indexing a document."""

    document_id: str
    path: str
    filename: str
    chunk_count: int
    success: bool
    skipped: bool = False
    error: str | None = None
    image_count: int = 0  # Number of images extracted (v0.4.0)
    failure_category: FailureCategory | None = None  # Categorised failure type (v0.7.6)
    remediation: str | None = None  # Suggested fix for the failure (v0.7.6)
    quality_warning: str | None = None  # User-friendly quality note (v0.8.0)
    quality_details: dict[str, Any] | None = None  # Technical quality details (v0.8.0)


def index_document(
    path: Path,
    store: ChromaStore,
    config: RagdConfig,
    skip_duplicates: bool = True,
    bm25_index: BM25Index | None = None,
    contextual: bool | None = None,
) -> IndexResult:
    """Index a single document.

    Args:
        path: Path to document
        store: ChromaDB store
        config: Configuration
        skip_duplicates: Whether to skip already-indexed documents
        bm25_index: Optional BM25 index for hybrid search
        contextual: Override contextual retrieval setting (uses config if None)

    Returns:
        IndexResult with status
    """
    document_id = generate_document_id(path)

    # Extract text
    result = extract_text(path)
    if not result.success:
        category, remediation = classify_failure(path, result, result.error)
        return IndexResult(
            document_id=document_id,
            path=str(path),
            filename=path.name,
            chunk_count=0,
            success=False,
            error=result.error,
            failure_category=category,
            remediation=remediation,
        )

    # Try OCR fallback if extraction yielded insufficient text
    extracted_chars = len(result.text.strip())
    if extracted_chars < MIN_EXTRACTION_CHARS:
        logger.debug(
            "Extraction yielded %d chars (threshold: %d) for %s via %s, triggering OCR fallback",
            extracted_chars,
            MIN_EXTRACTION_CHARS,
            path.name,
            result.extraction_method,
        )
        result = _try_ocr_fallback(path, result)

    if not result.text.strip():
        error_msg = (
            f"No text extracted from document (method: {result.extraction_method}, "
            f"file size: {path.stat().st_size} bytes). "
            "Document may be image-only, encrypted, or empty."
        )
        category, remediation = classify_failure(path, result, error_msg)
        return IndexResult(
            document_id=document_id,
            path=str(path),
            filename=path.name,
            chunk_count=0,
            success=False,
            error=error_msg,
            failure_category=category,
            remediation=remediation,
        )

    # Apply text normalisation
    text = result.text
    file_type = get_file_type(path)
    if config.normalisation.enabled:
        settings = NormalisationSettings(
            enabled=True,
            fix_spaced_letters=config.normalisation.fix_spaced_letters,
            fix_word_boundaries=config.normalisation.fix_word_boundaries,
            fix_line_breaks=config.normalisation.fix_line_breaks,
            fix_ocr_spelling=config.normalisation.fix_ocr_spelling,
            remove_boilerplate=config.normalisation.remove_boilerplate,
            boilerplate_mode=config.normalisation.boilerplate_mode,
        )
        source_type = source_type_from_file_type(file_type)
        norm_result = normalise_text(text, source_type, settings)
        text = norm_result.text

    # Check for duplicates (use normalised text for hash)
    content_hash = generate_content_hash(text)
    if skip_duplicates and store.document_exists(content_hash):
        return IndexResult(
            document_id=document_id,
            path=str(path),
            filename=path.name,
            chunk_count=0,
            success=True,
            skipped=True,
        )

    # Chunk normalised text
    chunks = chunk_text(
        text,
        strategy=config.chunking.strategy,  # type: ignore
        chunk_size=config.chunking.chunk_size,
        overlap=config.chunking.overlap,
        min_chunk_size=config.chunking.min_chunk_size,
        metadata={
            "source": str(path),
            "filename": path.name,
            "file_type": file_type,
        },
    )

    if not chunks:
        # Provide detailed diagnostics for why chunking failed
        text_len = len(text)
        min_size = config.chunking.min_chunk_size
        # Log sample of text for debugging (first 200 chars)
        text_sample = text[:200].replace("\n", "\\n") if text else "(empty)"
        logger.debug(
            "Chunking failed for %s: %d chars, min_chunk_size=%d, strategy=%s. "
            "Text sample: %s",
            path.name,
            text_len,
            min_size,
            config.chunking.strategy,
            text_sample,
        )
        error_msg = (
            f"No chunks generated (extracted {text_len} chars, min_chunk_size={min_size}). "
            f"Text too short or filtered out. Method: {result.extraction_method}"
        )
        category, remediation = classify_failure(path, result, error_msg)
        return IndexResult(
            document_id=document_id,
            path=str(path),
            filename=path.name,
            chunk_count=0,
            success=False,
            error=error_msg,
            failure_category=category,
            remediation=remediation,
        )

    # Determine if contextual retrieval is enabled
    use_contextual = contextual if contextual is not None else config.retrieval.contextual.enabled

    # Original chunk content (for storage and BM25)
    original_chunk_texts = [c.content for c in chunks]

    # Generate context for chunks (if enabled and LLM available)
    # Embedding texts may include context prefix
    embedding_texts = original_chunk_texts.copy()
    context_texts: list[str] = []  # Store context for metadata

    if use_contextual:
        try:
            from ragd.llm.context import create_context_generator

            context_gen = create_context_generator(
                base_url=config.retrieval.contextual.base_url,
                model=config.retrieval.contextual.model,
            )

            if context_gen is not None:
                contextual_chunks = context_gen.generate_contextual_chunks(
                    chunks=[(i, c) for i, c in enumerate(original_chunk_texts)],
                    title=path.name,
                    file_type=file_type,
                )
                # Use combined text for embedding, store context separately
                embedding_texts = [cc.combined for cc in contextual_chunks]
                context_texts = [cc.context for cc in contextual_chunks]

        except (ImportError, ConnectionError, RuntimeError) as e:
            # Graceful fallback - continue without context
            logger.debug("Contextual retrieval unavailable: %s", e)

    # Generate embeddings (using context-enhanced text if available)
    # Check if late chunking is enabled and available
    use_late_chunking = config.embedding.late_chunking
    if use_late_chunking:
        late_embedder = create_late_chunking_embedder(
            model_name=config.embedding.late_chunking_model,
            device=config.embedding.device,
        )
        if late_embedder is not None:
            # Use late chunking with full document context
            chunk_boundaries = [
                ChunkBoundary(
                    start=chunk.start_char,
                    end=chunk.end_char,
                    content=embedding_texts[i],  # Use context-enhanced if available
                )
                for i, chunk in enumerate(chunks)
            ]
            embeddings = late_embedder.embed_document_chunks(text, chunk_boundaries)
        else:
            # Fall back to standard embedding
            use_late_chunking = False

    if not use_late_chunking:
        embedder = get_embedder(
            model_name=config.embedding.model,
            device=config.embedding.device,
            batch_size=config.embedding.batch_size,
        )
        embeddings = embedder.embed(embedding_texts)

    # Extract PDF metadata for document reference resolution
    pdf_metadata = {}
    if result.metadata:
        # Pass through author, author_hint, and publication_year from extraction
        if result.metadata.get("author"):
            pdf_metadata["author"] = result.metadata["author"]
        if result.metadata.get("author_hint"):
            pdf_metadata["author_hint"] = result.metadata["author_hint"]
        if result.metadata.get("publication_year"):
            pdf_metadata["publication_year"] = result.metadata["publication_year"]
        if result.metadata.get("title"):
            pdf_metadata["title"] = result.metadata["title"]

    # Prepare metadata for each chunk
    metadatas = []
    for i, chunk in enumerate(chunks):
        metadata = {
            "chunk_index": chunk.index,
            "start_char": chunk.start_char,
            "end_char": chunk.end_char,
            "token_count": chunk.token_count,
            "source": str(path),
            "filename": path.name,
            "file_type": file_type,
            **pdf_metadata,  # Include author, author_hint, publication_year
        }
        if result.pages:
            metadata["pages"] = result.pages
        # Add context if generated
        if context_texts and i < len(context_texts):
            metadata["context"] = context_texts[i]
        metadatas.append(metadata)

    # Determine which embedding model was used
    if use_late_chunking:
        embedding_model = config.embedding.late_chunking_model
        # Late chunking models have varying dimensions; get from embedder
        embedding_dimension = late_embedder.dimension if late_embedder else config.embedding.dimension
    else:
        embedding_model = config.embedding.model
        embedding_dimension = config.embedding.dimension

    # Create document record
    document_record = DocumentRecord(
        document_id=document_id,
        path=str(path),
        filename=path.name,
        file_type=file_type,
        file_size=path.stat().st_size,
        chunk_count=len(chunks),
        indexed_at=datetime.now().isoformat(),
        content_hash=content_hash,
        metadata={
            "pages": result.pages,
            "extraction_method": result.extraction_method,
            "normalised": config.normalisation.enabled,
            "contextual": bool(context_texts),  # Was context generated?
            "late_chunking": use_late_chunking,  # Was late chunking used?
            # v2.1: Track embedding model for multi-modal and archive compatibility
            "embedding_model": embedding_model,
            "embedding_dimension": embedding_dimension,
        },
    )

    # Store in ChromaDB (use original content for display)
    store.add_document(
        document_id=document_id,
        chunks=original_chunk_texts,
        embeddings=embeddings,
        metadatas=metadatas,
        document_record=document_record,
    )

    # Add to BM25 index for hybrid search (use original content)
    if bm25_index is not None:
        chunk_tuples = [
            (f"{document_id}_chunk_{i}", content)
            for i, content in enumerate(original_chunk_texts)
        ]
        bm25_index.add_chunks(document_id, chunk_tuples)

    # Extract and index images from PDFs (v0.4.0 multi-modal support)
    image_count = 0
    if config.multi_modal.enabled and file_type == "pdf":
        try:
            from ragd.storage.images import ImageStore
            from ragd.vision.pipeline import index_images_from_pdf

            image_store = ImageStore(
                config.chroma_path,
                dimension=config.multi_modal.vision_dimension,
            )
            image_result = index_images_from_pdf(
                path,
                document_id=document_id,
                store=image_store,
                config=config,
                skip_duplicates=skip_duplicates,
            )
            if image_result.success:
                image_count = image_result.image_count
        except ImportError:
            # Vision dependencies not installed - continue without images
            logger.debug("Vision dependencies not installed for %s", path.name)
        except (OSError, ValueError, RuntimeError) as e:
            # Log but don't fail document indexing due to image extraction
            logger.debug("Image extraction failed for %s: %s", path.name, e)

    # Determine quality warnings based on extraction method and metadata
    quality_warning: str | None = None
    quality_details: dict[str, Any] | None = None

    if result.extraction_method and result.extraction_method.startswith("ocr_"):
        ocr_confidence = result.metadata.get("ocr_confidence", 0) if result.metadata else 0
        ocr_quality = result.metadata.get("ocr_quality", "") if result.metadata else ""
        ocr_warning = result.metadata.get("ocr_quality_warning") if result.metadata else None

        quality_details = {
            "extraction_method": result.extraction_method,
            "ocr_confidence": ocr_confidence,
            "ocr_quality": ocr_quality,
        }

        # Use warning from OCR pipeline if available, otherwise generate one
        if ocr_warning:
            quality_warning = ocr_warning
        elif ocr_quality == "poor" or ocr_confidence < 0.3:
            quality_warning = f"Scanned document - OCR quality {ocr_quality or 'poor'}"
        elif ocr_quality == "fair" or ocr_confidence < 0.5:
            quality_warning = "OCR quality fair - some text may be inaccurate"

    return IndexResult(
        document_id=document_id,
        path=str(path),
        filename=path.name,
        chunk_count=len(chunks),
        success=True,
        image_count=image_count,
        quality_warning=quality_warning,
        quality_details=quality_details,
    )


def index_path(
    path: Path,
    config: RagdConfig | None = None,
    recursive: bool = True,
    skip_duplicates: bool = True,
    progress_callback: Callable[[int, int, str], None] | None = None,
    contextual: bool | None = None,
) -> list[IndexResult]:
    """Index documents from a path.

    Args:
        path: File or directory path
        config: Configuration (loads default if not provided)
        recursive: Whether to search directories recursively
        skip_duplicates: Whether to skip already-indexed documents
        progress_callback: Optional callback for progress updates (current, total, filename)
        contextual: Override contextual retrieval setting (uses config if None)

    Returns:
        List of IndexResult for each document
    """
    if config is None:
        config = load_config()

    # Discover files
    files = discover_files(path, recursive=recursive)
    if not files:
        return []

    # Initialise stores
    store = ChromaStore(config.chroma_path)
    bm25_index = BM25Index(config.chroma_path / "bm25.db")

    results = []
    total = len(files)

    try:
        for i, file_path in enumerate(files):
            # Show current file being processed (1-based for display)
            if progress_callback:
                progress_callback(i + 1, total, file_path.name)

            result = index_document(
                file_path,
                store=store,
                config=config,
                skip_duplicates=skip_duplicates,
                bm25_index=bm25_index,
                contextual=contextual,
            )
            results.append(result)

        # Final callback to mark all complete
        if progress_callback:
            progress_callback(total, total, "")
    finally:
        bm25_index.close()

    return results
