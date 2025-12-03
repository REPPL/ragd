"""Tests for Smart Collections (F-063)."""

import pytest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from ragd.metadata.collections import (
    Collection,
    CollectionManager,
    TagQuery,
)
from ragd.metadata.store import MetadataStore
from ragd.metadata.schema import DocumentMetadata
from ragd.metadata.tags import TagManager


class TestTagQuery:
    """Tests for TagQuery class."""

    def test_empty_query_matches_all(self):
        """Empty query matches any document."""
        query = TagQuery()
        assert query.matches(["any", "tags"])
        assert query.matches([])

    def test_include_all_and_logic(self):
        """include_all requires ALL tags (AND logic)."""
        query = TagQuery(include_all=["finance", "q3-2024"])

        assert query.matches(["finance", "q3-2024"])
        assert query.matches(["finance", "q3-2024", "approved"])
        assert not query.matches(["finance"])
        assert not query.matches(["q3-2024"])
        assert not query.matches([])

    def test_include_any_or_logic(self):
        """include_any requires at least ONE tag (OR logic)."""
        query = TagQuery(include_any=["academic", "research", "papers"])

        assert query.matches(["academic"])
        assert query.matches(["research"])
        assert query.matches(["papers"])
        assert query.matches(["academic", "research"])
        assert not query.matches(["other"])
        assert not query.matches([])

    def test_exclude_not_logic(self):
        """exclude rejects documents with ANY excluded tag (NOT logic)."""
        query = TagQuery(exclude=["draft", "archived"])

        assert query.matches(["approved"])
        assert query.matches([])
        assert not query.matches(["draft"])
        assert not query.matches(["archived"])
        assert not query.matches(["approved", "draft"])

    def test_combined_logic(self):
        """Test combined AND, OR, NOT logic."""
        query = TagQuery(
            include_all=["finance"],
            include_any=["q3-2024", "q4-2024"],
            exclude=["draft"],
        )

        assert query.matches(["finance", "q3-2024"])
        assert query.matches(["finance", "q4-2024"])
        assert query.matches(["finance", "q3-2024", "approved"])
        assert not query.matches(["finance"])  # Missing include_any
        assert not query.matches(["q3-2024"])  # Missing include_all
        assert not query.matches(["finance", "q3-2024", "draft"])  # Has exclude

    def test_wildcard_pattern(self):
        """Wildcard patterns match prefixes."""
        query = TagQuery(include_any=["project/*"])

        assert query.matches(["project/alpha"])
        assert query.matches(["project/beta"])
        assert not query.matches(["project"])
        assert not query.matches(["projects/alpha"])

    def test_wildcard_exclude(self):
        """Wildcard patterns in exclude."""
        query = TagQuery(exclude=["status/*"])

        assert query.matches(["approved"])
        assert not query.matches(["status/draft"])
        assert not query.matches(["status/archived"])

    def test_to_string(self):
        """Query string representation."""
        query = TagQuery(
            include_all=["finance", "q3-2024"],
            exclude=["draft"],
        )
        result = query.to_string()
        assert "finance" in result
        assert "AND" in result
        assert "NOT" in result

    def test_to_dict_from_dict(self):
        """Serialisation round-trip."""
        query = TagQuery(
            include_all=["a", "b"],
            include_any=["c", "d"],
            exclude=["e"],
        )
        data = query.to_dict()
        restored = TagQuery.from_dict(data)

        assert restored.include_all == query.include_all
        assert restored.include_any == query.include_any
        assert restored.exclude == query.exclude

    def test_is_empty(self):
        """Test is_empty check."""
        assert TagQuery().is_empty()
        assert not TagQuery(include_all=["a"]).is_empty()
        assert not TagQuery(include_any=["a"]).is_empty()
        assert not TagQuery(exclude=["a"]).is_empty()


class TestCollection:
    """Tests for Collection class."""

    def test_generate_id(self):
        """ID generation from name."""
        id1 = Collection.generate_id("Q3 Finance")
        assert id1.startswith("col-q3-finance-")

        # Different timestamps produce different IDs
        id2 = Collection.generate_id("Q3 Finance")
        # IDs might be same if generated in same millisecond, but that's ok

    def test_to_dict_from_dict(self):
        """Serialisation round-trip."""
        collection = Collection(
            id="col-test-123",
            name="Test Collection",
            query=TagQuery(include_all=["test"]),
            description="A test collection",
            parent_id="col-parent-456",
        )
        data = collection.to_dict()
        restored = Collection.from_dict(data)

        assert restored.id == collection.id
        assert restored.name == collection.name
        assert restored.description == collection.description
        assert restored.parent_id == collection.parent_id
        assert restored.query.include_all == collection.query.include_all


class TestCollectionManager:
    """Tests for CollectionManager class."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create CollectionManager with temporary database."""
        db_path = tmp_path / "test.db"
        store = MetadataStore(db_path)
        tag_manager = TagManager(store)

        # Add some test documents with tags
        for i in range(5):
            doc_id = f"doc-{i:03d}"
            metadata = DocumentMetadata(dc_title=f"Document {i}")
            store.set(doc_id, metadata)

        # Add tags
        tag_manager.add("doc-000", ["finance", "q3-2024"])
        tag_manager.add("doc-001", ["finance", "q3-2024", "draft"])
        tag_manager.add("doc-002", ["finance", "q4-2024"])
        tag_manager.add("doc-003", ["research", "academic"])
        tag_manager.add("doc-004", ["research"])

        return CollectionManager(db_path, tag_manager)

    def test_create_collection(self, manager):
        """Create a new collection."""
        collection = manager.create(
            "Q3 Finance",
            include_all=["finance", "q3-2024"],
            exclude=["draft"],
        )

        assert collection.name == "Q3 Finance"
        assert collection.query.include_all == ["finance", "q3-2024"]
        assert collection.query.exclude == ["draft"]

    def test_create_duplicate_raises(self, manager):
        """Creating duplicate collection raises ValueError."""
        manager.create("Test", include_all=["a"])

        with pytest.raises(ValueError, match="already exists"):
            manager.create("Test", include_all=["b"])

    def test_get_by_name(self, manager):
        """Get collection by name."""
        manager.create("Test Collection", include_all=["test"])

        retrieved = manager.get_by_name("Test Collection")
        assert retrieved is not None
        assert retrieved.name == "Test Collection"

        assert manager.get_by_name("Nonexistent") is None

    def test_list_all(self, manager):
        """List all collections."""
        manager.create("A", include_all=["a"])
        manager.create("B", include_all=["b"])
        manager.create("C", include_all=["c"])

        collections = manager.list_all()
        assert len(collections) == 3
        assert [c.name for c in collections] == ["A", "B", "C"]  # Sorted by name

    def test_update_collection(self, manager):
        """Update collection query."""
        manager.create("Test", include_all=["a"])

        assert manager.update("Test", include_all=["b", "c"])

        updated = manager.get_by_name("Test")
        assert updated.query.include_all == ["b", "c"]

    def test_delete_collection(self, manager):
        """Delete collection."""
        manager.create("To Delete", include_all=["a"])
        assert manager.get_by_name("To Delete") is not None

        assert manager.delete("To Delete")
        assert manager.get_by_name("To Delete") is None

    def test_get_members(self, manager):
        """Get documents matching collection query."""
        manager.create(
            "Q3 Finance",
            include_all=["finance", "q3-2024"],
            exclude=["draft"],
        )

        members = manager.get_members("Q3 Finance")
        assert "doc-000" in members  # Has finance, q3-2024, no draft
        assert "doc-001" not in members  # Has draft
        assert "doc-002" not in members  # Has q4-2024, not q3-2024

    def test_count_members(self, manager):
        """Count documents in collection."""
        manager.create("Research", include_any=["research", "academic"])

        count = manager.count_members("Research")
        assert count == 2  # doc-003 and doc-004

    def test_get_collections_for_doc(self, manager):
        """Find collections containing a document."""
        manager.create("Finance", include_all=["finance"])
        manager.create("Research", include_all=["research"])
        manager.create("Q3", include_any=["q3-2024"])

        collections = manager.get_collections_for_doc("doc-000")
        names = [c.name for c in collections]

        assert "Finance" in names
        assert "Q3" in names
        assert "Research" not in names

    def test_nested_collections(self, manager):
        """Test parent-child collection relationship."""
        manager.create("Finance", include_all=["finance"])
        manager.create(
            "Finance/Q3",
            include_all=["q3-2024"],
            parent_name="Finance",
        )

        parent = manager.get_by_name("Finance")
        child = manager.get_by_name("Finance/Q3")

        assert child.parent_id == parent.id

        children = manager.list_children("Finance")
        assert len(children) == 1
        assert children[0].name == "Finance/Q3"

    def test_parent_not_found_raises(self, manager):
        """Creating collection with nonexistent parent raises ValueError."""
        with pytest.raises(ValueError, match="Parent collection not found"):
            manager.create("Child", include_all=["a"], parent_name="Nonexistent")

    def test_count(self, manager):
        """Count total collections."""
        assert manager.count() == 0

        manager.create("A", include_all=["a"])
        manager.create("B", include_all=["b"])

        assert manager.count() == 2
