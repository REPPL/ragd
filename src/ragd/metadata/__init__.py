"""Metadata storage and schema for ragd documents.

This module provides:
- DocumentMetadata: Dublin Core-based metadata with RAG extensions
- MetadataStore: SQLite-backed persistent storage
- Migration utilities for schema evolution
"""

from __future__ import annotations

from ragd.metadata.migration import (
    CURRENT_SCHEMA,
    SCHEMA_V1,
    SCHEMA_V2,
    get_schema_version,
    migrate_to_current,
    migrate_v1_to_v2,
    needs_migration,
)
from ragd.metadata.schema import DocumentMetadata
from ragd.metadata.store import MetadataStore

__all__ = [
    # Schema
    "DocumentMetadata",
    # Store
    "MetadataStore",
    # Migration
    "CURRENT_SCHEMA",
    "SCHEMA_V1",
    "SCHEMA_V2",
    "get_schema_version",
    "migrate_to_current",
    "migrate_v1_to_v2",
    "needs_migration",
]
