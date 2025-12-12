"""BM25 keyword search using SQLite FTS5.

Provides a keyword-based search index that complements semantic search.
Uses SQLite's built-in FTS5 extension for efficient BM25 ranking.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class BM25Result:
    """A single BM25 search result."""

    chunk_id: str
    document_id: str
    content: str
    bm25_score: float
    rank: int


class BM25Index:
    """SQLite FTS5-based BM25 keyword search index.

    Provides keyword-based search using BM25 ranking algorithm
    implemented via SQLite's FTS5 extension.
    """

    TABLE_NAME = "chunks_fts"

    def __init__(self, db_path: Path) -> None:
        """Initialise BM25 index.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        """Create FTS5 virtual table if not exists."""
        cursor = self._conn.cursor()

        # Create FTS5 table with porter stemmer tokenizer
        cursor.execute(
            f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS {self.TABLE_NAME} USING fts5(
                content,
                chunk_id UNINDEXED,
                document_id UNINDEXED,
                tokenize='porter unicode61'
            )
            """
        )

        # Create document tracking table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS indexed_documents (
                document_id TEXT PRIMARY KEY,
                indexed_at TEXT
            )
            """
        )

        self._conn.commit()

    def add_chunks(
        self,
        document_id: str,
        chunks: list[tuple[str, str]],
    ) -> None:
        """Add document chunks to the index.

        Args:
            document_id: Document identifier
            chunks: List of (chunk_id, content) tuples
        """
        if not chunks:
            return

        cursor = self._conn.cursor()

        # Delete existing chunks for this document (for re-indexing)
        cursor.execute(
            f"DELETE FROM {self.TABLE_NAME} WHERE document_id = ?",
            (document_id,),
        )

        # Insert new chunks
        cursor.executemany(
            f"INSERT INTO {self.TABLE_NAME} (content, chunk_id, document_id) VALUES (?, ?, ?)",
            [(content, chunk_id, document_id) for chunk_id, content in chunks],
        )

        # Track document
        cursor.execute(
            """
            INSERT OR REPLACE INTO indexed_documents (document_id, indexed_at)
            VALUES (?, datetime('now'))
            """,
            (document_id,),
        )

        self._conn.commit()

    def search(
        self,
        query: str,
        limit: int = 10,
        document_filter: str | None = None,
        document_ids: list[str] | None = None,
    ) -> list[BM25Result]:
        """Search using BM25 ranking.

        Args:
            query: Search query
            limit: Maximum results
            document_filter: Optional single document ID to filter by (deprecated)
            document_ids: Optional list of document IDs to filter by

        Returns:
            List of BM25Result ordered by relevance
        """
        if not query.strip():
            return []

        cursor = self._conn.cursor()

        # Escape special FTS5 characters
        escaped_query = self._escape_query(query)

        # Handle document filtering (document_ids takes precedence)
        if document_ids:
            # Multiple document IDs - use IN clause
            placeholders = ",".join("?" for _ in document_ids)
            cursor.execute(
                f"""
                SELECT
                    chunk_id,
                    document_id,
                    content,
                    bm25({self.TABLE_NAME}) as score
                FROM {self.TABLE_NAME}
                WHERE {self.TABLE_NAME} MATCH ?
                    AND document_id IN ({placeholders})
                ORDER BY score
                LIMIT ?
                """,
                (escaped_query, *document_ids, limit),
            )
        elif document_filter:
            cursor.execute(
                f"""
                SELECT
                    chunk_id,
                    document_id,
                    content,
                    bm25({self.TABLE_NAME}) as score
                FROM {self.TABLE_NAME}
                WHERE {self.TABLE_NAME} MATCH ?
                    AND document_id = ?
                ORDER BY score
                LIMIT ?
                """,
                (escaped_query, document_filter, limit),
            )
        else:
            cursor.execute(
                f"""
                SELECT
                    chunk_id,
                    document_id,
                    content,
                    bm25({self.TABLE_NAME}) as score
                FROM {self.TABLE_NAME}
                WHERE {self.TABLE_NAME} MATCH ?
                ORDER BY score
                LIMIT ?
                """,
                (escaped_query, limit),
            )

        results = []
        for rank, row in enumerate(cursor.fetchall()):
            # BM25 scores are negative in SQLite FTS5 (lower is better)
            # Convert to positive score (higher is better)
            bm25_score = -float(row["score"]) if row["score"] else 0.0

            results.append(
                BM25Result(
                    chunk_id=row["chunk_id"],
                    document_id=row["document_id"],
                    content=row["content"],
                    bm25_score=bm25_score,
                    rank=rank + 1,
                )
            )

        return results

    def _escape_query(self, query: str) -> str:
        """Parse and transform query for FTS5.

        Supports boolean operators (AND, OR, NOT), parentheses,
        quoted phrases, and prefix wildcards when detected.
        Falls back to simple escaping if parsing fails.

        Args:
            query: Raw query string

        Returns:
            FTS5-compatible query string
        """
        from ragd.search.query import QueryParseError, parse_query

        try:
            return parse_query(query)
        except QueryParseError:
            # Fallback to simple escaping on parse error
            return self._simple_escape(query)

    def _simple_escape(self, query: str) -> str:
        """Simple escaping fallback for FTS5 query.

        Provides safe escaping by quoting each word.
        This is the original ragd behaviour before boolean support.

        Args:
            query: Raw query string

        Returns:
            Safely escaped FTS5 query with quoted terms
        """
        words = query.split()
        escaped_words = []

        for word in words:
            # Remove FTS5 special characters
            clean = "".join(c for c in word if c.isalnum() or c in "-_")
            if clean:
                # Quote each term to prevent operator interpretation
                escaped_words.append(f'"{clean}"')

        return " ".join(escaped_words)

    def delete_document(self, document_id: str) -> bool:
        """Delete a document from the index.

        Args:
            document_id: Document to delete

        Returns:
            True if deleted, False if not found
        """
        cursor = self._conn.cursor()

        # Check if exists
        cursor.execute(
            "SELECT 1 FROM indexed_documents WHERE document_id = ?",
            (document_id,),
        )
        if not cursor.fetchone():
            return False

        # Delete chunks
        cursor.execute(
            f"DELETE FROM {self.TABLE_NAME} WHERE document_id = ?",
            (document_id,),
        )

        # Delete document record
        cursor.execute(
            "DELETE FROM indexed_documents WHERE document_id = ?",
            (document_id,),
        )

        self._conn.commit()
        return True

    def document_exists(self, document_id: str) -> bool:
        """Check if document is indexed.

        Args:
            document_id: Document identifier

        Returns:
            True if document exists in index
        """
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT 1 FROM indexed_documents WHERE document_id = ?",
            (document_id,),
        )
        return cursor.fetchone() is not None

    def get_stats(self) -> dict[str, int]:
        """Get index statistics.

        Returns:
            Dictionary with document and chunk counts
        """
        cursor = self._conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM indexed_documents")
        doc_count = cursor.fetchone()[0]

        cursor.execute(f"SELECT COUNT(*) FROM {self.TABLE_NAME}")
        chunk_count = cursor.fetchone()[0]

        return {
            "document_count": doc_count,
            "chunk_count": chunk_count,
        }

    def reset(self) -> None:
        """Reset the index. Warning: Deletes all data."""
        cursor = self._conn.cursor()
        cursor.execute(f"DELETE FROM {self.TABLE_NAME}")
        cursor.execute("DELETE FROM indexed_documents")
        self._conn.commit()

    def close(self) -> None:
        """Close database connection."""
        self._conn.close()

    def __enter__(self) -> "BM25Index":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()
