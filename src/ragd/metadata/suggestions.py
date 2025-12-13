"""Auto-tag suggestions from metadata extraction.

F-061: Auto-Tag Suggestions
- TagSuggestion dataclass with source, confidence, status
- SuggestionEngine for managing pending suggestions
- CLI workflow for reviewing and confirming suggestions
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from ragd.metadata.tags import TagManager

logger = logging.getLogger(__name__)

SuggestionSource = Literal["keybert", "llm", "ner", "imported"]
SuggestionStatus = Literal["pending", "confirmed", "rejected"]


@dataclass
class TagSuggestion:
    """A suggested tag pending user review.

    Suggestions are generated during indexing from:
    - KeyBERT keyword extraction
    - LLM classification
    - Named Entity Recognition (NER)
    - Imported metadata
    """

    tag_name: str
    source: SuggestionSource
    confidence: float
    doc_id: str
    status: SuggestionStatus = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    source_text: str = ""
    source_model: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialise to dictionary for storage."""
        return {
            "tag_name": self.tag_name,
            "source": self.source,
            "confidence": self.confidence,
            "doc_id": self.doc_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "source_text": self.source_text,
            "source_model": self.source_model,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TagSuggestion:
        """Create TagSuggestion from dictionary."""
        return cls(
            tag_name=data["tag_name"],
            source=data["source"],
            confidence=data["confidence"],
            doc_id=data["doc_id"],
            status=data.get("status", "pending"),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now(),
            source_text=data.get("source_text", ""),
            source_model=data.get("source_model", ""),
        )

    @classmethod
    def from_keybert(
        cls,
        doc_id: str,
        keyword: str,
        score: float,
        *,
        source_text: str = "",
        model: str = "all-MiniLM-L6-v2",
    ) -> TagSuggestion:
        """Create suggestion from KeyBERT extraction."""
        return cls(
            tag_name=keyword.lower().replace(" ", "-"),
            source="keybert",
            confidence=score,
            doc_id=doc_id,
            source_text=source_text,
            source_model=model,
        )

    @classmethod
    def from_llm(
        cls,
        doc_id: str,
        category: str,
        confidence: float,
        *,
        source_text: str = "",
        model: str = "",
    ) -> TagSuggestion:
        """Create suggestion from LLM classification."""
        return cls(
            tag_name=category.lower().replace(" ", "-"),
            source="llm",
            confidence=confidence,
            doc_id=doc_id,
            source_text=source_text,
            source_model=model,
        )

    @classmethod
    def from_ner(
        cls,
        doc_id: str,
        entity: str,
        entity_type: str,
        confidence: float,
        *,
        source_text: str = "",
        model: str = "en_core_web_sm",
    ) -> TagSuggestion:
        """Create suggestion from Named Entity Recognition."""
        # Prefix with entity type for namespace
        tag_name = f"{entity_type.lower()}/{entity.lower().replace(' ', '-')}"
        return cls(
            tag_name=tag_name,
            source="ner",
            confidence=confidence,
            doc_id=doc_id,
            source_text=source_text,
            source_model=model,
        )


@dataclass
class SuggestionConfig:
    """Configuration for tag suggestions."""

    enabled: bool = True
    min_confidence: float = 0.7
    max_suggestions_per_doc: int = 10
    keybert_enabled: bool = True
    llm_enabled: bool = True
    ner_enabled: bool = True


class SuggestionEngine:
    """Manages tag suggestions in SQLite storage.

    Provides operations for creating, reviewing, and confirming suggestions.
    """

    def __init__(self, db_path: Path, tag_manager: TagManager) -> None:
        """Initialise the suggestion engine.

        Args:
            db_path: Path to SQLite database file
            tag_manager: TagManager instance for confirming tags
        """
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._tag_manager = tag_manager
        self._config = SuggestionConfig()
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
        """Initialise database schema for suggestions."""
        with self._connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS tag_suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id TEXT NOT NULL,
                    tag_name TEXT NOT NULL,
                    source TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    source_text TEXT,
                    source_model TEXT,
                    created_at TEXT NOT NULL,
                    reviewed_at TEXT,
                    UNIQUE(doc_id, tag_name, source)
                );

                CREATE INDEX IF NOT EXISTS idx_suggestions_doc
                    ON tag_suggestions(doc_id);

                CREATE INDEX IF NOT EXISTS idx_suggestions_status
                    ON tag_suggestions(status);

                CREATE INDEX IF NOT EXISTS idx_suggestions_source
                    ON tag_suggestions(source);
            """)
            conn.commit()

    def configure(self, config: SuggestionConfig) -> None:
        """Update configuration.

        Args:
            config: New configuration settings
        """
        self._config = config

    def add(self, suggestion: TagSuggestion) -> bool:
        """Add a tag suggestion.

        Skips if suggestion already exists for doc/tag/source combination.
        Skips if confidence below threshold.

        Args:
            suggestion: TagSuggestion to add

        Returns:
            True if added, False if skipped
        """
        if suggestion.confidence < self._config.min_confidence:
            return False

        with self._connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO tag_suggestions
                    (doc_id, tag_name, source, confidence, status, source_text,
                     source_model, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        suggestion.doc_id,
                        suggestion.tag_name,
                        suggestion.source,
                        suggestion.confidence,
                        suggestion.status,
                        suggestion.source_text,
                        suggestion.source_model,
                        suggestion.created_at.isoformat(),
                    ),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # Already exists
                return False

    def add_batch(self, suggestions: list[TagSuggestion]) -> int:
        """Add multiple suggestions.

        Args:
            suggestions: List of suggestions to add

        Returns:
            Number of suggestions added
        """
        added = 0
        for suggestion in suggestions:
            if self.add(suggestion):
                added += 1
        return added

    def get_for_doc(
        self,
        doc_id: str,
        *,
        status: SuggestionStatus | None = None,
        min_confidence: float | None = None,
    ) -> list[TagSuggestion]:
        """Get suggestions for a document.

        Args:
            doc_id: Document identifier
            status: Filter by status (None for all)
            min_confidence: Filter by minimum confidence

        Returns:
            List of suggestions, sorted by confidence descending
        """
        query = "SELECT * FROM tag_suggestions WHERE doc_id = ?"
        params: list[Any] = [doc_id]

        if status:
            query += " AND status = ?"
            params.append(status)

        if min_confidence is not None:
            query += " AND confidence >= ?"
            params.append(min_confidence)

        query += " ORDER BY confidence DESC"

        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_suggestion(row) for row in rows]

    def get_pending(self, limit: int | None = None) -> list[TagSuggestion]:
        """Get all pending suggestions.

        Args:
            limit: Maximum number to return

        Returns:
            List of pending suggestions
        """
        query = "SELECT * FROM tag_suggestions WHERE status = 'pending'"
        query += " ORDER BY confidence DESC"

        if limit:
            query += f" LIMIT {limit}"

        with self._connection() as conn:
            rows = conn.execute(query).fetchall()
            return [self._row_to_suggestion(row) for row in rows]

    def get_pending_docs(self) -> list[str]:
        """Get document IDs with pending suggestions.

        Returns:
            List of document IDs with pending suggestions
        """
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT DISTINCT doc_id FROM tag_suggestions WHERE status = 'pending'"
            ).fetchall()
            return [row["doc_id"] for row in rows]

    def _row_to_suggestion(self, row: sqlite3.Row) -> TagSuggestion:
        """Convert database row to TagSuggestion."""
        return TagSuggestion(
            tag_name=row["tag_name"],
            source=row["source"],
            confidence=row["confidence"],
            doc_id=row["doc_id"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            source_text=row["source_text"] or "",
            source_model=row["source_model"] or "",
        )

    def confirm(
        self,
        doc_id: str,
        tag_names: list[str] | None = None,
        *,
        min_confidence: float | None = None,
    ) -> int:
        """Confirm suggestions and apply them as tags.

        Args:
            doc_id: Document identifier
            tag_names: Specific tags to confirm (None for all pending)
            min_confidence: Only confirm if above this confidence

        Returns:
            Number of suggestions confirmed
        """
        # Get pending suggestions
        suggestions = self.get_for_doc(doc_id, status="pending")

        confirmed = 0
        now = datetime.now().isoformat()

        with self._connection() as conn:
            for suggestion in suggestions:
                # Filter by tag names if specified
                if tag_names and suggestion.tag_name not in tag_names:
                    continue

                # Filter by confidence if specified
                if min_confidence and suggestion.confidence < min_confidence:
                    continue

                # Map source to auto-* format for provenance
                source_map = {
                    "keybert": "auto-keybert",
                    "llm": "auto-llm",
                    "ner": "auto-ner",
                    "imported": "imported",
                }
                tag_source = source_map.get(suggestion.source, f"auto-{suggestion.source}")

                # Add tag with provenance
                self._tag_manager.add(
                    doc_id,
                    suggestion.tag_name,
                    source=tag_source,
                    confidence=suggestion.confidence,
                )

                # Update status
                conn.execute(
                    """
                    UPDATE tag_suggestions
                    SET status = 'confirmed', reviewed_at = ?
                    WHERE doc_id = ? AND tag_name = ? AND source = ?
                    """,
                    (now, doc_id, suggestion.tag_name, suggestion.source),
                )
                confirmed += 1

            conn.commit()

        if confirmed:
            self._logger.info(
                "Confirmed %d suggestions for %s", confirmed, doc_id
            )
        return confirmed

    def reject(
        self,
        doc_id: str,
        tag_names: list[str] | None = None,
    ) -> int:
        """Reject suggestions.

        Rejected suggestions won't be shown again.

        Args:
            doc_id: Document identifier
            tag_names: Specific tags to reject (None for all pending)

        Returns:
            Number of suggestions rejected
        """
        now = datetime.now().isoformat()

        with self._connection() as conn:
            if tag_names:
                # Reject specific tags
                placeholders = ", ".join("?" * len(tag_names))
                cursor = conn.execute(
                    f"""
                    UPDATE tag_suggestions
                    SET status = 'rejected', reviewed_at = ?
                    WHERE doc_id = ? AND tag_name IN ({placeholders})
                      AND status = 'pending'
                    """,
                    [now, doc_id, *tag_names],
                )
            else:
                # Reject all pending
                cursor = conn.execute(
                    """
                    UPDATE tag_suggestions
                    SET status = 'rejected', reviewed_at = ?
                    WHERE doc_id = ? AND status = 'pending'
                    """,
                    (now, doc_id),
                )

            conn.commit()
            rejected = cursor.rowcount

        if rejected:
            self._logger.info("Rejected %d suggestions for %s", rejected, doc_id)
        return rejected

    def clear_for_doc(self, doc_id: str) -> int:
        """Clear all suggestions for a document.

        Args:
            doc_id: Document identifier

        Returns:
            Number of suggestions cleared
        """
        with self._connection() as conn:
            cursor = conn.execute(
                "DELETE FROM tag_suggestions WHERE doc_id = ?",
                (doc_id,),
            )
            conn.commit()
            return cursor.rowcount

    def count_pending(self, doc_id: str | None = None) -> int:
        """Count pending suggestions.

        Args:
            doc_id: Document to count for (None for all)

        Returns:
            Number of pending suggestions
        """
        if doc_id:
            query = "SELECT COUNT(*) as cnt FROM tag_suggestions WHERE doc_id = ? AND status = 'pending'"
            params: tuple[Any, ...] = (doc_id,)
        else:
            query = "SELECT COUNT(*) as cnt FROM tag_suggestions WHERE status = 'pending'"
            params = ()

        with self._connection() as conn:
            row = conn.execute(query, params).fetchone()
            return row["cnt"] if row else 0

    def stats(self) -> dict[str, Any]:
        """Get suggestion statistics.

        Returns:
            Dictionary with counts by status and source
        """
        with self._connection() as conn:
            # Count by status
            status_rows = conn.execute(
                "SELECT status, COUNT(*) as cnt FROM tag_suggestions GROUP BY status"
            ).fetchall()
            by_status = {row["status"]: row["cnt"] for row in status_rows}

            # Count by source
            source_rows = conn.execute(
                "SELECT source, COUNT(*) as cnt FROM tag_suggestions GROUP BY source"
            ).fetchall()
            by_source = {row["source"]: row["cnt"] for row in source_rows}

            # Documents with pending
            docs_pending = conn.execute(
                "SELECT COUNT(DISTINCT doc_id) as cnt FROM tag_suggestions WHERE status = 'pending'"
            ).fetchone()

        return {
            "by_status": by_status,
            "by_source": by_source,
            "docs_with_pending": docs_pending["cnt"] if docs_pending else 0,
            "total": sum(by_status.values()),
        }
