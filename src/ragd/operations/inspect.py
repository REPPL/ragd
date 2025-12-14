"""Database inspection utilities for troubleshooting indexing issues (v1.0.8).

This module provides utilities for inspecting the ragd index, finding
duplicates, and explaining why documents would be skipped during indexing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ragd.config import load_config
from ragd.storage import ChromaStore


@dataclass
class InspectResult:
    """Result of index inspection."""

    document_count: int
    chunk_count: int
    file_types: dict[str, int]
    storage_size_mb: float | None
    documents: list[dict[str, Any]]


@dataclass
class DuplicateGroup:
    """A group of documents with the same content hash."""

    content_hash: str
    documents: list[dict[str, Any]]

    @property
    def count(self) -> int:
        """Number of documents in this group."""
        return len(self.documents)


@dataclass
class SkipExplanation:
    """Explanation for why a file would be skipped."""

    path: str
    would_skip: bool
    reasons: list[str]
    duplicate_of: str | None = None
    content_hash: str | None = None
    supported_formats: list[str] | None = None
    extraction_error: str | None = None


def inspect_index(
    limit: int = 100,
    show_hashes: bool = False,
) -> InspectResult:
    """Inspect the current index state.

    Args:
        limit: Maximum documents to return
        show_hashes: Include content hashes in output

    Returns:
        InspectResult with index statistics and document list
    """
    config = load_config()
    store = ChromaStore(config.chroma_path)

    stats = store.get_stats()
    documents = store.list_documents()

    # Count file types
    file_types: dict[str, int] = {}
    for doc in documents:
        ft = doc.file_type.upper() if doc.file_type else "UNKNOWN"
        file_types[ft] = file_types.get(ft, 0) + 1

    # Get storage size
    storage_size_mb = None
    if hasattr(stats, "index_size_bytes") and stats.index_size_bytes:
        storage_size_mb = stats.index_size_bytes / (1024 * 1024)

    # Build document list
    doc_list = []
    for doc in documents[:limit]:
        doc_dict = {
            "id": doc.document_id,
            "path": doc.path,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "chunks": doc.chunk_count,
            "indexed_at": doc.indexed_at,
        }
        if show_hashes:
            doc_dict["content_hash"] = doc.content_hash
        doc_list.append(doc_dict)

    return InspectResult(
        document_count=len(documents),
        chunk_count=stats.chunk_count if hasattr(stats, "chunk_count") else stats.get("chunk_count", 0),
        file_types=file_types,
        storage_size_mb=storage_size_mb,
        documents=doc_list,
    )


def find_duplicates_in_index() -> list[DuplicateGroup]:
    """Find documents with duplicate content hashes in the index.

    Returns:
        List of DuplicateGroup objects for hashes with multiple documents
    """
    config = load_config()
    store = ChromaStore(config.chroma_path)

    documents = store.list_documents()

    # Group by content hash
    by_hash: dict[str, list[dict[str, Any]]] = {}
    for doc in documents:
        if not doc.content_hash:
            continue
        if doc.content_hash not in by_hash:
            by_hash[doc.content_hash] = []
        by_hash[doc.content_hash].append({
            "id": doc.document_id,
            "path": doc.path,
            "filename": doc.filename,
            "indexed_at": doc.indexed_at,
        })

    # Filter to only groups with duplicates
    duplicates = [
        DuplicateGroup(content_hash=hash_val, documents=docs)
        for hash_val, docs in by_hash.items()
        if len(docs) > 1
    ]

    return duplicates


def explain_skipped(path: Path) -> SkipExplanation:
    """Explain why a specific file would be skipped during indexing.

    Args:
        path: Path to the file to check

    Returns:
        SkipExplanation with reasons for skipping
    """
    from ragd.ingestion.extractor import extract_text
    from ragd.storage.chromadb import generate_content_hash, generate_document_id
    from ragd.utils.paths import get_file_type, is_supported_file

    config = load_config()
    store = ChromaStore(config.chroma_path)

    result = SkipExplanation(
        path=str(path),
        would_skip=False,
        reasons=[],
    )

    # Check if file exists
    if not path.exists():
        result.would_skip = True
        result.reasons.append("File does not exist")
        return result

    # Check if symlink
    if path.is_symlink():
        result.would_skip = True
        result.reasons.append("File is a symlink (skipped for security)")
        return result

    # Check format support
    if not is_supported_file(path):
        result.would_skip = True
        result.reasons.append(f"Unsupported format: {path.suffix}")
        result.supported_formats = [".pdf", ".txt", ".md", ".html", ".htm"]
        return result

    # Check if already indexed by document_id
    document_id = generate_document_id(path)
    if store.document_exists_by_id(document_id):
        result.would_skip = True
        result.reasons.append(f"Document ID already exists: {document_id}")

    # Try to extract and check content hash
    try:
        extraction = extract_text(path)
        if extraction.success and extraction.text:
            content_hash = generate_content_hash(extraction.text)
            existing = store.find_by_content_hash(content_hash)
            if existing:
                result.would_skip = True
                result.reasons.append(f"Duplicate content of: {existing.path}")
                result.duplicate_of = existing.path
                result.content_hash = content_hash
        elif not extraction.success:
            result.extraction_error = extraction.error
    except Exception as e:
        result.extraction_error = str(e)

    return result
