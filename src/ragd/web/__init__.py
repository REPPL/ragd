"""Web archive, folder watching, and HTML processing module for ragd.

This module provides:
- Web archive support (F-038): Parse and index SingleFile HTML archives
- Folder watching (F-037): Auto-index new and modified files
- Advanced HTML processing (F-039): Fast parsing, metadata, structure
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
from ragd.web.parser import (
    ComplexityTier,
    ParseResult,
    detect_complexity,
    get_attribute,
    get_element_by_selector,
    parse_html,
    SELECTOLAX_AVAILABLE as PARSER_SELECTOLAX_AVAILABLE,
    BEAUTIFULSOUP_AVAILABLE,
)
from ragd.web.metadata import (
    HTMLMetadata,
    extract_metadata,
)
from ragd.web.structure import (
    CodeBlockInfo,
    HeadingInfo,
    HTMLStructure,
    ListInfo,
    TableInfo,
    extract_structure,
    get_text_with_structure,
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
    # HTML parser (F-039)
    "ComplexityTier",
    "ParseResult",
    "parse_html",
    "detect_complexity",
    "get_element_by_selector",
    "get_attribute",
    "BEAUTIFULSOUP_AVAILABLE",
    # HTML metadata (F-039)
    "HTMLMetadata",
    "extract_metadata",
    # HTML structure (F-039)
    "HTMLStructure",
    "HeadingInfo",
    "TableInfo",
    "ListInfo",
    "CodeBlockInfo",
    "extract_structure",
    "get_text_with_structure",
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
