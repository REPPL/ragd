"""Type definitions for the storage layer.

This module defines the core data structures used across all vector store backends.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class BackendType(Enum):
    """Supported vector store backends."""

    CHROMADB = "chromadb"
    FAISS = "faiss"


class HealthStatus(Enum):
    """Health check status for backends."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class VectorSearchResult:
    """Result from a vector similarity search.

    All backends MUST normalise scores to 0-1 range where:
    - 1.0 = identical/perfect match
    - 0.0 = completely dissimilar

    This normalisation is CRITICAL for Agentic RAG which uses
    score thresholds to determine retrieval quality.
    """

    id: str
    content: str
    score: float  # MUST be 0-1 range (normalised)
    metadata: dict[str, Any] = field(default_factory=dict)
    raw_distance: float | None = None  # Original backend distance (optional)

    def __post_init__(self) -> None:
        """Validate score is in expected range."""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(
                f"Score must be in range [0, 1], got {self.score}. "
                "Backend adapter must normalise distances to scores."
            )


@dataclass
class StorageStats:
    """Statistics about vector store contents."""

    document_count: int
    chunk_count: int
    backend: BackendType
    dimension: int | None = None
    index_size_bytes: int | None = None
    last_modified: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialisation."""
        return {
            "document_count": self.document_count,
            "chunk_count": self.chunk_count,
            "backend": self.backend.value,
            "dimension": self.dimension,
            "index_size_bytes": self.index_size_bytes,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
        }


@dataclass
class BackendHealth:
    """Health check result for a backend."""

    backend: BackendType
    status: HealthStatus
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    latency_ms: float | None = None

    @property
    def is_healthy(self) -> bool:
        """Check if backend is operational."""
        return self.status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)


@dataclass
class MigrationProgress:
    """Progress tracking for backend migration."""

    source: BackendType
    target: BackendType
    total_chunks: int
    migrated_chunks: int
    current_document: str = ""
    errors: list[str] = field(default_factory=list)

    @property
    def progress_percent(self) -> float:
        """Calculate migration progress percentage."""
        if self.total_chunks == 0:
            return 100.0
        return (self.migrated_chunks / self.total_chunks) * 100

    @property
    def is_complete(self) -> bool:
        """Check if migration is complete."""
        return self.migrated_chunks >= self.total_chunks
