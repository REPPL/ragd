"""Operation audit trail for ragd (F-112).

Provides persistent logging of all operations for:
- Debugging issues
- Understanding index state
- Compliance and recovery
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ragd.config import DEFAULT_DATA_DIR, load_config


@dataclass
class AuditEntry:
    """A single audit log entry.

    Records details of an operation performed on the index.
    """

    id: str
    timestamp: datetime
    operation: str  # "index", "delete", "search", "doctor", etc.
    target: str | None  # File path or query
    result: str  # "success", "partial", "failed"
    duration_ms: int
    details: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        operation: str,
        target: str | None = None,
        result: str = "success",
        duration_ms: int = 0,
        **details: Any,
    ) -> AuditEntry:
        """Create a new audit entry.

        Args:
            operation: Type of operation performed
            target: Target of the operation (file, query, etc.)
            result: Outcome of the operation
            duration_ms: Duration in milliseconds
            **details: Additional operation-specific details

        Returns:
            New AuditEntry instance
        """
        return cls(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            operation=operation,
            target=target,
            result=result,
            duration_ms=duration_ms,
            details=details,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialisation."""
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d

    @classmethod
    def from_row(cls, row: tuple) -> AuditEntry:
        """Create from database row.

        Args:
            row: Database row tuple

        Returns:
            AuditEntry instance
        """
        return cls(
            id=row[0],
            timestamp=datetime.fromisoformat(row[1]),
            operation=row[2],
            target=row[3],
            result=row[4],
            duration_ms=row[5] or 0,
            details=json.loads(row[6]) if row[6] else {},
        )


class AuditLog:
    """Persistent audit log storage.

    Stores audit entries in SQLite for querying.
    """

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialise audit log.

        Args:
            db_path: Path to SQLite database. Defaults to config path.
        """
        if db_path is None:
            try:
                config = load_config()
                db_path = config.storage.data_dir / "audit.db"
            except Exception:
                db_path = DEFAULT_DATA_DIR / "audit.db"

        self.db_path = db_path
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        """Create tables if they don't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    target TEXT,
                    result TEXT NOT NULL,
                    duration_ms INTEGER,
                    details TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp
                ON audit_log(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_operation
                ON audit_log(operation)
            """)
            conn.commit()

    def add(self, entry: AuditEntry) -> None:
        """Add an audit entry.

        Args:
            entry: Audit entry to add
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO audit_log
                (id, timestamp, operation, target, result, duration_ms, details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.id,
                    entry.timestamp.isoformat(),
                    entry.operation,
                    entry.target,
                    entry.result,
                    entry.duration_ms,
                    json.dumps(entry.details) if entry.details else None,
                ),
            )
            conn.commit()

    def list(
        self,
        operation: str | None = None,
        result: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditEntry]:
        """List audit entries with filters.

        Args:
            operation: Filter by operation type
            result: Filter by result
            since: Filter entries after this time
            until: Filter entries before this time
            limit: Maximum entries to return
            offset: Offset for pagination

        Returns:
            List of matching audit entries
        """
        query = "SELECT * FROM audit_log WHERE 1=1"
        params: list[Any] = []

        if operation:
            query += " AND operation = ?"
            params.append(operation)
        if result:
            query += " AND result = ?"
            params.append(result)
        if since:
            query += " AND timestamp >= ?"
            params.append(since.isoformat())
        if until:
            query += " AND timestamp <= ?"
            params.append(until.isoformat())

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            return [AuditEntry.from_row(row) for row in cursor.fetchall()]

    def get(self, entry_id: str) -> AuditEntry | None:
        """Get a specific audit entry.

        Args:
            entry_id: ID of the entry to retrieve

        Returns:
            AuditEntry if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM audit_log WHERE id = ?",
                (entry_id,),
            )
            row = cursor.fetchone()
            return AuditEntry.from_row(row) if row else None

    def count(
        self,
        operation: str | None = None,
        result: str | None = None,
    ) -> int:
        """Count audit entries.

        Args:
            operation: Filter by operation type
            result: Filter by result

        Returns:
            Count of matching entries
        """
        query = "SELECT COUNT(*) FROM audit_log WHERE 1=1"
        params: list[Any] = []

        if operation:
            query += " AND operation = ?"
            params.append(operation)
        if result:
            query += " AND result = ?"
            params.append(result)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()[0]

    def clear(self, before: datetime | None = None) -> int:
        """Clear audit entries.

        Args:
            before: Only clear entries before this time.
                   If None, clears all entries.

        Returns:
            Number of entries cleared
        """
        if before:
            query = "DELETE FROM audit_log WHERE timestamp < ?"
            params = [before.isoformat()]
        else:
            query = "DELETE FROM audit_log"
            params = []

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount

    def rotate(self, max_entries: int = 10000, max_age_days: int = 90) -> int:
        """Rotate audit log to prevent unbounded growth.

        Args:
            max_entries: Maximum entries to keep
            max_age_days: Maximum age in days

        Returns:
            Number of entries removed
        """
        removed = 0

        # Remove old entries
        cutoff = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        from datetime import timedelta
        cutoff = cutoff - timedelta(days=max_age_days)
        removed += self.clear(before=cutoff)

        # Remove excess entries
        count = self.count()
        if count > max_entries:
            excess = count - max_entries
            with sqlite3.connect(self.db_path) as conn:
                # Delete oldest entries beyond limit
                conn.execute(
                    """
                    DELETE FROM audit_log WHERE id IN (
                        SELECT id FROM audit_log
                        ORDER BY timestamp ASC
                        LIMIT ?
                    )
                    """,
                    (excess,),
                )
                conn.commit()
                removed += excess

        return removed


# Global audit log instance
_audit_log: AuditLog | None = None


def get_audit_log() -> AuditLog:
    """Get the global audit log instance.

    Returns:
        AuditLog instance
    """
    global _audit_log
    if _audit_log is None:
        _audit_log = AuditLog()
    return _audit_log


@contextmanager
def audit_operation(
    operation: str,
    target: str | None = None,
    **initial_details: Any,
) -> Generator[dict[str, Any], None, None]:
    """Context manager for auditing operations.

    Usage:
        with audit_operation("index", "/path/to/file.pdf") as ctx:
            # Do work
            ctx["documents"] = 5
            ctx["chunks"] = 150

    Args:
        operation: Type of operation
        target: Target of the operation
        **initial_details: Initial details to include

    Yields:
        Dictionary to add details to during operation
    """
    start_time = time.monotonic()
    details = dict(initial_details)
    result = "success"

    try:
        yield details
    except Exception as e:
        result = "failed"
        details["error"] = str(e)
        raise
    finally:
        duration_ms = int((time.monotonic() - start_time) * 1000)

        # Check for partial success
        if details.get("failed", 0) > 0 and details.get("succeeded", 0) > 0:
            result = "partial"

        entry = AuditEntry.create(
            operation=operation,
            target=target,
            result=result,
            duration_ms=duration_ms,
            **details,
        )

        try:
            get_audit_log().add(entry)
        except Exception:
            # Don't fail operations due to audit logging errors
            pass


def log_operation(
    operation: str,
    target: str | None = None,
    result: str = "success",
    duration_ms: int = 0,
    **details: Any,
) -> AuditEntry:
    """Log an operation directly.

    Args:
        operation: Type of operation
        target: Target of the operation
        result: Outcome of the operation
        duration_ms: Duration in milliseconds
        **details: Additional details

    Returns:
        Created audit entry
    """
    entry = AuditEntry.create(
        operation=operation,
        target=target,
        result=result,
        duration_ms=duration_ms,
        **details,
    )
    get_audit_log().add(entry)
    return entry
