"""Knowledge graph storage and querying.

Provides graph-based storage for entities and relationships,
with support for graph-enhanced retrieval.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

from ragd.knowledge.entities import Entity, EntityType, get_entity_extractor

logger = logging.getLogger(__name__)


@dataclass
class Relationship:
    """A relationship between two entities.

    Attributes:
        source: Source entity name
        target: Target entity name
        type: Relationship type
        weight: Relationship strength (0-1)
        doc_id: Document where relationship was found
    """

    source: str
    target: str
    type: str = "RELATED_TO"
    weight: float = 1.0
    doc_id: str = ""

    def to_dict(self) -> dict:
        """Serialise to dictionary."""
        return {
            "source": self.source,
            "target": self.target,
            "type": self.type,
            "weight": self.weight,
            "doc_id": self.doc_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Relationship:
        """Deserialise from dictionary."""
        return cls(
            source=data["source"],
            target=data["target"],
            type=data.get("type", "RELATED_TO"),
            weight=data.get("weight", 1.0),
            doc_id=data.get("doc_id", ""),
        )


@dataclass
class GraphConfig:
    """Configuration for knowledge graph.

    Attributes:
        enabled: Whether graph features are enabled
        cooccurrence_window: Sentences for co-occurrence detection
        min_cooccurrence: Minimum co-occurrences for relationship
        hop_limit: Maximum relationship hops in queries
        weight_threshold: Minimum weight for relationships
    """

    enabled: bool = True
    cooccurrence_window: int = 3
    min_cooccurrence: int = 2
    hop_limit: int = 2
    weight_threshold: float = 0.3


@dataclass
class EntityNode:
    """An entity node in the knowledge graph.

    Attributes:
        name: Entity name (unique identifier)
        type: Entity type
        doc_count: Number of documents mentioning entity
        chunk_count: Number of chunks mentioning entity
    """

    name: str
    type: EntityType
    doc_count: int = 0
    chunk_count: int = 0


@dataclass
class GraphStats:
    """Statistics about the knowledge graph."""

    entity_count: int = 0
    relationship_count: int = 0
    document_count: int = 0
    entities_by_type: dict[str, int] = field(default_factory=dict)


class KnowledgeGraph:
    """SQLite-backed knowledge graph for entity and relationship storage.

    Uses a simple schema:
    - entities: Unique entities with type and counts
    - relationships: Entity pairs with weights
    - entity_mentions: Which documents/chunks mention each entity
    """

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS entities (
        name TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        doc_count INTEGER DEFAULT 0,
        chunk_count INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS relationships (
        source TEXT NOT NULL,
        target TEXT NOT NULL,
        type TEXT NOT NULL DEFAULT 'RELATED_TO',
        weight REAL DEFAULT 1.0,
        cooccurrence_count INTEGER DEFAULT 1,
        PRIMARY KEY (source, target, type),
        FOREIGN KEY (source) REFERENCES entities(name),
        FOREIGN KEY (target) REFERENCES entities(name)
    );

    CREATE TABLE IF NOT EXISTS entity_mentions (
        entity_name TEXT NOT NULL,
        doc_id TEXT NOT NULL,
        chunk_id TEXT,
        position_start INTEGER,
        position_end INTEGER,
        PRIMARY KEY (entity_name, doc_id, chunk_id),
        FOREIGN KEY (entity_name) REFERENCES entities(name)
    );

    CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source);
    CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target);
    CREATE INDEX IF NOT EXISTS idx_mentions_doc ON entity_mentions(doc_id);
    """

    def __init__(
        self,
        db_path: Path | str,
        config: GraphConfig | None = None,
    ) -> None:
        """Initialise knowledge graph.

        Args:
            db_path: Path to SQLite database
            config: Graph configuration
        """
        self.db_path = Path(db_path)
        self.config = config or GraphConfig()
        self._conn: sqlite3.Connection | None = None

        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialise schema
        self._init_schema()

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_schema(self) -> None:
        """Initialise database schema."""
        conn = self._get_conn()
        conn.executescript(self.SCHEMA)
        conn.commit()

    def add_entity(
        self,
        entity: Entity,
        doc_id: str,
        chunk_id: str | None = None,
    ) -> bool:
        """Add or update an entity.

        Args:
            entity: Entity to add
            doc_id: Document ID
            chunk_id: Chunk ID (optional)

        Returns:
            True if entity was added/updated
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        try:
            # Upsert entity
            cursor.execute(
                """
                INSERT INTO entities (name, type, doc_count, chunk_count)
                VALUES (?, ?, 1, 1)
                ON CONFLICT(name) DO UPDATE SET
                    doc_count = doc_count + 1,
                    chunk_count = chunk_count + 1
                """,
                (entity.name.lower(), entity.type.value),
            )

            # Record mention
            cursor.execute(
                """
                INSERT OR IGNORE INTO entity_mentions
                (entity_name, doc_id, chunk_id, position_start, position_end)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    entity.name.lower(),
                    doc_id,
                    chunk_id or "",
                    entity.start,
                    entity.end,
                ),
            )

            conn.commit()
            return True
        except Exception as e:
            logger.warning("Failed to add entity: %s", e)
            return False

    def add_entities_batch(
        self,
        entities: Sequence[Entity],
        doc_id: str,
        chunk_id: str | None = None,
    ) -> int:
        """Add multiple entities in batch.

        Args:
            entities: Entities to add
            doc_id: Document ID
            chunk_id: Chunk ID (optional)

        Returns:
            Number of entities added
        """
        added = 0
        for entity in entities:
            if self.add_entity(entity, doc_id, chunk_id):
                added += 1

        # Detect relationships via co-occurrence
        if len(entities) >= 2:
            self._add_cooccurrence_relationships(entities, doc_id)

        return added

    def _add_cooccurrence_relationships(
        self,
        entities: Sequence[Entity],
        doc_id: str,
    ) -> None:
        """Add relationships based on co-occurrence.

        Args:
            entities: Entities found in same context
            doc_id: Document ID
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        # All pairs co-occur
        for i, e1 in enumerate(entities):
            for e2 in entities[i + 1 :]:
                name1 = min(e1.name.lower(), e2.name.lower())
                name2 = max(e1.name.lower(), e2.name.lower())

                cursor.execute(
                    """
                    INSERT INTO relationships (source, target, type, weight, cooccurrence_count)
                    VALUES (?, ?, 'COOCCURS', 1.0, 1)
                    ON CONFLICT(source, target, type) DO UPDATE SET
                        cooccurrence_count = cooccurrence_count + 1,
                        weight = MIN(1.0, weight + 0.1)
                    """,
                    (name1, name2),
                )

        conn.commit()

    def add_relationship(self, relationship: Relationship) -> bool:
        """Add or update a relationship.

        Args:
            relationship: Relationship to add

        Returns:
            True if relationship was added/updated
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO relationships (source, target, type, weight)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(source, target, type) DO UPDATE SET
                    weight = MAX(weight, excluded.weight)
                """,
                (
                    relationship.source.lower(),
                    relationship.target.lower(),
                    relationship.type,
                    relationship.weight,
                ),
            )
            conn.commit()
            return True
        except Exception as e:
            logger.warning("Failed to add relationship: %s", e)
            return False

    def get_entity(self, name: str) -> EntityNode | None:
        """Get an entity by name.

        Args:
            name: Entity name

        Returns:
            EntityNode or None if not found
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM entities WHERE name = ?",
            (name.lower(),),
        )
        row = cursor.fetchone()

        if row:
            return EntityNode(
                name=row["name"],
                type=EntityType(row["type"]),
                doc_count=row["doc_count"],
                chunk_count=row["chunk_count"],
            )
        return None

    def get_related(
        self,
        entity_name: str,
        hops: int = 1,
        min_weight: float = 0.0,
    ) -> list[tuple[str, float]]:
        """Get entities related to a given entity.

        Args:
            entity_name: Starting entity name
            hops: Maximum relationship hops
            min_weight: Minimum relationship weight

        Returns:
            List of (entity_name, relevance_score) tuples
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        name = entity_name.lower()
        results: dict[str, float] = {}
        visited = {name}
        frontier = [(name, 1.0)]

        for hop in range(hops):
            next_frontier = []

            for current, score in frontier:
                # Get direct relationships
                cursor.execute(
                    """
                    SELECT target as related, weight FROM relationships
                    WHERE source = ? AND weight >= ?
                    UNION
                    SELECT source as related, weight FROM relationships
                    WHERE target = ? AND weight >= ?
                    """,
                    (current, min_weight, current, min_weight),
                )

                for row in cursor:
                    related = row["related"]
                    weight = row["weight"]

                    if related not in visited:
                        visited.add(related)
                        new_score = score * weight * (0.7 ** hop)  # Decay by hop
                        results[related] = max(
                            results.get(related, 0),
                            new_score,
                        )
                        next_frontier.append((related, new_score))

            frontier = next_frontier

        # Sort by score descending
        return sorted(results.items(), key=lambda x: x[1], reverse=True)

    def get_documents_for_entity(self, entity_name: str) -> list[str]:
        """Get documents mentioning an entity.

        Args:
            entity_name: Entity name

        Returns:
            List of document IDs
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT DISTINCT doc_id FROM entity_mentions WHERE entity_name = ?",
            (entity_name.lower(),),
        )

        return [row["doc_id"] for row in cursor]

    def get_entities_in_document(self, doc_id: str) -> list[EntityNode]:
        """Get entities mentioned in a document.

        Args:
            doc_id: Document ID

        Returns:
            List of EntityNode objects
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT e.* FROM entities e
            JOIN entity_mentions m ON e.name = m.entity_name
            WHERE m.doc_id = ?
            """,
            (doc_id,),
        )

        return [
            EntityNode(
                name=row["name"],
                type=EntityType(row["type"]),
                doc_count=row["doc_count"],
                chunk_count=row["chunk_count"],
            )
            for row in cursor
        ]

    def search_entities(
        self,
        query: str,
        limit: int = 10,
    ) -> list[EntityNode]:
        """Search for entities by name.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching EntityNode objects
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM entities
            WHERE name LIKE ?
            ORDER BY doc_count DESC
            LIMIT ?
            """,
            (f"%{query.lower()}%", limit),
        )

        return [
            EntityNode(
                name=row["name"],
                type=EntityType(row["type"]),
                doc_count=row["doc_count"],
                chunk_count=row["chunk_count"],
            )
            for row in cursor
        ]

    def stats(self) -> GraphStats:
        """Get graph statistics.

        Returns:
            GraphStats object
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        # Entity count
        cursor.execute("SELECT COUNT(*) as count FROM entities")
        entity_count = cursor.fetchone()["count"]

        # Relationship count
        cursor.execute("SELECT COUNT(*) as count FROM relationships")
        relationship_count = cursor.fetchone()["count"]

        # Document count
        cursor.execute(
            "SELECT COUNT(DISTINCT doc_id) as count FROM entity_mentions"
        )
        document_count = cursor.fetchone()["count"]

        # By type
        cursor.execute(
            "SELECT type, COUNT(*) as count FROM entities GROUP BY type"
        )
        by_type = {row["type"]: row["count"] for row in cursor}

        return GraphStats(
            entity_count=entity_count,
            relationship_count=relationship_count,
            document_count=document_count,
            entities_by_type=by_type,
        )

    def clear(self) -> None:
        """Clear all graph data."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM entity_mentions")
        cursor.execute("DELETE FROM relationships")
        cursor.execute("DELETE FROM entities")
        conn.commit()

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def explore(
        self,
        entity_name: str,
        hops: int = 2,
    ) -> dict[str, Any]:
        """Explore relationships from an entity.

        Args:
            entity_name: Starting entity
            hops: Maximum hops to explore

        Returns:
            Dictionary with exploration results
        """
        entity = self.get_entity(entity_name)
        if entity is None:
            return {"error": f"Entity not found: {entity_name}"}

        related = self.get_related(entity_name, hops=hops)
        docs = self.get_documents_for_entity(entity_name)

        return {
            "entity": {
                "name": entity.name,
                "type": entity.type.value,
                "doc_count": entity.doc_count,
            },
            "related": [
                {"name": name, "relevance": score}
                for name, score in related[:20]
            ],
            "documents": docs[:10],
        }
