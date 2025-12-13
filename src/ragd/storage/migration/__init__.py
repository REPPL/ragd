"""Backend migration module for ragd (F-075).

This module provides tools for migrating data between vector store backends
(ChromaDB, FAISS) without re-indexing documents.

Example:
    >>> from ragd.storage.migration import MigrationEngine
    >>> engine = MigrationEngine()
    >>> result = engine.migrate(
    ...     source_backend="chromadb",
    ...     target_backend="faiss",
    ...     validate=True,
    ... )
    >>> print(result.chunks_migrated)
"""

from __future__ import annotations

from ragd.storage.migration.engine import (
    MigrationEngine,
    MigrationResult,
)
from ragd.storage.migration.format import (
    MigratedChunk,
    MigratedDocument,
    MigrationCheckpoint,
    MigrationManifest,
)

__all__ = [
    "MigrationManifest",
    "MigratedChunk",
    "MigratedDocument",
    "MigrationCheckpoint",
    "MigrationEngine",
    "MigrationResult",
]
