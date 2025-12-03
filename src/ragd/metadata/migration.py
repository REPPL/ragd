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
SCHEMA_V2_1 = "2.1"
SCHEMA_V2_2 = "2.2"
CURRENT_SCHEMA = SCHEMA_V2_2


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


def migrate_v2_to_v2_1(
    v2_data: dict[str, Any],
    embedding_model: str = "",
    embedding_dimension: int = 0,
) -> DocumentMetadata:
    """Migrate v2.0 metadata to v2.1 schema.

    v2.1 adds:
    - ragd_sensitivity: str (default "public")
    - ragd_embedding_model: str (embedding model used)
    - ragd_embedding_dimension: int (embedding dimension)

    Args:
        v2_data: Dictionary with v2.0 schema fields
        embedding_model: Embedding model to back-populate (from config)
        embedding_dimension: Embedding dimension to back-populate

    Returns:
        DocumentMetadata instance with v2.1 schema
    """
    # Update version
    v2_data["ragd_schema_version"] = SCHEMA_V2_1

    # Add new fields with defaults
    v2_data.setdefault("ragd_sensitivity", "public")
    v2_data.setdefault("ragd_embedding_model", embedding_model)
    v2_data.setdefault("ragd_embedding_dimension", embedding_dimension)

    logger.debug(
        "Migrating v2.0→v2.1: %s (embedding=%s)",
        v2_data.get("ragd_source_path", "")[:50],
        embedding_model or "unknown",
    )

    return DocumentMetadata.from_dict(v2_data)


def migrate_v2_1_to_v2_2(v2_1_data: dict[str, Any]) -> DocumentMetadata:
    """Migrate v2.1 metadata to v2.2 schema.

    v2.2 adds:
    - ragd_data_tier: str (data sensitivity tier: public/personal/sensitive/critical)
    - ragd_tags: list[TagEntry] (provenance-tracked tags)

    Args:
        v2_1_data: Dictionary with v2.1 schema fields

    Returns:
        DocumentMetadata instance with v2.2 schema
    """
    # Update version
    v2_1_data["ragd_schema_version"] = SCHEMA_V2_2

    # Convert string tags to TagEntry format (with "legacy" source)
    tags = v2_1_data.get("ragd_tags", [])
    new_tags = []
    for tag in tags:
        if isinstance(tag, str):
            # Legacy string tag - convert to TagEntry dict
            new_tags.append({
                "name": tag,
                "source": "legacy",
                "confidence": None,
                "created_at": None,
                "created_by": None,
            })
        elif isinstance(tag, dict):
            # Already in new format or partial
            if "source" not in tag:
                tag["source"] = "legacy"
            new_tags.append(tag)
        else:
            # Unknown format, convert to string then TagEntry
            new_tags.append({
                "name": str(tag),
                "source": "legacy",
                "confidence": None,
                "created_at": None,
                "created_by": None,
            })

    v2_1_data["ragd_tags"] = new_tags

    # Map old sensitivity to new data tier
    sensitivity = v2_1_data.get("ragd_sensitivity", "public")
    tier_map = {
        "public": "public",
        "internal": "personal",
        "confidential": "sensitive",
    }
    v2_1_data.setdefault("ragd_data_tier", tier_map.get(sensitivity, "personal"))

    logger.debug(
        "Migrating v2.1→v2.2: %s (tags=%d, tier=%s)",
        v2_1_data.get("ragd_source_path", "")[:50],
        len(new_tags),
        v2_1_data.get("ragd_data_tier"),
    )

    return DocumentMetadata.from_dict(v2_1_data)


def migrate_to_current(
    data: dict[str, Any],
    embedding_model: str = "",
    embedding_dimension: int = 0,
) -> DocumentMetadata:
    """Migrate metadata from any version to current schema.

    Args:
        data: Raw metadata dictionary from storage
        embedding_model: Embedding model for back-population (v2.1 migration)
        embedding_dimension: Embedding dimension for back-population

    Returns:
        DocumentMetadata instance with current schema

    Raises:
        ValueError: If schema version is unknown
    """
    version = get_schema_version(data)

    if version == CURRENT_SCHEMA:
        return DocumentMetadata.from_dict(data)

    if version == SCHEMA_V1:
        # Chain migrations: v1 → v2 → v2.1 → v2.2
        v2_metadata = migrate_v1_to_v2(data)
        v2_1_metadata = migrate_v2_to_v2_1(
            v2_metadata.to_dict(),
            embedding_model=embedding_model,
            embedding_dimension=embedding_dimension,
        )
        return migrate_v2_1_to_v2_2(v2_1_metadata.to_dict())

    if version == SCHEMA_V2:
        # Chain migrations: v2 → v2.1 → v2.2
        v2_1_metadata = migrate_v2_to_v2_1(
            data,
            embedding_model=embedding_model,
            embedding_dimension=embedding_dimension,
        )
        return migrate_v2_1_to_v2_2(v2_1_metadata.to_dict())

    if version == SCHEMA_V2_1:
        return migrate_v2_1_to_v2_2(data)

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
