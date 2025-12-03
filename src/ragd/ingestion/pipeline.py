"""Document ingestion pipeline for ragd.

This module orchestrates the document indexing process:
extraction -> chunking -> embedding -> storage.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from ragd.config import RagdConfig, load_config
from ragd.embedding import get_embedder, ChunkBoundary, create_late_chunking_embedder
from ragd.ingestion.chunker import Chunk, chunk_text
from ragd.ingestion.extractor import extract_text
from ragd.search.bm25 import BM25Index
from ragd.storage import ChromaStore, DocumentRecord
from ragd.storage.chromadb import generate_content_hash, generate_document_id
from ragd.text import TextNormaliser, normalise_text
from ragd.text.normalise import NormalisationSettings, source_type_from_file_type
from ragd.utils.paths import discover_files, get_file_type


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
        return IndexResult(
            document_id=document_id,
            path=str(path),
            filename=path.name,
            chunk_count=0,
            success=False,
            error=result.error,
        )

    if not result.text.strip():
        return IndexResult(
            document_id=document_id,
            path=str(path),
            filename=path.name,
            chunk_count=0,
            success=False,
            error=f"No text extracted from document (method: {result.extraction_method}, "
                  f"file size: {path.stat().st_size} bytes). "
                  "Document may be image-only, encrypted, or empty.",
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
        return IndexResult(
            document_id=document_id,
            path=str(path),
            filename=path.name,
            chunk_count=0,
            success=False,
            error=f"No chunks generated (extracted {text_len} chars, min_chunk_size={min_size}). "
                  f"Text too short or filtered out. Method: {result.extraction_method}",
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

        except Exception:
            # Graceful fallback - continue without context
            pass

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
            pass
        except Exception:
            # Log but don't fail document indexing due to image extraction
            pass

    return IndexResult(
        document_id=document_id,
        path=str(path),
        filename=path.name,
        chunk_count=len(chunks),
        success=True,
        image_count=image_count,
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
            # Show current file being processed (completed count is i, not i+1)
            if progress_callback:
                progress_callback(i, total, file_path.name)

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
