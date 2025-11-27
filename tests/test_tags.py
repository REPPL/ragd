"""Tests for tag management module."""

from __future__ import annotations

from pathlib import Path

import pytest

from ragd.metadata import DocumentMetadata, MetadataStore, TagManager


class TestTagManager:
    """Tests for TagManager class."""

    @pytest.fixture
    def store(self, tmp_path: Path) -> MetadataStore:
        """Create a temporary metadata store."""
        return MetadataStore(tmp_path / "metadata.sqlite")

    @pytest.fixture
    def tags(self, store: MetadataStore) -> TagManager:
        """Create a tag manager."""
        return TagManager(store)

    @pytest.fixture
    def sample_docs(self, store: MetadataStore) -> list[str]:
        """Create sample documents with metadata."""
        doc_ids = ["doc-001", "doc-002", "doc-003"]
        for doc_id in doc_ids:
            store.set(doc_id, DocumentMetadata(dc_title=f"Document {doc_id}"))
        return doc_ids

    def test_add_single_tag(
        self,
        tags: TagManager,
        store: MetadataStore,
        sample_docs: list[str],
    ) -> None:
        """Test adding a single tag."""
        result = tags.add("doc-001", "important")
        assert result is True

        doc_tags = tags.get("doc-001")
        assert "important" in doc_tags

    def test_add_multiple_tags(
        self,
        tags: TagManager,
        sample_docs: list[str],
    ) -> None:
        """Test adding multiple tags at once."""
        result = tags.add("doc-001", ["tag1", "tag2", "tag3"])
        assert result is True

        doc_tags = tags.get("doc-001")
        assert "tag1" in doc_tags
        assert "tag2" in doc_tags
        assert "tag3" in doc_tags

    def test_add_tag_nonexistent_doc(self, tags: TagManager) -> None:
        """Test adding tag to non-existent document."""
        result = tags.add("nonexistent", "tag")
        assert result is False

    def test_add_duplicate_tags(
        self,
        tags: TagManager,
        sample_docs: list[str],
    ) -> None:
        """Test that duplicate tags are deduplicated."""
        tags.add("doc-001", "tag1")
        tags.add("doc-001", "tag1")  # Duplicate

        doc_tags = tags.get("doc-001")
        assert doc_tags.count("tag1") == 1

    def test_remove_tag(
        self,
        tags: TagManager,
        sample_docs: list[str],
    ) -> None:
        """Test removing a tag."""
        tags.add("doc-001", ["tag1", "tag2"])
        result = tags.remove("doc-001", "tag1")
        assert result is True

        doc_tags = tags.get("doc-001")
        assert "tag1" not in doc_tags
        assert "tag2" in doc_tags

    def test_remove_multiple_tags(
        self,
        tags: TagManager,
        sample_docs: list[str],
    ) -> None:
        """Test removing multiple tags."""
        tags.add("doc-001", ["tag1", "tag2", "tag3"])
        result = tags.remove("doc-001", ["tag1", "tag2"])
        assert result is True

        doc_tags = tags.get("doc-001")
        assert "tag1" not in doc_tags
        assert "tag2" not in doc_tags
        assert "tag3" in doc_tags

    def test_remove_nonexistent_tag(
        self,
        tags: TagManager,
        sample_docs: list[str],
    ) -> None:
        """Test removing a tag that doesn't exist."""
        tags.add("doc-001", "tag1")
        result = tags.remove("doc-001", "nonexistent")
        assert result is True  # No error, just no change

    def test_get_tags_empty(
        self,
        tags: TagManager,
        sample_docs: list[str],
    ) -> None:
        """Test getting tags from document with no tags."""
        doc_tags = tags.get("doc-001")
        assert doc_tags == []

    def test_get_tags_nonexistent_doc(self, tags: TagManager) -> None:
        """Test getting tags from non-existent document."""
        doc_tags = tags.get("nonexistent")
        assert doc_tags == []

    def test_set_tags(
        self,
        tags: TagManager,
        sample_docs: list[str],
    ) -> None:
        """Test setting exact tags (replacing existing)."""
        tags.add("doc-001", ["old1", "old2"])
        result = tags.set("doc-001", ["new1", "new2"])
        assert result is True

        doc_tags = tags.get("doc-001")
        assert "old1" not in doc_tags
        assert "old2" not in doc_tags
        assert "new1" in doc_tags
        assert "new2" in doc_tags

    def test_clear_tags(
        self,
        tags: TagManager,
        sample_docs: list[str],
    ) -> None:
        """Test clearing all tags."""
        tags.add("doc-001", ["tag1", "tag2"])
        result = tags.clear("doc-001")
        assert result is True

        doc_tags = tags.get("doc-001")
        assert doc_tags == []

    def test_list_all_tags(
        self,
        tags: TagManager,
        sample_docs: list[str],
    ) -> None:
        """Test listing all unique tags."""
        tags.add("doc-001", ["tag1", "tag2"])
        tags.add("doc-002", ["tag2", "tag3"])
        tags.add("doc-003", ["tag3", "tag4"])

        all_tags = tags.list_all_tags()
        assert set(all_tags) == {"tag1", "tag2", "tag3", "tag4"}
        assert all_tags == sorted(all_tags)  # Should be sorted

    def test_find_by_tags_match_all(
        self,
        tags: TagManager,
        sample_docs: list[str],
    ) -> None:
        """Test finding documents with ALL specified tags."""
        tags.add("doc-001", ["important", "reviewed"])
        tags.add("doc-002", ["important"])
        tags.add("doc-003", ["important", "reviewed", "archived"])

        # Find docs with both important AND reviewed
        results = tags.find_by_tags(["important", "reviewed"], match_all=True)
        assert "doc-001" in results
        assert "doc-002" not in results
        assert "doc-003" in results

    def test_find_by_tags_match_any(
        self,
        tags: TagManager,
        sample_docs: list[str],
    ) -> None:
        """Test finding documents with ANY specified tags."""
        tags.add("doc-001", ["important"])
        tags.add("doc-002", ["reviewed"])
        tags.add("doc-003", [])

        # Find docs with important OR reviewed
        results = tags.find_by_tags(["important", "reviewed"], match_all=False)
        assert "doc-001" in results
        assert "doc-002" in results
        assert "doc-003" not in results

    def test_find_by_tags_empty(self, tags: TagManager) -> None:
        """Test find_by_tags with empty tag list."""
        results = tags.find_by_tags([])
        assert results == []

    def test_tag_counts(
        self,
        tags: TagManager,
        sample_docs: list[str],
    ) -> None:
        """Test getting tag usage counts."""
        tags.add("doc-001", ["tag1", "tag2"])
        tags.add("doc-002", ["tag2", "tag3"])
        tags.add("doc-003", ["tag2"])

        counts = tags.tag_counts()
        assert counts["tag1"] == 1
        assert counts["tag2"] == 3
        assert counts["tag3"] == 1

    def test_rename_tag(
        self,
        tags: TagManager,
        sample_docs: list[str],
    ) -> None:
        """Test renaming a tag across all documents."""
        tags.add("doc-001", "old_tag")
        tags.add("doc-002", "old_tag")
        tags.add("doc-003", "other_tag")

        updated = tags.rename_tag("old_tag", "new_tag")
        assert updated == 2

        assert "new_tag" in tags.get("doc-001")
        assert "new_tag" in tags.get("doc-002")
        assert "old_tag" not in tags.get("doc-001")
        assert "old_tag" not in tags.get("doc-002")
        # doc-003 shouldn't be affected
        assert "other_tag" in tags.get("doc-003")

    def test_rename_tag_same_name(
        self,
        tags: TagManager,
        sample_docs: list[str],
    ) -> None:
        """Test renaming to same name does nothing."""
        tags.add("doc-001", "tag")
        updated = tags.rename_tag("tag", "tag")
        assert updated == 0

    def test_delete_tag(
        self,
        tags: TagManager,
        sample_docs: list[str],
    ) -> None:
        """Test deleting a tag from all documents."""
        tags.add("doc-001", ["tag1", "tag2"])
        tags.add("doc-002", ["tag1", "tag3"])

        updated = tags.delete_tag("tag1")
        assert updated == 2

        assert "tag1" not in tags.get("doc-001")
        assert "tag1" not in tags.get("doc-002")
        assert "tag2" in tags.get("doc-001")
        assert "tag3" in tags.get("doc-002")

    def test_tags_sorted(
        self,
        tags: TagManager,
        sample_docs: list[str],
    ) -> None:
        """Test that tags are always sorted."""
        tags.add("doc-001", ["zebra", "apple", "mango"])

        doc_tags = tags.get("doc-001")
        assert doc_tags == ["apple", "mango", "zebra"]

    def test_whitespace_handling(
        self,
        tags: TagManager,
        sample_docs: list[str],
    ) -> None:
        """Test that whitespace is trimmed from tags."""
        tags.add("doc-001", ["  tag1  ", "tag2 ", " tag3"])

        doc_tags = tags.get("doc-001")
        assert "tag1" in doc_tags
        assert "tag2" in doc_tags
        assert "tag3" in doc_tags

    def test_empty_tags_ignored(
        self,
        tags: TagManager,
        sample_docs: list[str],
    ) -> None:
        """Test that empty/whitespace-only tags are ignored."""
        tags.add("doc-001", ["tag1", "", "  ", "tag2"])

        doc_tags = tags.get("doc-001")
        assert doc_tags == ["tag1", "tag2"]
