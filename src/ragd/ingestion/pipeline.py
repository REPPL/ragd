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
from ragd.embedding import get_embedder
from ragd.ingestion.chunker import Chunk, chunk_text
from ragd.ingestion.extractor import extract_text
from ragd.storage import ChromaStore, DocumentRecord
from ragd.storage.chromadb import generate_content_hash, generate_document_id
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


def index_document(
    path: Path,
    store: ChromaStore,
    config: RagdConfig,
    skip_duplicates: bool = True,
) -> IndexResult:
    """Index a single document.

    Args:
        path: Path to document
        store: ChromaDB store
        config: Configuration
        skip_duplicates: Whether to skip already-indexed documents

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
            error="No text extracted from document",
        )

    # Check for duplicates
    content_hash = generate_content_hash(result.text)
    if skip_duplicates and store.document_exists(content_hash):
        return IndexResult(
            document_id=document_id,
            path=str(path),
            filename=path.name,
            chunk_count=0,
            success=True,
            skipped=True,
        )

    # Chunk text
    chunks = chunk_text(
        result.text,
        strategy=config.chunking.strategy,  # type: ignore
        chunk_size=config.chunking.chunk_size,
        overlap=config.chunking.overlap,
        min_chunk_size=config.chunking.min_chunk_size,
        metadata={
            "source": str(path),
            "filename": path.name,
            "file_type": get_file_type(path),
        },
    )

    if not chunks:
        return IndexResult(
            document_id=document_id,
            path=str(path),
            filename=path.name,
            chunk_count=0,
            success=False,
            error="No chunks generated from document",
        )

    # Generate embeddings
    embedder = get_embedder(
        model_name=config.embedding.model,
        device=config.embedding.device,
        batch_size=config.embedding.batch_size,
    )

    chunk_texts = [c.content for c in chunks]
    embeddings = embedder.embed(chunk_texts)

    # Prepare metadata for each chunk
    metadatas = []
    for chunk in chunks:
        metadata = {
            "chunk_index": chunk.index,
            "start_char": chunk.start_char,
            "end_char": chunk.end_char,
            "token_count": chunk.token_count,
            "source": str(path),
            "filename": path.name,
            "file_type": get_file_type(path),
        }
        if result.pages:
            metadata["pages"] = result.pages
        metadatas.append(metadata)

    # Create document record
    document_record = DocumentRecord(
        document_id=document_id,
        path=str(path),
        filename=path.name,
        file_type=get_file_type(path),
        file_size=path.stat().st_size,
        chunk_count=len(chunks),
        indexed_at=datetime.now().isoformat(),
        content_hash=content_hash,
        metadata={
            "pages": result.pages,
            "extraction_method": result.extraction_method,
        },
    )

    # Store in ChromaDB
    store.add_document(
        document_id=document_id,
        chunks=chunk_texts,
        embeddings=embeddings,
        metadatas=metadatas,
        document_record=document_record,
    )

    return IndexResult(
        document_id=document_id,
        path=str(path),
        filename=path.name,
        chunk_count=len(chunks),
        success=True,
    )


def index_path(
    path: Path,
    config: RagdConfig | None = None,
    recursive: bool = True,
    skip_duplicates: bool = True,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> list[IndexResult]:
    """Index documents from a path.

    Args:
        path: File or directory path
        config: Configuration (loads default if not provided)
        recursive: Whether to search directories recursively
        skip_duplicates: Whether to skip already-indexed documents
        progress_callback: Optional callback for progress updates (current, total, filename)

    Returns:
        List of IndexResult for each document
    """
    if config is None:
        config = load_config()

    # Discover files
    files = discover_files(path, recursive=recursive)
    if not files:
        return []

    # Initialise store
    store = ChromaStore(config.chroma_path)

    results = []
    total = len(files)

    for i, file_path in enumerate(files):
        if progress_callback:
            progress_callback(i + 1, total, file_path.name)

        result = index_document(
            file_path,
            store=store,
            config=config,
            skip_duplicates=skip_duplicates,
        )
        results.append(result)

    return results
