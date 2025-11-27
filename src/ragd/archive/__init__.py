"""Archive module for ragd export/import.

This module provides:
- Archive format specification (F-034)
- Export engine for creating archives (F-032)
- Import engine for restoring archives (F-033)
"""

from __future__ import annotations

from ragd.archive.format import (
    ARCHIVE_VERSION,
    COMPATIBLE_VERSIONS,
    ArchiveFilters,
    ArchiveManifest,
    ArchiveStatistics,
    ArchiveValidationError,
    ArchivedChunk,
    ArchivedDocument,
    ChecksumMismatchError,
    EmbeddingInfo,
    IncompatibleVersionError,
    is_version_compatible,
)
from ragd.archive.export import (
    ExportEngine,
    ExportOptions,
    ExportProgress,
    ExportResult,
)
from ragd.archive.import_ import (
    ConflictInfo,
    ConflictResolution,
    ImportEngine,
    ImportOptions,
    ImportProgress,
    ImportResult,
    ValidationResult,
)

__all__ = [
    # Format constants
    "ARCHIVE_VERSION",
    "COMPATIBLE_VERSIONS",
    # Format dataclasses
    "ArchiveManifest",
    "ArchiveStatistics",
    "ArchiveFilters",
    "EmbeddingInfo",
    "ArchivedDocument",
    "ArchivedChunk",
    # Format exceptions
    "ArchiveValidationError",
    "IncompatibleVersionError",
    "ChecksumMismatchError",
    # Format utilities
    "is_version_compatible",
    # Export
    "ExportEngine",
    "ExportOptions",
    "ExportProgress",
    "ExportResult",
    # Import
    "ImportEngine",
    "ImportOptions",
    "ImportProgress",
    "ImportResult",
    "ValidationResult",
    "ConflictResolution",
    "ConflictInfo",
]
