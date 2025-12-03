"""Tests for data sensitivity tier management."""

from __future__ import annotations

import pytest
from pathlib import Path

from ragd.security.tiers import (
    DataTier,
    TierAccessError,
    TierConfig,
    TierManager,
    get_tier_colour,
    get_tier_icon,
)


class TestDataTier:
    """Tests for DataTier enum."""

    def test_tier_values(self) -> None:
        """Test tier value strings."""
        assert DataTier.PUBLIC.value == "public"
        assert DataTier.PERSONAL.value == "personal"
        assert DataTier.SENSITIVE.value == "sensitive"
        assert DataTier.CRITICAL.value == "critical"

    def test_tier_levels(self) -> None:
        """Test tier level ordering."""
        assert DataTier.PUBLIC.level == 0
        assert DataTier.PERSONAL.level == 1
        assert DataTier.SENSITIVE.level == 2
        assert DataTier.CRITICAL.level == 3

    def test_tier_comparison_less_than(self) -> None:
        """Test tier < comparison."""
        assert DataTier.PUBLIC < DataTier.PERSONAL
        assert DataTier.PERSONAL < DataTier.SENSITIVE
        assert DataTier.SENSITIVE < DataTier.CRITICAL
        assert not DataTier.CRITICAL < DataTier.PUBLIC

    def test_tier_comparison_greater_than(self) -> None:
        """Test tier > comparison."""
        assert DataTier.CRITICAL > DataTier.SENSITIVE
        assert DataTier.SENSITIVE > DataTier.PERSONAL
        assert DataTier.PERSONAL > DataTier.PUBLIC
        assert not DataTier.PUBLIC > DataTier.CRITICAL

    def test_tier_comparison_less_equal(self) -> None:
        """Test tier <= comparison."""
        assert DataTier.PUBLIC <= DataTier.PUBLIC
        assert DataTier.PUBLIC <= DataTier.PERSONAL
        assert not DataTier.CRITICAL <= DataTier.PUBLIC

    def test_tier_comparison_greater_equal(self) -> None:
        """Test tier >= comparison."""
        assert DataTier.CRITICAL >= DataTier.CRITICAL
        assert DataTier.CRITICAL >= DataTier.PUBLIC
        assert not DataTier.PUBLIC >= DataTier.CRITICAL

    def test_from_string_valid(self) -> None:
        """Test parsing valid tier strings."""
        assert DataTier.from_string("public") == DataTier.PUBLIC
        assert DataTier.from_string("PERSONAL") == DataTier.PERSONAL
        assert DataTier.from_string("  Sensitive  ") == DataTier.SENSITIVE
        assert DataTier.from_string("CRITICAL") == DataTier.CRITICAL

    def test_from_string_invalid(self) -> None:
        """Test parsing invalid tier strings."""
        with pytest.raises(ValueError, match="Invalid tier"):
            DataTier.from_string("invalid")
        with pytest.raises(ValueError, match="Invalid tier"):
            DataTier.from_string("")

    def test_description(self) -> None:
        """Test tier descriptions."""
        assert "accessible" in DataTier.PUBLIC.description.lower()
        assert "password" in DataTier.PERSONAL.description.lower()
        assert "session" in DataTier.SENSITIVE.description.lower()
        assert "confirmation" in DataTier.CRITICAL.description.lower()


class TestTierConfig:
    """Tests for TierConfig."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = TierConfig()
        assert config.default_tier == DataTier.PERSONAL
        assert config.require_confirmation_for_critical is True

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = TierConfig(
            default_tier=DataTier.PUBLIC,
            require_confirmation_for_critical=False,
        )
        assert config.default_tier == DataTier.PUBLIC
        assert config.require_confirmation_for_critical is False


class TestTierManager:
    """Tests for TierManager."""

    @pytest.fixture
    def tmp_store(self, tmp_path: Path):
        """Create a temporary metadata store."""
        from ragd.metadata.store import MetadataStore
        from ragd.metadata.schema import DocumentMetadata

        db_path = tmp_path / "metadata.sqlite"
        store = MetadataStore(db_path)

        # Add test documents
        store.set("doc-001", DocumentMetadata(dc_title="Public Doc"))
        store.set("doc-002", DocumentMetadata(dc_title="Personal Doc"))
        store.set("doc-003", DocumentMetadata(dc_title="Sensitive Doc"))

        return store

    @pytest.fixture
    def manager(self, tmp_store):
        """Create a tier manager."""
        return TierManager(tmp_store, session=None)

    def test_get_default_tier(self, manager) -> None:
        """Test getting tier for document without explicit tier."""
        tier = manager.get_tier("doc-001")
        assert tier == DataTier.PERSONAL  # default

    def test_set_tier(self, manager) -> None:
        """Test setting document tier."""
        result = manager.set_tier("doc-001", DataTier.SENSITIVE)
        assert result is True

        tier = manager.get_tier("doc-001")
        assert tier == DataTier.SENSITIVE

    def test_set_tier_nonexistent(self, manager) -> None:
        """Test setting tier for nonexistent document."""
        result = manager.set_tier("nonexistent", DataTier.SENSITIVE)
        assert result is False

    def test_can_access_public(self, manager) -> None:
        """Test public tier always accessible."""
        assert manager.can_access(DataTier.PUBLIC) is True

    def test_can_access_personal(self, manager) -> None:
        """Test personal tier accessible without session."""
        assert manager.can_access(DataTier.PERSONAL) is True

    def test_can_access_sensitive_no_session(self, manager) -> None:
        """Test sensitive tier requires session."""
        # Without session manager, sensitive is not accessible
        assert manager.can_access(DataTier.SENSITIVE) is False

    def test_list_by_tier(self, manager) -> None:
        """Test listing documents by tier."""
        manager.set_tier("doc-001", DataTier.SENSITIVE)
        manager.set_tier("doc-002", DataTier.SENSITIVE)

        docs = manager.list_by_tier(DataTier.SENSITIVE)
        assert set(docs) == {"doc-001", "doc-002"}

    def test_tier_counts(self, manager) -> None:
        """Test counting documents per tier."""
        manager.set_tier("doc-001", DataTier.PUBLIC)
        manager.set_tier("doc-002", DataTier.SENSITIVE)

        counts = manager.tier_counts()
        assert counts[DataTier.PUBLIC] == 1
        assert counts[DataTier.SENSITIVE] == 1
        assert counts[DataTier.PERSONAL] == 1  # doc-003 defaults to personal

    def test_promote_tier(self, manager) -> None:
        """Test promoting document tier."""
        manager.set_tier("doc-001", DataTier.PERSONAL)
        new_tier = manager.promote_tier("doc-001")
        assert new_tier == DataTier.SENSITIVE

    def test_promote_tier_at_max(self, manager) -> None:
        """Test promoting at maximum tier."""
        manager.set_tier("doc-001", DataTier.CRITICAL)
        new_tier = manager.promote_tier("doc-001")
        assert new_tier is None

    def test_demote_tier(self, manager) -> None:
        """Test demoting document tier."""
        manager.set_tier("doc-001", DataTier.SENSITIVE)
        new_tier = manager.demote_tier("doc-001")
        assert new_tier == DataTier.PERSONAL

    def test_demote_tier_at_min(self, manager) -> None:
        """Test demoting at minimum tier."""
        manager.set_tier("doc-001", DataTier.PUBLIC)
        new_tier = manager.demote_tier("doc-001")
        assert new_tier is None

    def test_bulk_set_tier(self, manager) -> None:
        """Test bulk tier update."""
        updated = manager.bulk_set_tier(
            ["doc-001", "doc-002", "doc-003"],
            DataTier.SENSITIVE,
        )
        assert updated == 3

        for doc_id in ["doc-001", "doc-002", "doc-003"]:
            assert manager.get_tier(doc_id) == DataTier.SENSITIVE

    def test_filter_by_tier(self, manager) -> None:
        """Test filtering documents by accessible tiers."""
        manager.set_tier("doc-001", DataTier.PUBLIC)
        manager.set_tier("doc-002", DataTier.SENSITIVE)
        manager.set_tier("doc-003", DataTier.PERSONAL)

        # Filter to max PUBLIC tier (only doc-001 accessible)
        accessible = manager.filter_by_tier(
            ["doc-001", "doc-002", "doc-003"],
            max_tier=DataTier.PUBLIC,
        )
        assert accessible == ["doc-001"]


class TestTierAccessError:
    """Tests for TierAccessError."""

    def test_error_message(self) -> None:
        """Test error message."""
        error = TierAccessError("Access denied", DataTier.SENSITIVE)
        assert "Access denied" in str(error)
        assert error.required_tier == DataTier.SENSITIVE


class TestTierDisplayHelpers:
    """Tests for display helper functions."""

    def test_get_tier_colour(self) -> None:
        """Test tier colours."""
        assert get_tier_colour(DataTier.PUBLIC) == "green"
        assert get_tier_colour(DataTier.PERSONAL) == "blue"
        assert get_tier_colour(DataTier.SENSITIVE) == "yellow"
        assert get_tier_colour(DataTier.CRITICAL) == "red"

    def test_get_tier_icon(self) -> None:
        """Test tier icons are defined."""
        for tier in DataTier:
            icon = get_tier_icon(tier)
            assert icon is not None
            assert len(icon) > 0
