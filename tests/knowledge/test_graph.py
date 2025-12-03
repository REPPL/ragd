"""Tests for knowledge graph (F-022)."""

import pytest
from pathlib import Path

from ragd.knowledge.entities import Entity, EntityType
from ragd.knowledge.graph import (
    GraphConfig,
    GraphStats,
    KnowledgeGraph,
    Relationship,
)


class TestRelationship:
    """Tests for Relationship dataclass."""

    def test_create_relationship(self):
        """Create relationship with all fields."""
        rel = Relationship(
            source="python",
            target="django",
            type="USES",
            weight=0.9,
            doc_id="doc-123",
        )

        assert rel.source == "python"
        assert rel.target == "django"
        assert rel.type == "USES"
        assert rel.weight == 0.9

    def test_to_dict_from_dict(self):
        """Serialisation round-trip."""
        rel = Relationship(
            source="a",
            target="b",
            type="RELATED_TO",
            weight=0.75,
        )

        data = rel.to_dict()
        restored = Relationship.from_dict(data)

        assert restored.source == rel.source
        assert restored.target == rel.target
        assert restored.weight == rel.weight


class TestGraphConfig:
    """Tests for GraphConfig."""

    def test_default_config(self):
        """Default configuration values."""
        config = GraphConfig()

        assert config.enabled is True
        assert config.cooccurrence_window == 3
        assert config.hop_limit == 2

    def test_custom_config(self):
        """Custom configuration values."""
        config = GraphConfig(
            enabled=False,
            hop_limit=3,
            weight_threshold=0.5,
        )

        assert config.enabled is False
        assert config.hop_limit == 3
        assert config.weight_threshold == 0.5


class TestKnowledgeGraph:
    """Tests for KnowledgeGraph."""

    @pytest.fixture
    def graph(self, tmp_path):
        """Create KnowledgeGraph with temporary database."""
        db_path = tmp_path / "test_graph.db"
        return KnowledgeGraph(db_path)

    def test_add_entity(self, graph):
        """Add single entity."""
        entity = Entity(
            name="Python",
            type=EntityType.TECHNOLOGY,
            start=0,
            end=6,
        )

        result = graph.add_entity(entity, "doc-001")
        assert result is True

        # Verify retrieval
        node = graph.get_entity("python")
        assert node is not None
        assert node.name == "python"
        assert node.type == EntityType.TECHNOLOGY

    def test_add_entities_batch(self, graph):
        """Add multiple entities in batch."""
        entities = [
            Entity(name="Python", type=EntityType.TECHNOLOGY),
            Entity(name="Django", type=EntityType.TECHNOLOGY),
            Entity(name="REST", type=EntityType.CONCEPT),
        ]

        added = graph.add_entities_batch(entities, "doc-001")
        assert added == 3

        # Check stats
        stats = graph.stats()
        assert stats.entity_count == 3

    def test_cooccurrence_relationships(self, graph):
        """Entities in same batch create relationships."""
        entities = [
            Entity(name="Python", type=EntityType.TECHNOLOGY),
            Entity(name="Django", type=EntityType.TECHNOLOGY),
        ]

        graph.add_entities_batch(entities, "doc-001")

        stats = graph.stats()
        assert stats.relationship_count >= 1

    def test_add_relationship(self, graph):
        """Add explicit relationship."""
        # First add entities
        graph.add_entity(
            Entity(name="Python", type=EntityType.TECHNOLOGY),
            "doc-001",
        )
        graph.add_entity(
            Entity(name="Django", type=EntityType.TECHNOLOGY),
            "doc-001",
        )

        # Add relationship
        rel = Relationship(
            source="python",
            target="django",
            type="USES",
            weight=0.9,
        )
        result = graph.add_relationship(rel)
        assert result is True

    def test_get_related(self, graph):
        """Get related entities."""
        # Add entities with co-occurrence
        entities = [
            Entity(name="Python", type=EntityType.TECHNOLOGY),
            Entity(name="Django", type=EntityType.TECHNOLOGY),
            Entity(name="REST", type=EntityType.CONCEPT),
        ]
        graph.add_entities_batch(entities, "doc-001")

        related = graph.get_related("python", hops=1)

        # Should find django and rest
        names = [name for name, score in related]
        assert "django" in names or "rest" in names

    def test_get_related_with_hops(self, graph):
        """Get related entities with multiple hops."""
        # Chain: A -> B -> C
        graph.add_entities_batch(
            [
                Entity(name="A", type=EntityType.CONCEPT),
                Entity(name="B", type=EntityType.CONCEPT),
            ],
            "doc-001",
        )
        graph.add_entities_batch(
            [
                Entity(name="B", type=EntityType.CONCEPT),
                Entity(name="C", type=EntityType.CONCEPT),
            ],
            "doc-002",
        )

        # 1 hop from A should find B
        related_1 = graph.get_related("a", hops=1)
        names_1 = [name for name, score in related_1]
        assert "b" in names_1

        # 2 hops from A should find C
        related_2 = graph.get_related("a", hops=2)
        names_2 = [name for name, score in related_2]
        assert "c" in names_2

    def test_get_documents_for_entity(self, graph):
        """Get documents mentioning entity."""
        entity = Entity(name="Python", type=EntityType.TECHNOLOGY)
        graph.add_entity(entity, "doc-001")
        graph.add_entity(entity, "doc-002")

        docs = graph.get_documents_for_entity("python")

        assert len(docs) >= 1
        assert "doc-001" in docs

    def test_get_entities_in_document(self, graph):
        """Get entities in a document."""
        entities = [
            Entity(name="Python", type=EntityType.TECHNOLOGY),
            Entity(name="Django", type=EntityType.TECHNOLOGY),
        ]
        graph.add_entities_batch(entities, "doc-001")

        result = graph.get_entities_in_document("doc-001")

        names = [e.name for e in result]
        assert "python" in names
        assert "django" in names

    def test_search_entities(self, graph):
        """Search entities by name."""
        entities = [
            Entity(name="Python", type=EntityType.TECHNOLOGY),
            Entity(name="PyTorch", type=EntityType.TECHNOLOGY),
            Entity(name="Java", type=EntityType.TECHNOLOGY),
        ]
        graph.add_entities_batch(entities, "doc-001")

        results = graph.search_entities("py")

        names = [e.name for e in results]
        assert "python" in names
        assert "pytorch" in names
        assert "java" not in names

    def test_stats(self, graph):
        """Get graph statistics."""
        entities = [
            Entity(name="Python", type=EntityType.TECHNOLOGY),
            Entity(name="Django", type=EntityType.TECHNOLOGY),
            Entity(name="REST", type=EntityType.CONCEPT),
        ]
        graph.add_entities_batch(entities, "doc-001")

        stats = graph.stats()

        assert isinstance(stats, GraphStats)
        assert stats.entity_count == 3
        assert stats.document_count == 1
        assert "TECH" in stats.entities_by_type or "TECHNOLOGY" in stats.entities_by_type

    def test_clear(self, graph):
        """Clear graph data."""
        entities = [
            Entity(name="Python", type=EntityType.TECHNOLOGY),
        ]
        graph.add_entities_batch(entities, "doc-001")

        # Verify data exists
        assert graph.stats().entity_count > 0

        # Clear
        graph.clear()

        # Verify empty
        assert graph.stats().entity_count == 0
        assert graph.stats().relationship_count == 0

    def test_explore(self, graph):
        """Explore entity relationships."""
        entities = [
            Entity(name="Python", type=EntityType.TECHNOLOGY),
            Entity(name="Django", type=EntityType.TECHNOLOGY),
        ]
        graph.add_entities_batch(entities, "doc-001")

        result = graph.explore("python")

        assert "entity" in result
        assert result["entity"]["name"] == "python"
        assert "related" in result
        assert "documents" in result

    def test_explore_not_found(self, graph):
        """Explore non-existent entity returns error."""
        result = graph.explore("nonexistent")

        assert "error" in result

    def test_case_insensitive(self, graph):
        """Entity names are case-insensitive."""
        entity = Entity(name="Python", type=EntityType.TECHNOLOGY)
        graph.add_entity(entity, "doc-001")

        # Should find with different case
        assert graph.get_entity("python") is not None
        assert graph.get_entity("PYTHON") is not None
        assert graph.get_entity("Python") is not None
