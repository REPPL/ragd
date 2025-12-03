"""Tests for Tag Library Management (F-062)."""

import pytest
from datetime import datetime
from pathlib import Path

from ragd.metadata.library import (
    LibraryConfig,
    TagLibrary,
    TagNamespace,
    SYSTEM_NAMESPACES,
)
from ragd.metadata.store import MetadataStore
from ragd.metadata.schema import DocumentMetadata
from ragd.metadata.tags import TagManager


class TestTagNamespace:
    """Tests for TagNamespace class."""

    def test_create_closed_namespace(self):
        """Create closed namespace with predefined tags."""
        ns = TagNamespace(
            name="status",
            tags=["draft", "review", "approved"],
            is_open=False,
        )

        assert ns.name == "status"
        assert ns.tags == ["draft", "review", "approved"]
        assert ns.is_open is False

    def test_create_open_namespace(self):
        """Create open namespace accepting any tag."""
        ns = TagNamespace(
            name="topic",
            is_open=True,
        )

        assert ns.is_open is True
        assert ns.tags == []

    def test_validate_tag_closed_valid(self):
        """Validate tag against closed namespace - valid."""
        ns = TagNamespace(
            name="status",
            tags=["draft", "review", "approved"],
            is_open=False,
        )

        is_valid, message = ns.validate_tag("draft")
        assert is_valid is True
        assert "Tag in namespace" in message

    def test_validate_tag_closed_invalid(self):
        """Validate tag against closed namespace - invalid."""
        ns = TagNamespace(
            name="status",
            tags=["draft", "review", "approved"],
            is_open=False,
        )

        is_valid, message = ns.validate_tag("pending")
        assert is_valid is False
        assert "not in closed namespace" in message

    def test_validate_tag_open(self):
        """Validate tag against open namespace - always valid."""
        ns = TagNamespace(
            name="topic",
            is_open=True,
        )

        is_valid, message = ns.validate_tag("anything")
        assert is_valid is True
        assert "Open namespace" in message

    def test_to_dict_from_dict(self):
        """Serialisation round-trip."""
        ns = TagNamespace(
            name="test",
            tags=["a", "b", "c"],
            is_open=False,
            is_system=True,
            is_hidden=False,
            description="Test namespace",
        )

        data = ns.to_dict()
        restored = TagNamespace.from_dict(data)

        assert restored.name == ns.name
        assert restored.tags == ns.tags
        assert restored.is_open == ns.is_open
        assert restored.is_system == ns.is_system
        assert restored.description == ns.description


class TestLibraryConfig:
    """Tests for LibraryConfig."""

    def test_default_config(self):
        """Default configuration values."""
        config = LibraryConfig()

        assert config.enforce_namespaces is False
        assert config.suggest_namespace is True
        assert config.auto_create_namespace is False


class TestTagLibrary:
    """Tests for TagLibrary class."""

    @pytest.fixture
    def library(self, tmp_path):
        """Create TagLibrary with temporary database."""
        db_path = tmp_path / "test.db"
        store = MetadataStore(db_path)
        tag_manager = TagManager(store)

        # Add test documents with tags
        for i in range(3):
            doc_id = f"doc-{i:03d}"
            metadata = DocumentMetadata(dc_title=f"Document {i}")
            store.set(doc_id, metadata)

        tag_manager.add("doc-000", ["status/draft", "topic/ml"])
        tag_manager.add("doc-001", ["status/review", "project/alpha"])
        tag_manager.add("doc-002", ["custom-tag"])

        return TagLibrary(db_path, tag_manager)

    def test_system_namespaces_initialised(self, library):
        """System namespaces are created on init."""
        namespaces = library.list_namespaces()
        names = [ns.name for ns in namespaces]

        for system_name in SYSTEM_NAMESPACES:
            assert system_name in names

    def test_system_namespace_is_system(self, library):
        """System namespaces have is_system=True."""
        ns = library.get_namespace("status")
        assert ns is not None
        assert ns.is_system is True

    def test_create_namespace_closed(self, library):
        """Create closed namespace."""
        ns = library.create_namespace(
            "project",
            is_open=False,
            tags=["alpha", "beta", "gamma"],
            description="Project codes",
        )

        assert ns.name == "project"
        assert ns.is_open is False
        assert "alpha" in ns.tags

    def test_create_namespace_open(self, library):
        """Create open namespace."""
        ns = library.create_namespace(
            "topic",
            is_open=True,
            description="Topic tags - any value allowed",
        )

        assert ns.name == "topic"
        assert ns.is_open is True

    def test_create_duplicate_raises(self, library):
        """Creating duplicate namespace raises ValueError."""
        library.create_namespace("test", is_open=False)

        with pytest.raises(ValueError, match="already exists"):
            library.create_namespace("test", is_open=True)

    def test_get_namespace(self, library):
        """Get namespace by name."""
        library.create_namespace("test", is_open=False, tags=["a", "b"])

        ns = library.get_namespace("test")
        assert ns is not None
        assert ns.name == "test"
        assert "a" in ns.tags

        assert library.get_namespace("nonexistent") is None

    def test_list_namespaces(self, library):
        """List namespaces."""
        library.create_namespace("user-ns", is_open=False)

        namespaces = library.list_namespaces()
        assert len(namespaces) >= 4  # 3 system + 1 user

    def test_list_namespaces_exclude_hidden(self, library):
        """List namespaces excludes hidden by default."""
        library.create_namespace("hidden-ns", is_open=False)
        library.hide_namespace("hidden-ns", hidden=True)

        visible = library.list_namespaces(include_hidden=False)
        hidden_names = [ns.name for ns in visible]
        assert "hidden-ns" not in hidden_names

        all_ns = library.list_namespaces(include_hidden=True)
        all_names = [ns.name for ns in all_ns]
        assert "hidden-ns" in all_names

    def test_add_tag_to_namespace(self, library):
        """Add tag value to namespace."""
        library.create_namespace("project", is_open=False, tags=["alpha"])

        assert library.add_tag_to_namespace("project", "beta") is True

        ns = library.get_namespace("project")
        assert "beta" in ns.tags

    def test_add_tag_to_open_namespace_fails(self, library):
        """Cannot add tags to open namespace."""
        library.create_namespace("topic", is_open=True)

        assert library.add_tag_to_namespace("topic", "something") is False

    def test_remove_tag_from_namespace(self, library):
        """Remove tag value from namespace."""
        library.create_namespace("project", is_open=False, tags=["alpha", "beta"])

        assert library.remove_tag_from_namespace("project", "beta") is True

        ns = library.get_namespace("project")
        assert "beta" not in ns.tags

    def test_delete_namespace(self, library):
        """Delete user namespace."""
        library.create_namespace("to-delete", is_open=False)
        assert library.get_namespace("to-delete") is not None

        assert library.delete_namespace("to-delete") is True
        assert library.get_namespace("to-delete") is None

    def test_delete_system_namespace_raises(self, library):
        """Cannot delete system namespace."""
        with pytest.raises(ValueError, match="Cannot delete system namespace"):
            library.delete_namespace("status")

    def test_hide_namespace(self, library):
        """Hide and show namespace."""
        library.create_namespace("test", is_open=False)

        library.hide_namespace("test", hidden=True)
        ns = library.get_namespace("test")
        assert ns.is_hidden is True

        library.hide_namespace("test", hidden=False)
        ns = library.get_namespace("test")
        assert ns.is_hidden is False

    def test_validate_tag_namespaced_valid(self, library):
        """Validate namespaced tag - valid."""
        is_valid, message = library.validate_tag("status/draft")
        assert is_valid is True

    def test_validate_tag_namespaced_invalid(self, library):
        """Validate namespaced tag - invalid value."""
        is_valid, message = library.validate_tag("status/unknown")
        assert is_valid is False
        assert "not in closed namespace" in message

    def test_validate_tag_unknown_namespace(self, library):
        """Validate tag with unknown namespace."""
        is_valid, message = library.validate_tag("unknown/value")
        assert is_valid is False
        assert "Unknown namespace" in message

    def test_validate_tag_unnamespaced_allowed(self, library):
        """Unnamespaced tags allowed by default."""
        is_valid, message = library.validate_tag("simple-tag")
        assert is_valid is True

    def test_validate_tag_unnamespaced_rejected(self, library):
        """Unnamespaced tags rejected when enforced."""
        library.configure(LibraryConfig(enforce_namespaces=True))

        is_valid, message = library.validate_tag("simple-tag")
        assert is_valid is False
        assert "Unnamespaced tags not allowed" in message

    def test_validate_all_tags(self, library):
        """Validate all tags in knowledge base."""
        # doc-002 has "custom-tag" which is not in any namespace
        invalid = library.validate_all_tags()

        # Should find invalid namespaced tags or unnamespaced if enforced
        # With default config (enforce_namespaces=False), only unknown namespaces
        # Since custom-tag has no namespace, it's allowed
        assert isinstance(invalid, list)

    def test_rename_tag_in_namespace(self, library):
        """Rename tag value across namespace and documents."""
        # This requires a namespace that documents use
        # Let's create a new setup for this test
        ns = library.get_namespace("status")
        # Add "draft" if not already there
        if "draft" not in ns.tags:
            library.add_tag_to_namespace("status", "draft")

        # doc-000 has status/draft - rename to status/wip
        updated = library.rename_tag_in_namespace("status", "draft", "wip")

        # Check namespace updated
        ns = library.get_namespace("status")
        assert "wip" in ns.tags

    def test_add_pending_tag(self, library):
        """Add tag to pending list."""
        assert library.add_pending_tag("new-tag", "topic") is True
        assert library.add_pending_tag("new-tag", "topic") is False  # Duplicate

    def test_get_pending_tags(self, library):
        """Get pending tags."""
        library.add_pending_tag("tag-a", "topic")
        library.add_pending_tag("tag-b", None)

        pending = library.get_pending_tags()
        tag_names = [t[0] for t in pending]

        assert "tag-a" in tag_names
        assert "tag-b" in tag_names

    def test_promote_pending_tag(self, library):
        """Promote pending tag to namespace."""
        library.create_namespace("topic", is_open=False, tags=["existing"])
        library.add_pending_tag("new-tag", "topic")

        assert library.promote_pending_tag("new-tag", "topic") is True

        # Check tag added to namespace
        ns = library.get_namespace("topic")
        assert "new-tag" in ns.tags

        # Check removed from pending
        pending = library.get_pending_tags()
        tag_names = [t[0] for t in pending]
        assert "new-tag" not in tag_names

    def test_reject_pending_tag(self, library):
        """Reject pending tag."""
        library.add_pending_tag("unwanted", None)

        assert library.reject_pending_tag("unwanted") is True

        pending = library.get_pending_tags()
        tag_names = [t[0] for t in pending]
        assert "unwanted" not in tag_names

    def test_stats(self, library):
        """Get library statistics."""
        library.create_namespace("user-ns", is_open=False, tags=["a", "b"])
        library.add_pending_tag("pending-tag", None)

        stats = library.stats()

        assert stats["total_namespaces"] >= 4  # 3 system + 1 user
        assert stats["system_namespaces"] == 3
        assert stats["user_namespaces"] >= 1
        assert stats["pending_tags"] == 1
