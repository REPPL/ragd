"""SQLCipher-encrypted storage for ragd.

This module provides encrypted SQLite storage using SQLCipher, which
implements AES-256 encryption in GCM mode at the page level.

SQLCipher Integration:
    - Transparent encryption of all database content
    - Password/key-based encryption with PBKDF2 or raw key
    - 5-15% performance overhead compared to unencrypted SQLite
    - Compatible with standard SQLite API

Usage:
    from ragd.security.encrypted_store import EncryptedConnection

    with EncryptedConnection(db_path, key) as conn:
        conn.execute("SELECT * FROM data")
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Base exception for encryption operations."""

    pass


class EncryptedConnectionError(EncryptionError):
    """Exception raised when encrypted connection fails."""

    pass


class DatabaseLockedError(EncryptionError):
    """Exception raised when database is locked (wrong key or not unlocked)."""

    pass


def _get_sqlcipher() -> Any:
    """Get SQLCipher module.

    Tries multiple SQLCipher packages in order of preference:
    1. pysqlcipher3 - Most commonly available
    2. sqlcipher3 - Alternative binding

    Returns:
        SQLCipher module.

    Raises:
        ImportError: If no SQLCipher package is available.
    """
    # Try pysqlcipher3 first (most common)
    try:
        import pysqlcipher3.dbapi2 as sqlcipher

        return sqlcipher
    except ImportError:
        pass

    # Try sqlcipher3
    try:
        import sqlcipher3

        return sqlcipher3
    except ImportError:
        pass

    raise ImportError(
        "SQLCipher is required for encryption but not available. "
        "Install system SQLCipher first:\n"
        "  macOS: brew install sqlcipher\n"
        "  Linux: apt-get install sqlcipher libsqlcipher-dev\n"
        "Then: pip install ragd[encryption]"
    )


def is_sqlcipher_available() -> bool:
    """Check if SQLCipher is available.

    Returns:
        True if a SQLCipher package can be imported.
    """
    try:
        _get_sqlcipher()
        return True
    except ImportError:
        return False


class EncryptedConnection:
    """Context manager for encrypted SQLite connections.

    Provides a connection to an encrypted SQLite database using SQLCipher.
    The key is passed as raw bytes and applied using the hex format.

    Usage:
        with EncryptedConnection(path, key) as conn:
            conn.execute("SELECT * FROM table")
    """

    def __init__(
        self,
        db_path: Path | str,
        key: bytes,
        *,
        kdf_iter: int = 256000,
        cipher: str = "aes-256-gcm",
    ) -> None:
        """Initialise encrypted connection.

        Args:
            db_path: Path to database file.
            key: Raw encryption key (typically 32 bytes for AES-256).
            kdf_iter: PBKDF2 iterations for key derivation (default 256000).
            cipher: Cipher algorithm (default aes-256-gcm).
        """
        self._db_path = Path(db_path)
        self._key = key
        self._kdf_iter = kdf_iter
        self._cipher = cipher
        self._conn: Any = None

    def __enter__(self) -> Any:
        """Open encrypted connection."""
        sqlcipher = _get_sqlcipher()

        # Create parent directory if needed
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            self._conn = sqlcipher.connect(str(self._db_path))

            # Apply encryption key using hex format
            # This provides the raw key directly rather than using password-based derivation
            key_hex = self._key.hex()
            self._conn.execute(f"PRAGMA key = \"x'{key_hex}'\"")

            # Configure SQLCipher settings
            self._conn.execute("PRAGMA cipher_page_size = 4096")
            self._conn.execute(f"PRAGMA kdf_iter = {self._kdf_iter}")
            self._conn.execute(f"PRAGMA cipher = '{self._cipher}'")

            # Verify the key works by accessing the database
            # This will fail if the key is wrong
            self._conn.execute("SELECT count(*) FROM sqlite_master")

            self._conn.row_factory = sqlcipher.Row

            return self._conn

        except Exception as e:
            if self._conn:
                self._conn.close()
                self._conn = None

            # Check for wrong key error
            error_msg = str(e).lower()
            if "file is not a database" in error_msg or "encrypted" in error_msg:
                raise DatabaseLockedError(
                    "Database is encrypted and the provided key is incorrect"
                ) from e

            raise EncryptedConnectionError(f"Failed to open encrypted database: {e}") from e

    def __exit__(self, *args: object) -> None:
        """Close connection."""
        if self._conn:
            self._conn.close()
            self._conn = None


@contextmanager
def encrypted_connection(
    db_path: Path | str,
    key: bytes,
    **kwargs: Any,
) -> Iterator[Any]:
    """Context manager for encrypted database connections.

    Convenience function wrapping EncryptedConnection.

    Args:
        db_path: Path to database file.
        key: Encryption key.
        **kwargs: Additional arguments for EncryptedConnection.

    Yields:
        SQLCipher connection.
    """
    with EncryptedConnection(db_path, key, **kwargs) as conn:
        yield conn


class EncryptedMetadataStore:
    """SQLCipher-encrypted metadata store.

    Drop-in replacement for SQLiteMetadataStore with encryption.
    Uses the same schema and API but encrypts all data at rest.
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

    def __init__(self, db_path: Path, key: bytes) -> None:
        """Initialise encrypted metadata store.

        Args:
            db_path: Path to database file.
            key: Encryption key (32 bytes for AES-256).
        """
        self._db_path = db_path
        self._key = key

        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialise schema
        with EncryptedConnection(db_path, key) as conn:
            conn.executescript(self.SCHEMA)
            conn.commit()

        logger.debug("EncryptedMetadataStore initialised: %s", db_path)

    @contextmanager
    def _connection(self) -> Iterator[Any]:
        """Get an encrypted database connection."""
        with EncryptedConnection(self._db_path, self._key) as conn:
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

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
            vector_id: Backend's internal vector ID.
            chunk_id: Unique chunk identifier.
            document_id: Parent document identifier.
            content: Text content.
            metadata: Additional metadata dictionary.
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
            items: List of (vector_id, chunk_id, document_id, content, metadata).
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
            chunk_id: Chunk identifier.

        Returns:
            Dictionary with metadata, or None if not found.
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
            vector_id: Backend's internal vector ID.

        Returns:
            Dictionary with metadata, or None if not found.
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

    def filter(self, where: dict[str, Any]) -> list[int]:
        """Find vector IDs matching filter criteria.

        Args:
            where: Filter conditions.

        Returns:
            List of matching vector IDs.
        """
        if not where:
            with self._connection() as conn:
                rows = conn.execute(
                    "SELECT vector_id FROM vector_metadata"
                ).fetchall()
                return [row["vector_id"] for row in rows]

        sql_parts, params = self._translate_filter(where)

        with self._connection() as conn:
            rows = conn.execute(
                f"SELECT vector_id FROM vector_metadata WHERE {sql_parts}",
                params,
            ).fetchall()

            return [row["vector_id"] for row in rows]

    def _translate_filter(self, where: dict[str, Any]) -> tuple[str, list[Any]]:
        """Translate ChromaDB-style filter to SQL."""
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
                for op, op_value in value.items():
                    sql_cond, sql_params = self._translate_operator(key, op, op_value)
                    conditions.append(sql_cond)
                    params.extend(sql_params)

            else:
                conditions.append(self._get_column_expr(key) + " = ?")
                params.append(self._serialize_value(value))

        return " AND ".join(conditions) if conditions else "1=1", params

    def _translate_operator(
        self, key: str, op: str, value: Any
    ) -> tuple[str, list[Any]]:
        """Translate a single operator expression."""
        col_expr = self._get_column_expr(key)

        operators = {
            "$eq": "=",
            "$ne": "!=",
            "$gt": ">",
            "$gte": ">=",
            "$lt": "<",
            "$lte": "<=",
        }

        if op in operators:
            return f"{col_expr} {operators[op]} ?", [self._serialize_value(value)]
        elif op == "$in":
            if not value:
                return "0=1", []
            placeholders = ",".join("?" * len(value))
            return f"{col_expr} IN ({placeholders})", [
                self._serialize_value(v) for v in value
            ]
        elif op == "$nin":
            if not value:
                return "1=1", []
            placeholders = ",".join("?" * len(value))
            return f"{col_expr} NOT IN ({placeholders})", [
                self._serialize_value(v) for v in value
            ]
        else:
            raise ValueError(f"Unknown operator: {op}")

    def _get_column_expr(self, key: str) -> str:
        """Get SQL column expression for a key."""
        standard_columns = {"chunk_id", "document_id", "content", "vector_id"}
        if key in standard_columns:
            return key
        return f"json_extract(metadata, '$.{key}')"

    def _serialize_value(self, value: Any) -> Any:
        """Serialize a value for SQL."""
        if isinstance(value, bool):
            return 1 if value else 0
        return value

    def delete(self, chunk_ids: list[str]) -> int:
        """Delete metadata by chunk IDs.

        Args:
            chunk_ids: List of chunk identifiers.

        Returns:
            Number of records deleted.
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
            document_id: Document identifier.

        Returns:
            Number of records deleted.
        """
        with self._connection() as conn:
            cursor = conn.execute(
                "DELETE FROM vector_metadata WHERE document_id = ?",
                (document_id,),
            )
            return cursor.rowcount

    def count(self) -> int:
        """Return total number of metadata records."""
        with self._connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM vector_metadata").fetchone()
            return row[0]

    def close(self) -> None:
        """Close the store.

        Note: Each operation uses its own connection, so this is a no-op.
        """
        pass


def is_database_encrypted(db_path: Path) -> bool:
    """Check if a database file is encrypted.

    Attempts to open the database with standard SQLite. If it fails
    with a "not a database" error, the file is likely encrypted.

    Args:
        db_path: Path to database file.

    Returns:
        True if the database appears to be encrypted.
    """
    if not db_path.exists():
        return False

    import sqlite3

    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute("SELECT count(*) FROM sqlite_master")
        conn.close()
        return False
    except sqlite3.DatabaseError as e:
        if "file is not a database" in str(e).lower():
            return True
        raise


def migrate_to_encrypted(
    source_path: Path,
    dest_path: Path,
    key: bytes,
    *,
    delete_source: bool = False,
) -> None:
    """Migrate an unencrypted database to encrypted.

    Args:
        source_path: Path to unencrypted source database.
        dest_path: Path for encrypted destination database.
        key: Encryption key for destination.
        delete_source: Whether to delete source after migration.

    Raises:
        FileNotFoundError: If source doesn't exist.
        FileExistsError: If destination already exists.
    """
    import sqlite3

    if not source_path.exists():
        raise FileNotFoundError(f"Source database not found: {source_path}")

    if dest_path.exists():
        raise FileExistsError(f"Destination already exists: {dest_path}")

    # Open source (unencrypted)
    source_conn = sqlite3.connect(str(source_path))
    source_conn.row_factory = sqlite3.Row

    try:
        # Create encrypted destination
        with EncryptedConnection(dest_path, key) as dest_conn:
            # Get all tables from source
            tables = source_conn.execute(
                "SELECT name, sql FROM sqlite_master WHERE type='table'"
            ).fetchall()

            for table in tables:
                table_name = table["name"]
                create_sql = table["sql"]

                if table_name.startswith("sqlite_"):
                    continue

                # Create table in destination
                dest_conn.execute(create_sql)

                # Copy data
                rows = source_conn.execute(f"SELECT * FROM {table_name}").fetchall()
                if rows:
                    columns = rows[0].keys()
                    placeholders = ",".join("?" * len(columns))
                    dest_conn.executemany(
                        f"INSERT INTO {table_name} VALUES ({placeholders})",
                        [tuple(row) for row in rows],
                    )

            # Copy indices
            indices = source_conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"
            ).fetchall()

            for index in indices:
                dest_conn.execute(index["sql"])

            dest_conn.commit()

    finally:
        source_conn.close()

    if delete_source:
        source_path.unlink()

    logger.info("Migrated database to encrypted: %s -> %s", source_path, dest_path)
