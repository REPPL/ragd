"""Metadata schema migration utilities.

Provides migration functions for upgrading document metadata between
schema versions. See ADR-0023 for migration strategy.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from ragd.metadata.schema import DocumentMetadata

logger = logging.getLogger(__name__)

# Schema version constants
SCHEMA_V1 = "1.0"
SCHEMA_V2 = "2.0"
CURRENT_SCHEMA = SCHEMA_V2


def get_schema_version(data: dict[str, Any]) -> str:
    """Determine the schema version of stored metadata.

    Args:
        data: Raw metadata dictionary from storage

    Returns:
        Schema version string ("1.0", "2.0", etc.)
    """
    # v2.0+ has explicit version field
    if "ragd_schema_version" in data:
        return data["ragd_schema_version"]

    # v1.0 has source_path but not ragd_source_path
    if "source_path" in data and "ragd_source_path" not in data:
        return SCHEMA_V1

    # Default to current if structure unclear
    return CURRENT_SCHEMA


def needs_migration(data: dict[str, Any]) -> bool:
    """Check if metadata needs migration to current schema.

    Args:
        data: Raw metadata dictionary from storage

    Returns:
        True if migration is needed
    """
    return get_schema_version(data) != CURRENT_SCHEMA


def migrate_v1_to_v2(v1_data: dict[str, Any]) -> DocumentMetadata:
    """Migrate v0.1.0 metadata to v0.2.0 schema.

    v1.0 schema fields:
    - source_path: str
    - content_hash: str
    - chunk_count: int
    - indexed_at: datetime | str
    - file_type: str
    - page_count: int (PDFs only)

    Args:
        v1_data: Dictionary with v1.0 schema fields

    Returns:
        DocumentMetadata instance with v2.0 schema
    """
    # Parse indexed_at datetime
    indexed_at = v1_data.get("indexed_at")
    if isinstance(indexed_at, str):
        try:
            indexed_at = datetime.fromisoformat(indexed_at)
        except ValueError:
            indexed_at = None

    # Derive title from filename
    source_path = v1_data.get("source_path", "")
    title = Path(source_path).stem if source_path else ""

    # Map file_type to MIME format
    file_type = v1_data.get("file_type", "")
    mime_type = _file_type_to_mime(file_type)

    logger.debug(
        "Migrating v1→v2: %s (hash=%s)",
        source_path,
        v1_data.get("content_hash", "")[:8],
    )

    return DocumentMetadata(
        ragd_schema_version=SCHEMA_V2,
        # Carry over existing fields with new names
        ragd_source_path=source_path,
        ragd_source_hash=v1_data.get("content_hash", ""),
        ragd_chunk_count=v1_data.get("chunk_count", 0),
        ragd_ingestion_date=indexed_at,
        # Derive what we can
        dc_title=title,
        dc_format=mime_type,
        dc_language="en",  # Default, can be detected later
        # Leave optional fields empty for user enrichment
        dc_creator=[],
        dc_subject=[],
        dc_description="",
        dc_date=None,
        dc_type="",
        dc_identifier="",
        ragd_quality_score=0.0,
        ragd_tags=[],
        ragd_project="",
    )


def migrate_to_current(data: dict[str, Any]) -> DocumentMetadata:
    """Migrate metadata from any version to current schema.

    Args:
        data: Raw metadata dictionary from storage

    Returns:
        DocumentMetadata instance with current schema

    Raises:
        ValueError: If schema version is unknown
    """
    version = get_schema_version(data)

    if version == CURRENT_SCHEMA:
        return DocumentMetadata.from_dict(data)

    if version == SCHEMA_V1:
        return migrate_v1_to_v2(data)

    raise ValueError(f"Unknown schema version: {version}")


def _file_type_to_mime(file_type: str) -> str:
    """Convert file type extension to MIME type.

    Args:
        file_type: File extension (e.g., "pdf", "txt")

    Returns:
        MIME type string
    """
    mime_map = {
        "pdf": "application/pdf",
        "txt": "text/plain",
        "md": "text/markdown",
        "html": "text/html",
        "htm": "text/html",
        "json": "application/json",
        "xml": "application/xml",
        "csv": "text/csv",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    return mime_map.get(file_type.lower().lstrip("."), f"application/{file_type}")
