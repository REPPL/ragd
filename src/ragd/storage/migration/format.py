"""Migration data format definitions (F-075).

Defines the intermediate format for migrating data between backends.
The format is JSON-serialisable for portability and debugging.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class MigratedChunk:
    """Individual chunk data for migration.

    Contains all information needed to recreate a chunk in a new backend.
    """

    chunk_id: str
    document_id: str
    content: str
    embedding: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialisation."""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "content": self.content,
            "embedding": self.embedding,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MigratedChunk:
        """Create from dictionary."""
        return cls(
            chunk_id=data["chunk_id"],
            document_id=data["document_id"],
            content=data["content"],
            embedding=data["embedding"],
            metadata=data.get("metadata", {}),
        )


@dataclass
class MigratedDocument:
    """Document metadata for migration."""

    document_id: str
    path: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialisation."""
        return {
            "document_id": self.document_id,
            "path": self.path,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MigratedDocument:
        """Create from dictionary."""
        return cls(
            document_id=data["document_id"],
            path=data["path"],
            metadata=data.get("metadata", {}),
        )


@dataclass
class MigrationManifest:
    """Manifest describing migration data.

    Contains metadata about the migration and the data being transferred.
    """

    version: str = "1.0"
    source_backend: str = ""
    target_backend: str = ""
    export_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    total_documents: int = 0
    total_chunks: int = 0
    embedding_model: str = ""
    embedding_dimension: int = 384
    checksum: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialisation."""
        return {
            "version": self.version,
            "source_backend": self.source_backend,
            "target_backend": self.target_backend,
            "export_timestamp": self.export_timestamp,
            "total_documents": self.total_documents,
            "total_chunks": self.total_chunks,
            "embedding_model": self.embedding_model,
            "embedding_dimension": self.embedding_dimension,
            "checksum": self.checksum,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MigrationManifest:
        """Create from dictionary."""
        return cls(
            version=data.get("version", "1.0"),
            source_backend=data.get("source_backend", ""),
            target_backend=data.get("target_backend", ""),
            export_timestamp=data.get("export_timestamp", ""),
            total_documents=data.get("total_documents", 0),
            total_chunks=data.get("total_chunks", 0),
            embedding_model=data.get("embedding_model", ""),
            embedding_dimension=data.get("embedding_dimension", 384),
            checksum=data.get("checksum", ""),
        )

    def save(self, path: Path) -> None:
        """Save manifest to file."""
        path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: Path) -> MigrationManifest:
        """Load manifest from file."""
        data = json.loads(path.read_text())
        return cls.from_dict(data)


@dataclass
class MigrationCheckpoint:
    """Checkpoint for resumable migration.

    Tracks progress so interrupted migrations can be resumed.
    """

    manifest: MigrationManifest
    chunks_migrated: int = 0
    documents_migrated: int = 0
    last_chunk_id: str = ""
    last_document_id: str = ""
    errors: list[str] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def progress_percent(self) -> float:
        """Calculate migration progress percentage."""
        if self.manifest.total_chunks == 0:
            return 100.0
        return (self.chunks_migrated / self.manifest.total_chunks) * 100

    @property
    def is_complete(self) -> bool:
        """Check if migration is complete."""
        return self.chunks_migrated >= self.manifest.total_chunks

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialisation."""
        return {
            "manifest": self.manifest.to_dict(),
            "chunks_migrated": self.chunks_migrated,
            "documents_migrated": self.documents_migrated,
            "last_chunk_id": self.last_chunk_id,
            "last_document_id": self.last_document_id,
            "errors": self.errors,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MigrationCheckpoint:
        """Create from dictionary."""
        return cls(
            manifest=MigrationManifest.from_dict(data["manifest"]),
            chunks_migrated=data.get("chunks_migrated", 0),
            documents_migrated=data.get("documents_migrated", 0),
            last_chunk_id=data.get("last_chunk_id", ""),
            last_document_id=data.get("last_document_id", ""),
            errors=data.get("errors", []),
            started_at=data.get("started_at", ""),
            updated_at=data.get("updated_at", ""),
        )

    def save(self, path: Path) -> None:
        """Save checkpoint to file."""
        self.updated_at = datetime.now().isoformat()
        path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: Path) -> MigrationCheckpoint:
        """Load checkpoint from file."""
        data = json.loads(path.read_text())
        return cls.from_dict(data)
