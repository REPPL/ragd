"""Tests for tag provenance tracking."""

from __future__ import annotations

from datetime import datetime
import pytest

from ragd.metadata.provenance import (
    TagEntry,
    TagSource,
    normalise_tags,
    serialise_tags,
    get_tag_names,
)


class TestTagEntry:
    """Tests for TagEntry dataclass."""

    def test_create_basic(self) -> None:
        """Test creating a basic tag entry."""
        tag = TagEntry(name="test-tag")
        assert tag.name == "test-tag"
        assert tag.source == "manual"
        assert tag.confidence is None
        assert isinstance(tag.created_at, datetime)
        assert tag.created_by is None

    def test_name_normalisation(self) -> None:
        """Test tag name normalisation."""
        tag = TagEntry(name="  TEST-TAG  ")
        assert tag.name == "test-tag"

    def test_confidence_validation(self) -> None:
        """Test confidence score validation."""
        tag = TagEntry(name="test", confidence=0.5)
        assert tag.confidence == 0.5

        with pytest.raises(ValueError, match="Confidence must be between"):
            TagEntry(name="test", confidence=1.5)

        with pytest.raises(ValueError, match="Confidence must be between"):
            TagEntry(name="test", confidence=-0.1)

    def test_is_auto_generated(self) -> None:
        """Test auto-generated detection."""
        manual = TagEntry(name="test", source="manual")
        assert manual.is_auto_generated is False

        auto = TagEntry(name="test", source="auto-keybert")
        assert auto.is_auto_generated is True

    def test_is_manual(self) -> None:
        """Test manual source detection."""
        manual = TagEntry(name="test", source="manual")
        assert manual.is_manual is True

        auto = TagEntry(name="test", source="auto-llm")
        assert manual.is_manual is True

    def test_is_legacy(self) -> None:
        """Test legacy source detection."""
        legacy = TagEntry(name="test", source="legacy")
        assert legacy.is_legacy is True

        manual = TagEntry(name="test", source="manual")
        assert manual.is_legacy is False

    def test_to_dict(self) -> None:
        """Test serialisation to dictionary."""
        tag = TagEntry(
            name="test-tag",
            source="auto-keybert",
            confidence=0.85,
            created_by="model-v1",
        )
        data = tag.to_dict()

        assert data["name"] == "test-tag"
        assert data["source"] == "auto-keybert"
        assert data["confidence"] == 0.85
        assert data["created_by"] == "model-v1"
        assert "created_at" in data

    def test_from_dict_full(self) -> None:
        """Test deserialisation from full dictionary."""
        data = {
            "name": "test-tag",
            "source": "auto-keybert",
            "confidence": 0.85,
            "created_at": "2024-01-15T10:30:00",
            "created_by": "model-v1",
        }
        tag = TagEntry.from_dict(data)

        assert tag.name == "test-tag"
        assert tag.source == "auto-keybert"
        assert tag.confidence == 0.85
        assert tag.created_by == "model-v1"

    def test_from_dict_string(self) -> None:
        """Test deserialisation from legacy string format."""
        tag = TagEntry.from_dict("test-tag")

        assert tag.name == "test-tag"
        assert tag.source == "legacy"
        assert tag.confidence is None

    def test_manual_factory(self) -> None:
        """Test manual tag factory method."""
        tag = TagEntry.manual("important", created_by="user-123")

        assert tag.name == "important"
        assert tag.source == "manual"
        assert tag.created_by == "user-123"

    def test_auto_keybert_factory(self) -> None:
        """Test auto-keybert factory method."""
        tag = TagEntry.auto_keybert("machine-learning", 0.89, model="keybert-v1")

        assert tag.name == "machine-learning"
        assert tag.source == "auto-keybert"
        assert tag.confidence == 0.89
        assert tag.created_by == "keybert-v1"

    def test_auto_llm_factory(self) -> None:
        """Test auto-llm factory method."""
        tag = TagEntry.auto_llm("tutorial", 0.95, model="llama3.2:3b")

        assert tag.name == "tutorial"
        assert tag.source == "auto-llm"
        assert tag.confidence == 0.95
        assert tag.created_by == "llama3.2:3b"

    def test_str_representation(self) -> None:
        """Test string representation."""
        tag = TagEntry(name="test-tag")
        assert str(tag) == "test-tag"

    def test_repr(self) -> None:
        """Test detailed representation."""
        tag = TagEntry(name="test", source="auto-keybert", confidence=0.85)
        repr_str = repr(tag)
        assert "test" in repr_str
        assert "auto-keybert" in repr_str
        assert "0.85" in repr_str

    def test_equality_with_tag_entry(self) -> None:
        """Test equality with another TagEntry."""
        tag1 = TagEntry(name="test")
        tag2 = TagEntry(name="test", source="auto-keybert")
        tag3 = TagEntry(name="other")

        assert tag1 == tag2  # Same name, different source
        assert tag1 != tag3

    def test_equality_with_string(self) -> None:
        """Test equality with string."""
        tag = TagEntry(name="test")
        assert tag == "test"
        assert tag == "  TEST  "  # normalisation
        assert tag != "other"

    def test_hash(self) -> None:
        """Test hash for set operations."""
        tag1 = TagEntry(name="test")
        tag2 = TagEntry(name="test", source="auto-keybert")

        # Same name = same hash (for deduplication)
        assert hash(tag1) == hash(tag2)

        tags = {tag1, tag2}
        assert len(tags) == 1

    def test_sorting(self) -> None:
        """Test sorting by name."""
        tags = [
            TagEntry(name="zebra"),
            TagEntry(name="apple"),
            TagEntry(name="mango"),
        ]
        sorted_tags = sorted(tags)

        assert sorted_tags[0].name == "apple"
        assert sorted_tags[1].name == "mango"
        assert sorted_tags[2].name == "zebra"


class TestNormaliseTags:
    """Tests for normalise_tags function."""

    def test_normalise_strings(self) -> None:
        """Test normalising string tags."""
        tags = ["test", "important"]
        result = normalise_tags(tags)

        assert len(result) == 2
        assert all(isinstance(t, TagEntry) for t in result)
        assert result[0].source == "legacy"

    def test_normalise_dicts(self) -> None:
        """Test normalising dictionary tags."""
        tags = [
            {"name": "test", "source": "auto-keybert", "confidence": 0.85},
        ]
        result = normalise_tags(tags)

        assert len(result) == 1
        assert result[0].name == "test"
        assert result[0].source == "auto-keybert"
        assert result[0].confidence == 0.85

    def test_normalise_mixed(self) -> None:
        """Test normalising mixed tag formats."""
        tags = [
            "legacy-tag",
            TagEntry(name="entry-tag"),
            {"name": "dict-tag", "source": "manual"},
        ]
        result = normalise_tags(tags)

        assert len(result) == 3
        assert all(isinstance(t, TagEntry) for t in result)

    def test_normalise_tag_entries(self) -> None:
        """Test normalising existing TagEntry objects."""
        original = TagEntry(name="test", source="auto-keybert")
        result = normalise_tags([original])

        assert len(result) == 1
        assert result[0] is original  # Same object


class TestSerialiseTags:
    """Tests for serialise_tags function."""

    def test_serialise_to_dicts(self) -> None:
        """Test serialising tags to dictionaries."""
        tags = [
            TagEntry(name="test", source="manual"),
            TagEntry(name="auto", source="auto-keybert", confidence=0.8),
        ]
        result = serialise_tags(tags)

        assert len(result) == 2
        assert all(isinstance(d, dict) for d in result)
        assert result[0]["name"] == "test"
        assert result[1]["confidence"] == 0.8


class TestGetTagNames:
    """Tests for get_tag_names function."""

    def test_extract_names(self) -> None:
        """Test extracting names from TagEntry list."""
        tags = [
            TagEntry(name="apple"),
            TagEntry(name="banana"),
            TagEntry(name="cherry"),
        ]
        names = get_tag_names(tags)

        assert names == ["apple", "banana", "cherry"]

    def test_empty_list(self) -> None:
        """Test with empty list."""
        names = get_tag_names([])
        assert names == []
