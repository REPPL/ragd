"""Metadata storage and schema for ragd documents.

This module provides:
- DocumentMetadata: Dublin Core-based metadata with RAG extensions
- MetadataStore: SQLite-backed persistent storage
- MetadataExtractor: NLP-based metadata extraction
- Migration utilities for schema evolution
"""

from __future__ import annotations

from ragd.metadata.extractor import (
    ExtractedEntity,
    ExtractedKeyword,
    ExtractedMetadata,
    MetadataExtractor,
)
from ragd.metadata.migration import (
    CURRENT_SCHEMA,
    SCHEMA_V1,
    SCHEMA_V2,
    SCHEMA_V2_1,
    get_schema_version,
    migrate_to_current,
    migrate_v1_to_v2,
    migrate_v2_to_v2_1,
    needs_migration,
)
from ragd.metadata.schema import DocumentMetadata
from ragd.metadata.store import MetadataStore
from ragd.metadata.tags import TagManager

__all__ = [
    # Schema
    "DocumentMetadata",
    # Store
    "MetadataStore",
    # Tags
    "TagManager",
    # Extraction
    "MetadataExtractor",
    "ExtractedMetadata",
    "ExtractedKeyword",
    "ExtractedEntity",
    # Migration
    "CURRENT_SCHEMA",
    "SCHEMA_V1",
    "SCHEMA_V2",
    "SCHEMA_V2_1",
    "get_schema_version",
    "migrate_to_current",
    "migrate_v1_to_v2",
    "migrate_v2_to_v2_1",
    "needs_migration",
]
