"""SQLite-based metadata storage for document metadata.

This module provides persistent storage for DocumentMetadata using SQLite,
supporting CRUD operations, querying, and lazy schema migration.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from ragd.metadata.migration import migrate_to_current, needs_migration
from ragd.metadata.schema import DocumentMetadata

logger = logging.getLogger(__name__)


class MetadataStore:
    """SQLite-based storage for document metadata.

    Stores DocumentMetadata in a SQLite database with JSON storage for
    flexibility and forward compatibility. Supports lazy migration from
    older schema versions.

    Example:
        >>> store = MetadataStore(Path("~/.ragd/metadata.sqlite"))
        >>> store.set("doc-123", DocumentMetadata(dc_title="My Document"))
        >>> metadata = store.get("doc-123")
        >>> print(metadata.dc_title)
        My Document
    """

    def __init__(self, db_path: Path) -> None:
        """Initialise the metadata store.

        Args:
            db_path: Path to SQLite database file. Created if doesn't exist.
        """
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        """Context manager for database connections."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        """Initialise database schema."""
        with self._connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    metadata JSON NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_project
                    ON documents(json_extract(metadata, '$.ragd_project'));

                CREATE INDEX IF NOT EXISTS idx_ingestion_date
                    ON documents(json_extract(metadata, '$.ragd_ingestion_date'));

                CREATE INDEX IF NOT EXISTS idx_source_path
                    ON documents(json_extract(metadata, '$.ragd_source_path'));

                CREATE INDEX IF NOT EXISTS idx_source_hash
                    ON documents(json_extract(metadata, '$.ragd_source_hash'));
            """)
            conn.commit()

    def get(self, doc_id: str) -> DocumentMetadata | None:
        """Get metadata for a document.

        Performs lazy migration if the document has an older schema version.

        Args:
            doc_id: Document identifier

        Returns:
            DocumentMetadata or None if not found
        """
        with self._connection() as conn:
            row = conn.execute(
                "SELECT metadata FROM documents WHERE id = ?",
                (doc_id,),
            ).fetchone()

            if row is None:
                return None

            raw_data = json.loads(row["metadata"])

            # Lazy migration
            if needs_migration(raw_data):
                self._logger.debug("Migrating metadata for %s", doc_id)
                metadata = migrate_to_current(raw_data)
                self._update_raw(conn, doc_id, metadata.to_dict())
                conn.commit()
                return metadata

            return DocumentMetadata.from_dict(raw_data)

    def get_raw(self, doc_id: str) -> dict[str, Any] | None:
        """Get raw metadata dictionary without migration.

        Useful for inspection or debugging.

        Args:
            doc_id: Document identifier

        Returns:
            Raw metadata dict or None if not found
        """
        with self._connection() as conn:
            row = conn.execute(
                "SELECT metadata FROM documents WHERE id = ?",
                (doc_id,),
            ).fetchone()

            if row is None:
                return None

            return json.loads(row["metadata"])

    def set(self, doc_id: str, metadata: DocumentMetadata) -> None:
        """Set metadata for a document.

        Creates new record or updates existing.

        Args:
            doc_id: Document identifier
            metadata: DocumentMetadata to store
        """
        now = datetime.now().isoformat()
        data = metadata.to_dict()

        with self._connection() as conn:
            existing = conn.execute(
                "SELECT id FROM documents WHERE id = ?",
                (doc_id,),
            ).fetchone()

            if existing:
                conn.execute(
                    """
                    UPDATE documents
                    SET metadata = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (json.dumps(data), now, doc_id),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO documents (id, metadata, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (doc_id, json.dumps(data), now, now),
                )
            conn.commit()

    def update(self, doc_id: str, **fields: Any) -> bool:
        """Update specific fields of document metadata.

        Retrieves existing metadata, updates specified fields, and saves.

        Args:
            doc_id: Document identifier
            **fields: Field names and values to update

        Returns:
            True if document was found and updated, False otherwise
        """
        existing = self.get(doc_id)
        if existing is None:
            return False

        # Update fields
        data = existing.to_dict()
        for key, value in fields.items():
            if hasattr(existing, key):
                data[key] = value
            else:
                self._logger.warning("Unknown field %s, ignoring", key)

        updated = DocumentMetadata.from_dict(data)
        self.set(doc_id, updated)
        return True

    def delete(self, doc_id: str) -> bool:
        """Delete metadata for a document.

        Args:
            doc_id: Document identifier

        Returns:
            True if document was deleted, False if not found
        """
        with self._connection() as conn:
            cursor = conn.execute(
                "DELETE FROM documents WHERE id = ?",
                (doc_id,),
            )
            conn.commit()
            return cursor.rowcount > 0

    def exists(self, doc_id: str) -> bool:
        """Check if metadata exists for a document.

        Args:
            doc_id: Document identifier

        Returns:
            True if metadata exists
        """
        with self._connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM documents WHERE id = ?",
                (doc_id,),
            ).fetchone()
            return row is not None

    def list_ids(self) -> list[str]:
        """List all document IDs in the store.

        Returns:
            List of document IDs
        """
        with self._connection() as conn:
            rows = conn.execute("SELECT id FROM documents").fetchall()
            return [row["id"] for row in rows]

    def count(self) -> int:
        """Count total documents in the store.

        Returns:
            Number of documents
        """
        with self._connection() as conn:
            row = conn.execute("SELECT COUNT(*) as cnt FROM documents").fetchone()
            return row["cnt"] if row else 0

    def query(
        self,
        *,
        project: str | None = None,
        tags: list[str] | None = None,
        source_path_contains: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
    ) -> list[tuple[str, DocumentMetadata]]:
        """Query documents by metadata fields.

        Args:
            project: Filter by ragd_project
            tags: Filter by ragd_tags (documents must have ALL specified tags)
            source_path_contains: Filter by substring in source path
            since: Filter by ingestion date >= since
            until: Filter by ingestion date <= until
            limit: Maximum number of results

        Returns:
            List of (doc_id, DocumentMetadata) tuples
        """
        conditions: list[str] = []
        params: list[Any] = []

        if project is not None:
            conditions.append("json_extract(metadata, '$.ragd_project') = ?")
            params.append(project)

        if tags:
            # Each tag must be present in the tags array
            for tag in tags:
                conditions.append(
                    "json_extract(metadata, '$.ragd_tags') LIKE ?"
                )
                params.append(f'%"{tag}"%')

        if source_path_contains:
            conditions.append(
                "json_extract(metadata, '$.ragd_source_path') LIKE ?"
            )
            params.append(f"%{source_path_contains}%")

        if since:
            conditions.append(
                "json_extract(metadata, '$.ragd_ingestion_date') >= ?"
            )
            params.append(since.isoformat())

        if until:
            conditions.append(
                "json_extract(metadata, '$.ragd_ingestion_date') <= ?"
            )
            params.append(until.isoformat())

        query = "SELECT id, metadata FROM documents"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY json_extract(metadata, '$.ragd_ingestion_date') DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        results: list[tuple[str, DocumentMetadata]] = []
        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
            for row in rows:
                raw_data = json.loads(row["metadata"])

                # Lazy migration during query
                if needs_migration(raw_data):
                    metadata = migrate_to_current(raw_data)
                    self._update_raw(conn, row["id"], metadata.to_dict())
                else:
                    metadata = DocumentMetadata.from_dict(raw_data)

                results.append((row["id"], metadata))

            conn.commit()

        return results

    def _update_raw(
        self,
        conn: sqlite3.Connection,
        doc_id: str,
        data: dict[str, Any],
    ) -> None:
        """Update raw metadata without creating new connection.

        Internal method for use within transaction.
        """
        now = datetime.now().isoformat()
        conn.execute(
            """
            UPDATE documents
            SET metadata = ?, updated_at = ?
            WHERE id = ?
            """,
            (json.dumps(data), now, doc_id),
        )

    def get_migration_stats(self) -> dict[str, int]:
        """Get statistics about schema versions in the store.

        Returns:
            Dictionary with version counts
        """
        stats: dict[str, int] = {}
        with self._connection() as conn:
            rows = conn.execute("SELECT metadata FROM documents").fetchall()
            for row in rows:
                raw_data = json.loads(row["metadata"])
                version = raw_data.get("ragd_schema_version", "1.0")
                stats[version] = stats.get(version, 0) + 1
        return stats

    def migrate_all(self, *, batch_size: int = 100) -> int:
        """Migrate all documents to current schema.

        Performs batch migration of all documents that need migration.
        Useful for upfront migration instead of lazy migration.

        Args:
            batch_size: Number of documents to migrate per batch

        Returns:
            Number of documents migrated
        """
        migrated = 0
        with self._connection() as conn:
            offset = 0
            while True:
                rows = conn.execute(
                    "SELECT id, metadata FROM documents LIMIT ? OFFSET ?",
                    (batch_size, offset),
                ).fetchall()

                if not rows:
                    break

                for row in rows:
                    raw_data = json.loads(row["metadata"])
                    if needs_migration(raw_data):
                        metadata = migrate_to_current(raw_data)
                        self._update_raw(conn, row["id"], metadata.to_dict())
                        migrated += 1

                conn.commit()
                offset += batch_size

                if migrated > 0 and migrated % 500 == 0:
                    self._logger.info("Migrated %d documents...", migrated)

        if migrated > 0:
            self._logger.info("Migration complete: %d documents migrated", migrated)

        return migrated
