"""SQLite-backed metadata store for FAISS and other backends.

This module provides metadata storage and filtering capabilities for
vector store backends that don't support native metadata operations.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SQLiteMetadataStore:
    """SQLite-backed metadata store.

    Provides metadata storage and ChromaDB-style filter translation for
    backends like FAISS that don't have native metadata support.

    The store maintains a mapping between:
    - vector_id: The backend's internal ID (e.g., FAISS index position)
    - chunk_id: The application-level unique chunk identifier
    - document_id: The parent document identifier

    Filter Translation:
    ChromaDB-style filters are translated to SQL queries:
    - {"key": "value"} → key = 'value'
    - {"$and": [...]} → ... AND ...
    - {"$or": [...]} → ... OR ...
    - {"key": {"$eq": v}} → key = v
    - {"key": {"$ne": v}} → key != v
    - {"key": {"$gt": v}} → key > v
    - {"key": {"$gte": v}} → key >= v
    - {"key": {"$lt": v}} → key < v
    - {"key": {"$lte": v}} → key <= v
    - {"key": {"$in": [...]}} → key IN (...)
    - {"key": {"$nin": [...]}} → key NOT IN (...)
    """

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS vector_metadata (
        vector_id INTEGER PRIMARY KEY,
        chunk_id TEXT UNIQUE NOT NULL,
        document_id TEXT NOT NULL,
        content TEXT NOT NULL,
        metadata JSON,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_chunk_id ON vector_metadata(chunk_id);
    CREATE INDEX IF NOT EXISTS idx_document_id ON vector_metadata(document_id);
    """

    def __init__(self, db_path: Path) -> None:
        """Initialise SQLite metadata store.

        Args:
            db_path: Path to SQLite database file
        """
        self._db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialise database
        with self._connection() as conn:
            conn.executescript(self.SCHEMA)

        logger.debug("SQLiteMetadataStore initialised: %s", db_path)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        """Get a database connection with proper cleanup."""
        conn = sqlite3.connect(
            str(self._db_path),
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def add(
        self,
        vector_id: int,
        chunk_id: str,
        document_id: str,
        content: str,
        metadata: dict[str, Any],
    ) -> None:
        """Add metadata for a vector.

        Args:
            vector_id: Backend's internal vector ID
            chunk_id: Unique chunk identifier
            document_id: Parent document identifier
            content: Text content
            metadata: Additional metadata dictionary
        """
        with self._connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO vector_metadata
                (vector_id, chunk_id, document_id, content, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (vector_id, chunk_id, document_id, content, json.dumps(metadata)),
            )

    def add_batch(
        self,
        items: list[tuple[int, str, str, str, dict[str, Any]]],
    ) -> None:
        """Add multiple metadata entries efficiently.

        Args:
            items: List of (vector_id, chunk_id, document_id, content, metadata)
        """
        with self._connection() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO vector_metadata
                (vector_id, chunk_id, document_id, content, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (vid, cid, did, content, json.dumps(meta))
                    for vid, cid, did, content, meta in items
                ],
            )

    def get(self, chunk_id: str) -> dict[str, Any] | None:
        """Get metadata by chunk ID.

        Args:
            chunk_id: Chunk identifier

        Returns:
            Dictionary with vector_id, document_id, content, metadata
            or None if not found
        """
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT vector_id, document_id, content, metadata
                FROM vector_metadata
                WHERE chunk_id = ?
                """,
                (chunk_id,),
            ).fetchone()

            if row is None:
                return None

            return {
                "vector_id": row["vector_id"],
                "chunk_id": chunk_id,
                "document_id": row["document_id"],
                "content": row["content"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            }

    def get_by_vector_id(self, vector_id: int) -> dict[str, Any] | None:
        """Get metadata by backend vector ID.

        Args:
            vector_id: Backend's internal vector ID

        Returns:
            Dictionary with chunk_id, document_id, content, metadata
            or None if not found
        """
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT chunk_id, document_id, content, metadata
                FROM vector_metadata
                WHERE vector_id = ?
                """,
                (vector_id,),
            ).fetchone()

            if row is None:
                return None

            return {
                "vector_id": vector_id,
                "chunk_id": row["chunk_id"],
                "document_id": row["document_id"],
                "content": row["content"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            }

    def get_batch(self, vector_ids: list[int]) -> list[dict[str, Any] | None]:
        """Get metadata for multiple vector IDs efficiently.

        Args:
            vector_ids: List of vector IDs

        Returns:
            List of metadata dicts (None for missing IDs)
        """
        if not vector_ids:
            return []

        with self._connection() as conn:
            placeholders = ",".join("?" * len(vector_ids))
            rows = conn.execute(
                f"""
                SELECT vector_id, chunk_id, document_id, content, metadata
                FROM vector_metadata
                WHERE vector_id IN ({placeholders})
                """,
                vector_ids,
            ).fetchall()

            # Build lookup
            result_map: dict[int, dict[str, Any]] = {}
            for row in rows:
                result_map[row["vector_id"]] = {
                    "vector_id": row["vector_id"],
                    "chunk_id": row["chunk_id"],
                    "document_id": row["document_id"],
                    "content": row["content"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                }

            # Return in order
            return [result_map.get(vid) for vid in vector_ids]

    def filter(self, where: dict[str, Any]) -> list[int]:
        """Find vector IDs matching filter criteria.

        Translates ChromaDB-style where filters to SQL.

        Args:
            where: Filter conditions

        Returns:
            List of matching vector IDs
        """
        if not where:
            # No filter - return all
            with self._connection() as conn:
                rows = conn.execute(
                    "SELECT vector_id FROM vector_metadata"
                ).fetchall()
                return [row["vector_id"] for row in rows]

        # Build SQL filter
        sql_parts, params = self._translate_filter(where)

        with self._connection() as conn:
            rows = conn.execute(
                f"SELECT vector_id FROM vector_metadata WHERE {sql_parts}",
                params,
            ).fetchall()

            return [row["vector_id"] for row in rows]

    def _translate_filter(self, where: dict[str, Any]) -> tuple[str, list[Any]]:
        """Translate ChromaDB-style filter to SQL.

        Args:
            where: Filter dictionary

        Returns:
            Tuple of (SQL WHERE clause, parameters)
        """
        conditions = []
        params: list[Any] = []

        for key, value in where.items():
            if key == "$and":
                sub_conditions = []
                for sub_filter in value:
                    sub_sql, sub_params = self._translate_filter(sub_filter)
                    sub_conditions.append(f"({sub_sql})")
                    params.extend(sub_params)
                conditions.append(" AND ".join(sub_conditions))

            elif key == "$or":
                sub_conditions = []
                for sub_filter in value:
                    sub_sql, sub_params = self._translate_filter(sub_filter)
                    sub_conditions.append(f"({sub_sql})")
                    params.extend(sub_params)
                conditions.append(f"({' OR '.join(sub_conditions)})")

            elif isinstance(value, dict):
                # Operator-based filter
                for op, op_value in value.items():
                    sql_cond, sql_params = self._translate_operator(key, op, op_value)
                    conditions.append(sql_cond)
                    params.extend(sql_params)

            else:
                # Simple equality
                conditions.append(self._get_column_expr(key) + " = ?")
                params.append(self._serialize_value(value))

        return " AND ".join(conditions) if conditions else "1=1", params

    def _translate_operator(
        self, key: str, op: str, value: Any
    ) -> tuple[str, list[Any]]:
        """Translate a single operator expression.

        Args:
            key: Field name
            op: Operator (e.g., "$eq", "$gt")
            value: Comparison value

        Returns:
            Tuple of (SQL condition, parameters)
        """
        col_expr = self._get_column_expr(key)

        if op == "$eq":
            return f"{col_expr} = ?", [self._serialize_value(value)]
        elif op == "$ne":
            return f"{col_expr} != ?", [self._serialize_value(value)]
        elif op == "$gt":
            return f"{col_expr} > ?", [self._serialize_value(value)]
        elif op == "$gte":
            return f"{col_expr} >= ?", [self._serialize_value(value)]
        elif op == "$lt":
            return f"{col_expr} < ?", [self._serialize_value(value)]
        elif op == "$lte":
            return f"{col_expr} <= ?", [self._serialize_value(value)]
        elif op == "$in":
            if not value:
                return "0=1", []  # Empty IN clause
            placeholders = ",".join("?" * len(value))
            return f"{col_expr} IN ({placeholders})", [
                self._serialize_value(v) for v in value
            ]
        elif op == "$nin":
            if not value:
                return "1=1", []  # Empty NOT IN clause
            placeholders = ",".join("?" * len(value))
            return f"{col_expr} NOT IN ({placeholders})", [
                self._serialize_value(v) for v in value
            ]
        else:
            raise ValueError(f"Unknown operator: {op}")

    def _get_column_expr(self, key: str) -> str:
        """Get SQL column expression for a key.

        Standard columns are accessed directly, metadata fields via JSON extract.

        Args:
            key: Field name

        Returns:
            SQL column expression
        """
        standard_columns = {"chunk_id", "document_id", "content", "vector_id"}

        if key in standard_columns:
            return key
        else:
            # JSON extract for metadata fields
            return f"json_extract(metadata, '$.{key}')"

    def _serialize_value(self, value: Any) -> Any:
        """Serialize a value for SQL.

        Args:
            value: Value to serialize

        Returns:
            Serialized value
        """
        if isinstance(value, bool):
            return 1 if value else 0
        return value

    def delete(self, chunk_ids: list[str]) -> int:
        """Delete metadata by chunk IDs.

        Args:
            chunk_ids: List of chunk identifiers

        Returns:
            Number of records deleted
        """
        if not chunk_ids:
            return 0

        with self._connection() as conn:
            placeholders = ",".join("?" * len(chunk_ids))
            cursor = conn.execute(
                f"DELETE FROM vector_metadata WHERE chunk_id IN ({placeholders})",
                chunk_ids,
            )
            return cursor.rowcount

    def delete_by_document(self, document_id: str) -> int:
        """Delete all metadata for a document.

        Args:
            document_id: Document identifier

        Returns:
            Number of records deleted
        """
        with self._connection() as conn:
            cursor = conn.execute(
                "DELETE FROM vector_metadata WHERE document_id = ?",
                (document_id,),
            )
            return cursor.rowcount

    def delete_by_vector_ids(self, vector_ids: list[int]) -> int:
        """Delete metadata by vector IDs.

        Args:
            vector_ids: List of vector IDs

        Returns:
            Number of records deleted
        """
        if not vector_ids:
            return 0

        with self._connection() as conn:
            placeholders = ",".join("?" * len(vector_ids))
            cursor = conn.execute(
                f"DELETE FROM vector_metadata WHERE vector_id IN ({placeholders})",
                vector_ids,
            )
            return cursor.rowcount

    def count(self) -> int:
        """Return total number of metadata records."""
        with self._connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM vector_metadata").fetchone()
            return row[0]

    def get_all_document_ids(self) -> list[str]:
        """Get all unique document IDs.

        Returns:
            List of document IDs
        """
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT DISTINCT document_id FROM vector_metadata"
            ).fetchall()
            return [row["document_id"] for row in rows]

    def get_vector_ids_for_document(self, document_id: str) -> list[int]:
        """Get all vector IDs for a document.

        Args:
            document_id: Document identifier

        Returns:
            List of vector IDs
        """
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT vector_id FROM vector_metadata WHERE document_id = ?",
                (document_id,),
            ).fetchall()
            return [row["vector_id"] for row in rows]

    def close(self) -> None:
        """Close database connections.

        Note: This is a no-op since we use connection-per-operation pattern.
        """
        pass
