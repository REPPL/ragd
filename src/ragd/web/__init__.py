"""Web archive and folder watching module for ragd.

This module provides:
- Web archive support (F-038): Parse and index SingleFile HTML archives
- Folder watching (F-037): Auto-index new and modified files
"""

from __future__ import annotations

from ragd.web.archive import (
    ExtractedWebContent,
    WebArchiveMetadata,
    WebArchiveProcessor,
    extract_singlefile_metadata,
    extract_web_content,
    generate_reader_view,
    is_singlefile_archive,
    SELECTOLAX_AVAILABLE,
    TRAFILATURA_AVAILABLE,
)
from ragd.web.watcher import (
    DEFAULT_DEBOUNCE_SECONDS,
    DEFAULT_EXCLUDES,
    DEFAULT_MAX_FILE_SIZE_MB,
    DEFAULT_PATTERNS,
    FolderWatcher,
    IndexEventHandler,
    WatchConfig,
    WatchEvent,
    WatchStatus,
    WATCHDOG_AVAILABLE,
    should_index,
)

__all__ = [
    # Web archive (F-038)
    "WebArchiveMetadata",
    "ExtractedWebContent",
    "WebArchiveProcessor",
    "is_singlefile_archive",
    "extract_singlefile_metadata",
    "extract_web_content",
    "generate_reader_view",
    "SELECTOLAX_AVAILABLE",
    "TRAFILATURA_AVAILABLE",
    # Folder watching (F-037)
    "WatchConfig",
    "WatchStatus",
    "WatchEvent",
    "FolderWatcher",
    "IndexEventHandler",
    "should_index",
    "WATCHDOG_AVAILABLE",
    # Default configuration
    "DEFAULT_PATTERNS",
    "DEFAULT_EXCLUDES",
    "DEFAULT_DEBOUNCE_SECONDS",
    "DEFAULT_MAX_FILE_SIZE_MB",
]
