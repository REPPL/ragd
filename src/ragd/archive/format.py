"""Archive format specification for ragd export/import.

This module defines the v1.0 archive format as specified in F-034.
The format is self-describing and versioned for forward compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Archive format version
ARCHIVE_VERSION = "1.1"
COMPATIBLE_VERSIONS = ["1.0", "1.1"]


@dataclass(frozen=True)
class EmbeddingInfo:
    """Embedding configuration in archive."""

    included: bool
    model: str
    dimensions: int
    format: str = "parquet"


@dataclass(frozen=True)
class ArchiveStatistics:
    """Archive statistics."""

    document_count: int
    chunk_count: int
    total_size_bytes: int = 0


@dataclass(frozen=True)
class ArchiveFilters:
    """Filters applied during export."""

    tags: list[str] = field(default_factory=list)
    project: str | None = None
    date_from: str | None = None
    date_to: str | None = None


@dataclass
class ArchiveManifest:
    """Archive manifest containing metadata and checksums.

    This is the primary descriptor of an archive file.
    """

    version: str
    created_at: str
    ragd_version: str
    statistics: ArchiveStatistics
    embeddings: EmbeddingInfo
    compression: str = "gzip"
    filters: ArchiveFilters = field(default_factory=ArchiveFilters)
    checksums: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert manifest to dictionary for JSON serialisation."""
        return {
            "$schema": "ragd-archive-v1",
            "version": self.version,
            "created_at": self.created_at,
            "ragd_version": self.ragd_version,
            "statistics": {
                "document_count": self.statistics.document_count,
                "chunk_count": self.statistics.chunk_count,
                "total_size_bytes": self.statistics.total_size_bytes,
            },
            "embeddings": {
                "included": self.embeddings.included,
                "model": self.embeddings.model,
                "dimensions": self.embeddings.dimensions,
                "format": self.embeddings.format,
            },
            "compression": self.compression,
            "filters": {
                "tags": list(self.filters.tags),
                "project": self.filters.project,
                "date_from": self.filters.date_from,
                "date_to": self.filters.date_to,
            },
            "checksums": dict(self.checksums),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ArchiveManifest:
        """Create manifest from dictionary."""
        stats_data = data.get("statistics", {})
        embed_data = data.get("embeddings", {})
        filter_data = data.get("filters", {})

        return cls(
            version=data.get("version", ARCHIVE_VERSION),
            created_at=data.get("created_at", ""),
            ragd_version=data.get("ragd_version", ""),
            statistics=ArchiveStatistics(
                document_count=stats_data.get("document_count", 0),
                chunk_count=stats_data.get("chunk_count", 0),
                total_size_bytes=stats_data.get("total_size_bytes", 0),
            ),
            embeddings=EmbeddingInfo(
                included=embed_data.get("included", False),
                model=embed_data.get("model", ""),
                dimensions=embed_data.get("dimensions", 0),
                format=embed_data.get("format", "parquet"),
            ),
            compression=data.get("compression", "gzip"),
            filters=ArchiveFilters(
                tags=filter_data.get("tags", []),
                project=filter_data.get("project"),
                date_from=filter_data.get("date_from"),
                date_to=filter_data.get("date_to"),
            ),
            checksums=data.get("checksums", {}),
        )


@dataclass
class ArchivedDocument:
    """Document metadata as stored in archive."""

    id: str
    dc_title: str
    dc_creator: list[str]
    dc_date: str | None
    dc_subject: list[str]
    ragd_source_path: str
    ragd_source_hash: str
    ragd_tags: list[str]
    ragd_ingestion_date: str
    ragd_chunk_count: int
    metadata: dict[str, Any] = field(default_factory=dict)
    # v1.1 / schema v2.1 fields
    ragd_sensitivity: str = "public"
    ragd_embedding_model: str = ""
    ragd_embedding_dimension: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialisation."""
        return {
            "id": self.id,
            "dc_title": self.dc_title,
            "dc_creator": self.dc_creator,
            "dc_date": self.dc_date,
            "dc_subject": self.dc_subject,
            "ragd_source_path": self.ragd_source_path,
            "ragd_source_hash": self.ragd_source_hash,
            "ragd_tags": self.ragd_tags,
            "ragd_ingestion_date": self.ragd_ingestion_date,
            "ragd_chunk_count": self.ragd_chunk_count,
            "metadata": self.metadata,
            # v1.1 / schema v2.1 fields
            "ragd_sensitivity": self.ragd_sensitivity,
            "ragd_embedding_model": self.ragd_embedding_model,
            "ragd_embedding_dimension": self.ragd_embedding_dimension,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ArchivedDocument:
        """Create from dictionary."""
        return cls(
            id=data.get("id", ""),
            dc_title=data.get("dc_title", ""),
            dc_creator=data.get("dc_creator", []),
            dc_date=data.get("dc_date"),
            dc_subject=data.get("dc_subject", []),
            ragd_source_path=data.get("ragd_source_path", ""),
            ragd_source_hash=data.get("ragd_source_hash", ""),
            ragd_tags=data.get("ragd_tags", []),
            ragd_ingestion_date=data.get("ragd_ingestion_date", ""),
            ragd_chunk_count=data.get("ragd_chunk_count", 0),
            metadata=data.get("metadata", {}),
            # v1.1 / schema v2.1 fields (with defaults for v1.0 archives)
            ragd_sensitivity=data.get("ragd_sensitivity", "public"),
            ragd_embedding_model=data.get("ragd_embedding_model", ""),
            ragd_embedding_dimension=data.get("ragd_embedding_dimension", 0),
        )


@dataclass
class ArchivedChunk:
    """Chunk data as stored in archive."""

    id: str
    document_id: str
    text: str
    page_numbers: list[int] = field(default_factory=list)
    section: str = ""
    char_start: int = 0
    char_end: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialisation."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "text": self.text,
            "page_numbers": self.page_numbers,
            "section": self.section,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ArchivedChunk:
        """Create from dictionary."""
        return cls(
            id=data.get("id", ""),
            document_id=data.get("document_id", ""),
            text=data.get("text", ""),
            page_numbers=data.get("page_numbers", []),
            section=data.get("section", ""),
            char_start=data.get("char_start", 0),
            char_end=data.get("char_end", 0),
            metadata=data.get("metadata", {}),
        )


class ArchiveValidationError(Exception):
    """Raised when archive validation fails."""

    pass


class IncompatibleVersionError(Exception):
    """Raised when archive version is not supported."""

    def __init__(self, archive_version: str) -> None:
        self.archive_version = archive_version
        super().__init__(
            f"Archive version {archive_version} not supported. "
            f"Compatible versions: {COMPATIBLE_VERSIONS}"
        )


class ChecksumMismatchError(Exception):
    """Raised when archive checksum verification fails."""

    def __init__(self, filename: str, expected: str, actual: str) -> None:
        self.filename = filename
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"Checksum mismatch for {filename}: expected {expected[:16]}..., "
            f"got {actual[:16]}..."
        )


def is_version_compatible(version: str) -> bool:
    """Check if archive version is compatible.

    Args:
        version: Archive format version string

    Returns:
        True if version is supported
    """
    return version in COMPATIBLE_VERSIONS
