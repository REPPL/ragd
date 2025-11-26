"""Document ingestion pipeline for ragd."""

from ragd.ingestion.extractor import (
    ExtractionResult,
    TextExtractor,
    extract_text,
)
from ragd.ingestion.chunker import Chunk, chunk_text
from ragd.ingestion.pipeline import IndexResult, index_document, index_path
from ragd.utils.paths import discover_files

__all__ = [
    "ExtractionResult",
    "TextExtractor",
    "extract_text",
    "Chunk",
    "chunk_text",
    "IndexResult",
    "index_document",
    "index_path",
    "discover_files",
]
