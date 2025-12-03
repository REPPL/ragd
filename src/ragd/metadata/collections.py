"""Smart Collections for virtual document organisation.

F-063: Smart Collections
- TagQuery with boolean logic (AND, OR, NOT)
- Collection dataclass with saved queries
- Auto-updating virtual folders based on tag queries
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from fnmatch import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from ragd.metadata.tags import TagManager

logger = logging.getLogger(__name__)


@dataclass
class TagQuery:
    """Boolean combination of tags for collection membership.

    Supports:
    - include_all: Document must have ALL these tags (AND logic)
    - include_any: Document must have at least ONE of these tags (OR logic)
    - exclude: Document must NOT have any of these tags (NOT logic)
    - Wildcards: "project/*" matches any tag starting with "project/"
    """

    include_all: list[str] = field(default_factory=list)
    include_any: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)

    def matches(self, doc_tags: list[str]) -> bool:
        """Check if document tags match this query.

        Args:
            doc_tags: List of tag names from the document

        Returns:
            True if document matches the query
        """
        doc_set = set(doc_tags)

        # Must have ALL include_all tags
        if self.include_all:
            for tag in self.include_all:
                if not self._tag_matches(tag, doc_set):
                    return False

        # Must have at least ONE include_any tag (if specified)
        if self.include_any:
            matched = False
            for tag in self.include_any:
                if self._tag_matches(tag, doc_set):
                    matched = True
                    break
            if not matched:
                return False

        # Must NOT have any exclude tags
        if self.exclude:
            for tag in self.exclude:
                if self._tag_matches(tag, doc_set):
                    return False

        return True

    def _tag_matches(self, pattern: str, doc_tags: set[str]) -> bool:
        """Check if a pattern matches any document tag.

        Supports wildcards: "project/*" matches "project/alpha".
        """
        if pattern.endswith("/*"):
            prefix = pattern[:-1]  # "project/"
            return any(t.startswith(prefix) for t in doc_tags)
        elif "*" in pattern:
            # General fnmatch pattern
            return any(fnmatch(t, pattern) for t in doc_tags)
        else:
            return pattern in doc_tags

    def to_string(self) -> str:
        """Human-readable query representation."""
        parts = []
        if self.include_all:
            parts.append(" AND ".join(self.include_all))
        if self.include_any:
            parts.append(f"({' OR '.join(self.include_any)})")
        if self.exclude:
            parts.append(f"NOT ({' OR '.join(self.exclude)})")
        return " AND ".join(parts) if parts else "*"

    def to_dict(self) -> dict[str, Any]:
        """Serialise to dictionary for storage."""
        return {
            "include_all": self.include_all,
            "include_any": self.include_any,
            "exclude": self.exclude,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TagQuery":
        """Create TagQuery from dictionary."""
        return cls(
            include_all=data.get("include_all", []),
            include_any=data.get("include_any", []),
            exclude=data.get("exclude", []),
        )

    def is_empty(self) -> bool:
        """Check if query has no criteria (matches all)."""
        return not self.include_all and not self.include_any and not self.exclude


@dataclass
class Collection:
    """A saved tag query that auto-collects matching documents.

    Collections are virtual folders - they don't move or copy documents,
    just provide a filtered view based on tag queries.
    """

    id: str
    name: str
    query: TagQuery
    description: str = ""
    parent_id: str | None = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to dictionary for storage."""
        return {
            "id": self.id,
            "name": self.name,
            "query": self.query.to_dict(),
            "description": self.description,
            "parent_id": self.parent_id,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Collection":
        """Create Collection from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            query=TagQuery.from_dict(data["query"]),
            description=data.get("description", ""),
            parent_id=data.get("parent_id"),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now(),
        )

    @staticmethod
    def generate_id(name: str) -> str:
        """Generate a unique ID from collection name."""
        slug = name.lower().replace(" ", "-").replace("/", "-")
        hash_suffix = hashlib.sha256(
            f"{slug}-{datetime.now().isoformat()}".encode()
        ).hexdigest()[:8]
        return f"col-{slug[:20]}-{hash_suffix}"


class CollectionManager:
    """Manages smart collections in SQLite storage.

    Provides CRUD operations for collections and membership queries.
    """

    def __init__(self, db_path: Path, tag_manager: "TagManager") -> None:
        """Initialise the collection manager.

        Args:
            db_path: Path to SQLite database file
            tag_manager: TagManager instance for tag queries
        """
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._tag_manager = tag_manager
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
        """Initialise database schema for collections."""
        with self._connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS collections (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    parent_id TEXT REFERENCES collections(id),
                    include_all TEXT,
                    include_any TEXT,
                    exclude TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_collections_parent
                    ON collections(parent_id);

                CREATE INDEX IF NOT EXISTS idx_collections_name
                    ON collections(name);
            """)
            conn.commit()

    def create(
        self,
        name: str,
        *,
        include_all: list[str] | None = None,
        include_any: list[str] | None = None,
        exclude: list[str] | None = None,
        description: str = "",
        parent_name: str | None = None,
    ) -> Collection:
        """Create a new collection.

        Args:
            name: Collection name (must be unique)
            include_all: Tags that must ALL be present (AND)
            include_any: Tags where at least ONE must be present (OR)
            exclude: Tags that must NOT be present (NOT)
            description: Optional description
            parent_name: Optional parent collection name for nesting

        Returns:
            Created Collection

        Raises:
            ValueError: If name already exists or parent not found
        """
        # Resolve parent ID
        parent_id = None
        if parent_name:
            parent = self.get_by_name(parent_name)
            if parent is None:
                raise ValueError(f"Parent collection not found: {parent_name}")
            parent_id = parent.id

        query = TagQuery(
            include_all=include_all or [],
            include_any=include_any or [],
            exclude=exclude or [],
        )

        collection = Collection(
            id=Collection.generate_id(name),
            name=name,
            query=query,
            description=description,
            parent_id=parent_id,
        )

        with self._connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO collections
                    (id, name, description, parent_id, include_all, include_any,
                     exclude, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        collection.id,
                        collection.name,
                        collection.description,
                        collection.parent_id,
                        json.dumps(query.include_all),
                        json.dumps(query.include_any),
                        json.dumps(query.exclude),
                        collection.created_at.isoformat(),
                    ),
                )
                conn.commit()
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed" in str(e):
                    raise ValueError(f"Collection already exists: {name}") from e
                raise

        self._logger.info("Created collection '%s' with query: %s", name, query.to_string())
        return collection

    def get(self, collection_id: str) -> Collection | None:
        """Get a collection by ID.

        Args:
            collection_id: Collection identifier

        Returns:
            Collection or None if not found
        """
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM collections WHERE id = ?",
                (collection_id,),
            ).fetchone()

            if row is None:
                return None

            return self._row_to_collection(row)

    def get_by_name(self, name: str) -> Collection | None:
        """Get a collection by name.

        Args:
            name: Collection name

        Returns:
            Collection or None if not found
        """
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM collections WHERE name = ?",
                (name,),
            ).fetchone()

            if row is None:
                return None

            return self._row_to_collection(row)

    def _row_to_collection(self, row: sqlite3.Row) -> Collection:
        """Convert database row to Collection object."""
        return Collection(
            id=row["id"],
            name=row["name"],
            query=TagQuery(
                include_all=json.loads(row["include_all"]) if row["include_all"] else [],
                include_any=json.loads(row["include_any"]) if row["include_any"] else [],
                exclude=json.loads(row["exclude"]) if row["exclude"] else [],
            ),
            description=row["description"] or "",
            parent_id=row["parent_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def update(
        self,
        name: str,
        *,
        include_all: list[str] | None = None,
        include_any: list[str] | None = None,
        exclude: list[str] | None = None,
        description: str | None = None,
    ) -> bool:
        """Update a collection's query or description.

        Args:
            name: Collection name to update
            include_all: New include_all tags (None to keep existing)
            include_any: New include_any tags (None to keep existing)
            exclude: New exclude tags (None to keep existing)
            description: New description (None to keep existing)

        Returns:
            True if updated, False if not found
        """
        collection = self.get_by_name(name)
        if collection is None:
            return False

        # Build update query
        updates: list[str] = []
        params: list[Any] = []

        if include_all is not None:
            updates.append("include_all = ?")
            params.append(json.dumps(include_all))

        if include_any is not None:
            updates.append("include_any = ?")
            params.append(json.dumps(include_any))

        if exclude is not None:
            updates.append("exclude = ?")
            params.append(json.dumps(exclude))

        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if not updates:
            return True  # Nothing to update

        params.append(name)
        with self._connection() as conn:
            conn.execute(
                f"UPDATE collections SET {', '.join(updates)} WHERE name = ?",
                params,
            )
            conn.commit()

        self._logger.info("Updated collection '%s'", name)
        return True

    def delete(self, name: str) -> bool:
        """Delete a collection.

        Does NOT delete the documents - only the collection.

        Args:
            name: Collection name to delete

        Returns:
            True if deleted, False if not found
        """
        with self._connection() as conn:
            # First update children to remove parent reference
            collection = self.get_by_name(name)
            if collection:
                conn.execute(
                    "UPDATE collections SET parent_id = NULL WHERE parent_id = ?",
                    (collection.id,),
                )

            cursor = conn.execute(
                "DELETE FROM collections WHERE name = ?",
                (name,),
            )
            conn.commit()
            deleted = cursor.rowcount > 0

        if deleted:
            self._logger.info("Deleted collection '%s'", name)
        return deleted

    def list_all(self) -> list[Collection]:
        """List all collections.

        Returns:
            List of all collections, sorted by name
        """
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM collections ORDER BY name"
            ).fetchall()
            return [self._row_to_collection(row) for row in rows]

    def list_children(self, parent_name: str) -> list[Collection]:
        """List child collections of a parent.

        Args:
            parent_name: Parent collection name

        Returns:
            List of child collections
        """
        parent = self.get_by_name(parent_name)
        if parent is None:
            return []

        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM collections WHERE parent_id = ? ORDER BY name",
                (parent.id,),
            ).fetchall()
            return [self._row_to_collection(row) for row in rows]

    def get_members(self, name: str) -> list[str]:
        """Get all document IDs that match a collection's query.

        This is a live query - results update automatically as tags change.

        Args:
            name: Collection name

        Returns:
            List of matching document IDs
        """
        collection = self.get_by_name(name)
        if collection is None:
            return []

        if collection.query.is_empty():
            # Empty query matches all documents
            return self._tag_manager._store.list_ids()

        matching: list[str] = []
        for doc_id in self._tag_manager._store.list_ids():
            doc_tags = self._tag_manager.get_names(doc_id)
            if collection.query.matches(doc_tags):
                matching.append(doc_id)

        return matching

    def count_members(self, name: str) -> int:
        """Count documents matching a collection's query.

        Args:
            name: Collection name

        Returns:
            Number of matching documents
        """
        return len(self.get_members(name))

    def get_collections_for_doc(self, doc_id: str) -> list[Collection]:
        """Get all collections that contain a document.

        Args:
            doc_id: Document identifier

        Returns:
            List of collections containing the document
        """
        doc_tags = self._tag_manager.get_names(doc_id)
        matching: list[Collection] = []

        for collection in self.list_all():
            if collection.query.matches(doc_tags):
                matching.append(collection)

        return matching

    def count(self) -> int:
        """Count total collections.

        Returns:
            Number of collections
        """
        with self._connection() as conn:
            row = conn.execute("SELECT COUNT(*) as cnt FROM collections").fetchone()
            return row["cnt"] if row else 0
