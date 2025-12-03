"""Tag Library for controlled vocabulary management.

F-062: Tag Library Management
- TagNamespace for organising tags into categories
- TagLibrary for managing the controlled vocabulary
- System namespaces (immutable) and user namespaces (customisable)
"""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from ragd.metadata.tags import TagManager

logger = logging.getLogger(__name__)


@dataclass
class TagNamespace:
    """A namespace in the tag library.

    Namespaces organise tags into categories. They can be:
    - Open: Any tag value allowed (e.g., topic/*)
    - Closed: Only predefined values allowed (e.g., status/[draft,review,approved])
    """

    name: str
    tags: list[str] = field(default_factory=list)
    is_open: bool = False
    is_system: bool = False
    is_hidden: bool = False
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to dictionary for storage."""
        return {
            "name": self.name,
            "tags": self.tags,
            "is_open": self.is_open,
            "is_system": self.is_system,
            "is_hidden": self.is_hidden,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TagNamespace":
        """Create TagNamespace from dictionary."""
        return cls(
            name=data["name"],
            tags=data.get("tags", []),
            is_open=data.get("is_open", False),
            is_system=data.get("is_system", False),
            is_hidden=data.get("is_hidden", False),
            description=data.get("description", ""),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now(),
        )

    def validate_tag(self, tag_value: str) -> tuple[bool, str]:
        """Validate a tag value against this namespace.

        Args:
            tag_value: The tag value (without namespace prefix)

        Returns:
            (is_valid, message)
        """
        if self.is_open:
            return True, "Open namespace accepts any value"

        if tag_value in self.tags:
            return True, "Tag in namespace"

        return False, f"Tag '{tag_value}' not in closed namespace '{self.name}'"


@dataclass
class LibraryConfig:
    """Configuration for tag library."""

    enforce_namespaces: bool = False  # If true, reject unnamespaced tags
    suggest_namespace: bool = True  # Suggest namespace when adding tags
    auto_create_namespace: bool = False  # Auto-create namespace for new patterns


# System namespace definitions
SYSTEM_NAMESPACES = {
    "document-type": {
        "tags": ["report", "article", "documentation", "legal", "financial", "academic", "other"],
        "description": "Document classification by type",
    },
    "sensitivity": {
        "tags": ["public", "internal", "confidential"],
        "description": "Data sensitivity classification",
    },
    "status": {
        "tags": ["draft", "review", "approved", "archived"],
        "description": "Document workflow status",
    },
}


class TagLibrary:
    """Manages the controlled vocabulary for tags.

    Provides namespace management and tag validation.
    """

    def __init__(self, db_path: Path, tag_manager: "TagManager") -> None:
        """Initialise the tag library.

        Args:
            db_path: Path to SQLite database file
            tag_manager: TagManager instance for tag operations
        """
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._tag_manager = tag_manager
        self._config = LibraryConfig()
        self._init_schema()
        self._init_system_namespaces()
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
        """Initialise database schema for tag library."""
        with self._connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS tag_namespaces (
                    name TEXT PRIMARY KEY,
                    is_open BOOLEAN DEFAULT FALSE,
                    is_system BOOLEAN DEFAULT FALSE,
                    is_hidden BOOLEAN DEFAULT FALSE,
                    description TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tag_namespace_values (
                    namespace TEXT NOT NULL,
                    tag_value TEXT NOT NULL,
                    PRIMARY KEY (namespace, tag_value),
                    FOREIGN KEY (namespace) REFERENCES tag_namespaces(name)
                        ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS pending_library_tags (
                    tag_name TEXT PRIMARY KEY,
                    suggested_namespace TEXT,
                    created_at TEXT NOT NULL
                );
            """)
            conn.commit()

    def _init_system_namespaces(self) -> None:
        """Initialise system namespaces if not present."""
        with self._connection() as conn:
            for ns_name, ns_data in SYSTEM_NAMESPACES.items():
                # Check if exists
                row = conn.execute(
                    "SELECT name FROM tag_namespaces WHERE name = ?",
                    (ns_name,),
                ).fetchone()

                if row is None:
                    # Create system namespace
                    conn.execute(
                        """
                        INSERT INTO tag_namespaces
                        (name, is_open, is_system, is_hidden, description, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            ns_name,
                            False,  # Closed
                            True,   # System
                            False,  # Not hidden
                            ns_data["description"],
                            datetime.now().isoformat(),
                        ),
                    )

                    # Add tag values
                    for tag_value in ns_data["tags"]:
                        conn.execute(
                            "INSERT INTO tag_namespace_values (namespace, tag_value) VALUES (?, ?)",
                            (ns_name, tag_value),
                        )

            conn.commit()

    def configure(self, config: LibraryConfig) -> None:
        """Update configuration.

        Args:
            config: New configuration settings
        """
        self._config = config

    def create_namespace(
        self,
        name: str,
        *,
        is_open: bool = False,
        description: str = "",
        tags: list[str] | None = None,
    ) -> TagNamespace:
        """Create a new namespace.

        Args:
            name: Namespace name (must be unique)
            is_open: If True, any tag value allowed; if False, only predefined values
            description: Optional description
            tags: Initial tag values (for closed namespaces)

        Returns:
            Created TagNamespace

        Raises:
            ValueError: If name already exists
        """
        name = name.lower().strip()

        with self._connection() as conn:
            # Check for existing
            row = conn.execute(
                "SELECT name FROM tag_namespaces WHERE name = ?",
                (name,),
            ).fetchone()

            if row:
                raise ValueError(f"Namespace already exists: {name}")

            now = datetime.now().isoformat()
            conn.execute(
                """
                INSERT INTO tag_namespaces
                (name, is_open, is_system, is_hidden, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, is_open, False, False, description, now),
            )

            # Add initial tags
            if tags and not is_open:
                for tag_value in tags:
                    conn.execute(
                        "INSERT INTO tag_namespace_values (namespace, tag_value) VALUES (?, ?)",
                        (name, tag_value.lower().strip()),
                    )

            conn.commit()

        namespace = TagNamespace(
            name=name,
            tags=tags or [],
            is_open=is_open,
            description=description,
        )
        self._logger.info(
            "Created namespace '%s' (%s)",
            name,
            "open" if is_open else "closed",
        )
        return namespace

    def get_namespace(self, name: str) -> TagNamespace | None:
        """Get a namespace by name.

        Args:
            name: Namespace name

        Returns:
            TagNamespace or None if not found
        """
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM tag_namespaces WHERE name = ?",
                (name.lower(),),
            ).fetchone()

            if row is None:
                return None

            # Get tag values
            tags_rows = conn.execute(
                "SELECT tag_value FROM tag_namespace_values WHERE namespace = ?",
                (name.lower(),),
            ).fetchall()

            return TagNamespace(
                name=row["name"],
                tags=[r["tag_value"] for r in tags_rows],
                is_open=bool(row["is_open"]),
                is_system=bool(row["is_system"]),
                is_hidden=bool(row["is_hidden"]),
                description=row["description"] or "",
                created_at=datetime.fromisoformat(row["created_at"]),
            )

    def list_namespaces(self, *, include_hidden: bool = False) -> list[TagNamespace]:
        """List all namespaces.

        Args:
            include_hidden: Include hidden namespaces

        Returns:
            List of namespaces
        """
        query = "SELECT * FROM tag_namespaces"
        if not include_hidden:
            query += " WHERE is_hidden = FALSE"
        query += " ORDER BY is_system DESC, name"

        with self._connection() as conn:
            rows = conn.execute(query).fetchall()
            namespaces = []

            for row in rows:
                tags_rows = conn.execute(
                    "SELECT tag_value FROM tag_namespace_values WHERE namespace = ?",
                    (row["name"],),
                ).fetchall()

                namespaces.append(TagNamespace(
                    name=row["name"],
                    tags=[r["tag_value"] for r in tags_rows],
                    is_open=bool(row["is_open"]),
                    is_system=bool(row["is_system"]),
                    is_hidden=bool(row["is_hidden"]),
                    description=row["description"] or "",
                    created_at=datetime.fromisoformat(row["created_at"]),
                ))

            return namespaces

    def add_tag_to_namespace(self, namespace: str, tag_value: str) -> bool:
        """Add a tag value to a namespace.

        Args:
            namespace: Namespace name
            tag_value: Tag value to add

        Returns:
            True if added, False if namespace not found or already exists
        """
        namespace = namespace.lower()
        tag_value = tag_value.lower().strip()

        ns = self.get_namespace(namespace)
        if ns is None:
            self._logger.warning("Namespace not found: %s", namespace)
            return False

        if ns.is_open:
            self._logger.warning("Cannot add tags to open namespace: %s", namespace)
            return False

        with self._connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO tag_namespace_values (namespace, tag_value) VALUES (?, ?)",
                    (namespace, tag_value),
                )
                conn.commit()
                self._logger.info("Added '%s' to namespace '%s'", tag_value, namespace)
                return True
            except sqlite3.IntegrityError:
                return False  # Already exists

    def remove_tag_from_namespace(self, namespace: str, tag_value: str) -> bool:
        """Remove a tag value from a namespace.

        Args:
            namespace: Namespace name
            tag_value: Tag value to remove

        Returns:
            True if removed, False if not found
        """
        namespace = namespace.lower()
        tag_value = tag_value.lower().strip()

        with self._connection() as conn:
            cursor = conn.execute(
                "DELETE FROM tag_namespace_values WHERE namespace = ? AND tag_value = ?",
                (namespace, tag_value),
            )
            conn.commit()
            removed = cursor.rowcount > 0

        if removed:
            self._logger.info("Removed '%s' from namespace '%s'", tag_value, namespace)
        return removed

    def delete_namespace(self, name: str) -> bool:
        """Delete a namespace.

        Cannot delete system namespaces.

        Args:
            name: Namespace name

        Returns:
            True if deleted, False if not found or is system

        Raises:
            ValueError: If attempting to delete system namespace
        """
        name = name.lower()
        ns = self.get_namespace(name)

        if ns is None:
            return False

        if ns.is_system:
            raise ValueError(f"Cannot delete system namespace: {name}")

        with self._connection() as conn:
            conn.execute(
                "DELETE FROM tag_namespace_values WHERE namespace = ?",
                (name,),
            )
            conn.execute(
                "DELETE FROM tag_namespaces WHERE name = ?",
                (name,),
            )
            conn.commit()

        self._logger.info("Deleted namespace '%s'", name)
        return True

    def hide_namespace(self, name: str, hidden: bool = True) -> bool:
        """Hide or show a namespace.

        Args:
            name: Namespace name
            hidden: True to hide, False to show

        Returns:
            True if updated, False if not found
        """
        with self._connection() as conn:
            cursor = conn.execute(
                "UPDATE tag_namespaces SET is_hidden = ? WHERE name = ?",
                (hidden, name.lower()),
            )
            conn.commit()
            return cursor.rowcount > 0

    def validate_tag(self, tag: str) -> tuple[bool, str]:
        """Validate a tag against the library.

        Args:
            tag: Full tag (may include namespace like "status/draft")

        Returns:
            (is_valid, message)
        """
        if "/" not in tag:
            if self._config.enforce_namespaces:
                return False, "Unnamespaced tags not allowed"
            return True, "Unnamespaced tags allowed"

        namespace, value = tag.split("/", 1)
        ns = self.get_namespace(namespace)

        if ns is None:
            return False, f"Unknown namespace: {namespace}"

        return ns.validate_tag(value)

    def validate_all_tags(self) -> list[tuple[str, str, str]]:
        """Validate all tags in the knowledge base.

        Returns:
            List of (doc_id, tag, error_message) for invalid tags
        """
        invalid: list[tuple[str, str, str]] = []

        for doc_id in self._tag_manager._store.list_ids():
            tags = self._tag_manager.get_names(doc_id)
            for tag in tags:
                valid, message = self.validate_tag(tag)
                if not valid:
                    invalid.append((doc_id, tag, message))

        return invalid

    def rename_tag_in_namespace(
        self,
        namespace: str,
        old_value: str,
        new_value: str,
    ) -> int:
        """Rename a tag value across the namespace and all documents.

        Args:
            namespace: Namespace name
            old_value: Current tag value
            new_value: New tag value

        Returns:
            Number of documents updated
        """
        namespace = namespace.lower()
        old_value = old_value.lower().strip()
        new_value = new_value.lower().strip()

        old_tag = f"{namespace}/{old_value}"
        new_tag = f"{namespace}/{new_value}"

        # Update namespace definition
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE tag_namespace_values
                SET tag_value = ?
                WHERE namespace = ? AND tag_value = ?
                """,
                (new_value, namespace, old_value),
            )
            conn.commit()

        # Update documents
        return self._tag_manager.rename_tag(old_tag, new_tag)

    def add_pending_tag(self, tag_name: str, suggested_namespace: str | None = None) -> bool:
        """Add a tag to the pending list for library review.

        Args:
            tag_name: Tag name
            suggested_namespace: Suggested namespace for the tag

        Returns:
            True if added, False if already exists
        """
        with self._connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO pending_library_tags
                    (tag_name, suggested_namespace, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (tag_name.lower(), suggested_namespace, datetime.now().isoformat()),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def get_pending_tags(self) -> list[tuple[str, str | None]]:
        """Get pending tags awaiting promotion.

        Returns:
            List of (tag_name, suggested_namespace) tuples
        """
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT tag_name, suggested_namespace FROM pending_library_tags ORDER BY tag_name"
            ).fetchall()
            return [(row["tag_name"], row["suggested_namespace"]) for row in rows]

    def promote_pending_tag(self, tag_name: str, namespace: str) -> bool:
        """Promote a pending tag to a namespace.

        Args:
            tag_name: Tag name to promote
            namespace: Target namespace

        Returns:
            True if promoted, False if not found or failed
        """
        tag_name = tag_name.lower()
        namespace = namespace.lower()

        # Add to namespace
        if not self.add_tag_to_namespace(namespace, tag_name):
            return False

        # Remove from pending
        with self._connection() as conn:
            conn.execute(
                "DELETE FROM pending_library_tags WHERE tag_name = ?",
                (tag_name,),
            )
            conn.commit()

        self._logger.info("Promoted '%s' to namespace '%s'", tag_name, namespace)
        return True

    def reject_pending_tag(self, tag_name: str) -> bool:
        """Remove a tag from the pending list.

        Args:
            tag_name: Tag name to reject

        Returns:
            True if removed, False if not found
        """
        with self._connection() as conn:
            cursor = conn.execute(
                "DELETE FROM pending_library_tags WHERE tag_name = ?",
                (tag_name.lower(),),
            )
            conn.commit()
            return cursor.rowcount > 0

    def stats(self) -> dict[str, Any]:
        """Get library statistics.

        Returns:
            Dictionary with namespace and tag counts
        """
        with self._connection() as conn:
            ns_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM tag_namespaces"
            ).fetchone()

            system_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM tag_namespaces WHERE is_system = TRUE"
            ).fetchone()

            tag_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM tag_namespace_values"
            ).fetchone()

            pending_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM pending_library_tags"
            ).fetchone()

        return {
            "total_namespaces": ns_count["cnt"] if ns_count else 0,
            "system_namespaces": system_count["cnt"] if system_count else 0,
            "user_namespaces": (ns_count["cnt"] if ns_count else 0) - (system_count["cnt"] if system_count else 0),
            "total_tag_values": tag_count["cnt"] if tag_count else 0,
            "pending_tags": pending_count["cnt"] if pending_count else 0,
        }
