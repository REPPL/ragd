"""Metadata proxy layer for backends without native metadata support.

This module provides SQLite-backed metadata storage for vector store backends
like FAISS that don't natively support metadata storage or filtering.
"""

from ragd.storage.metadata.sqlite_store import SQLiteMetadataStore

__all__ = ["SQLiteMetadataStore"]
