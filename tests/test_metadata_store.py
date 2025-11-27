"""Tests for metadata storage module."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from ragd.metadata import (
    CURRENT_SCHEMA,
    SCHEMA_V1,
    SCHEMA_V2,
    DocumentMetadata,
    MetadataStore,
    get_schema_version,
    migrate_to_current,
    migrate_v1_to_v2,
    needs_migration,
)


class TestDocumentMetadata:
    """Tests for DocumentMetadata dataclass."""

    def test_default_values(self) -> None:
        """Test default values for DocumentMetadata."""
        meta = DocumentMetadata()
        assert meta.ragd_schema_version == "2.0"
        assert meta.dc_title == ""
        assert meta.dc_creator == []
        assert meta.dc_language == "en"
        assert meta.ragd_tags == []

    def test_with_values(self) -> None:
        """Test creating DocumentMetadata with values."""
        meta = DocumentMetadata(
            dc_title="Test Document",
            dc_creator=["Author One", "Author Two"],
            dc_subject=["Python", "RAG"],
            ragd_tags=["important", "reviewed"],
            ragd_project="test-project",
        )
        assert meta.dc_title == "Test Document"
        assert len(meta.dc_creator) == 2
        assert "Python" in meta.dc_subject
        assert meta.ragd_project == "test-project"

    def test_to_dict(self) -> None:
        """Test converting to dictionary."""
        now = datetime.now()
        meta = DocumentMetadata(
            dc_title="Test",
            dc_date=now,
            ragd_ingestion_date=now,
        )
        data = meta.to_dict()
        assert data["dc_title"] == "Test"
        assert data["dc_date"] == now.isoformat()
        assert data["ragd_ingestion_date"] == now.isoformat()

    def test_from_dict(self) -> None:
        """Test creating from dictionary."""
        now = datetime.now()
        data = {
            "dc_title": "Test",
            "dc_creator": ["Author"],
            "dc_date": now.isoformat(),
            "ragd_ingestion_date": now.isoformat(),
        }
        meta = DocumentMetadata.from_dict(data)
        assert meta.dc_title == "Test"
        assert meta.dc_creator == ["Author"]
        assert meta.dc_date == now

    def test_to_json(self) -> None:
        """Test JSON serialisation."""
        meta = DocumentMetadata(dc_title="Test")
        json_str = meta.to_json()
        data = json.loads(json_str)
        assert data["dc_title"] == "Test"

    def test_from_json(self) -> None:
        """Test JSON deserialisation."""
        json_str = '{"dc_title": "Test", "dc_creator": ["Author"]}'
        meta = DocumentMetadata.from_json(json_str)
        assert meta.dc_title == "Test"

    def test_str_representation(self) -> None:
        """Test string representation."""
        meta = DocumentMetadata(
            dc_title="Test Document",
            dc_creator=["Author"],
            ragd_source_path="/path/to/doc.pdf",
        )
        result = str(meta)
        assert "Test Document" in result
        assert "Author" in result
        assert "/path/to/doc.pdf" in result

    def test_str_empty_metadata(self) -> None:
        """Test string representation of empty metadata."""
        meta = DocumentMetadata()
        result = str(meta)
        assert "No metadata" in result


class TestMigration:
    """Tests for metadata migration."""

    def test_get_schema_version_v2(self) -> None:
        """Test getting version from v2 data."""
        data = {"ragd_schema_version": "2.0", "dc_title": "Test"}
        assert get_schema_version(data) == "2.0"

    def test_get_schema_version_v1(self) -> None:
        """Test getting version from v1 data."""
        data = {"source_path": "/path/to/file.pdf", "content_hash": "abc123"}
        assert get_schema_version(data) == "1.0"

    def test_needs_migration_v1(self) -> None:
        """Test migration needed for v1 data."""
        data = {"source_path": "/path/to/file.pdf"}
        assert needs_migration(data) is True

    def test_needs_migration_v2(self) -> None:
        """Test no migration needed for v2 data."""
        data = {"ragd_schema_version": "2.0"}
        assert needs_migration(data) is False

    def test_migrate_v1_to_v2(self) -> None:
        """Test migrating v1 data to v2."""
        v1_data = {
            "source_path": "/docs/report.pdf",
            "content_hash": "abc123def456",
            "chunk_count": 10,
            "indexed_at": "2024-01-15T10:30:00",
            "file_type": "pdf",
        }
        meta = migrate_v1_to_v2(v1_data)

        assert meta.ragd_schema_version == SCHEMA_V2
        assert meta.ragd_source_path == "/docs/report.pdf"
        assert meta.ragd_source_hash == "abc123def456"
        assert meta.ragd_chunk_count == 10
        assert meta.dc_title == "report"  # Derived from filename
        assert meta.dc_format == "application/pdf"

    def test_migrate_v1_with_datetime_object(self) -> None:
        """Test migrating v1 data with datetime object."""
        indexed = datetime(2024, 1, 15, 10, 30)
        v1_data = {
            "source_path": "/docs/doc.txt",
            "content_hash": "hash",
            "indexed_at": indexed,
        }
        meta = migrate_v1_to_v2(v1_data)
        assert meta.ragd_ingestion_date == indexed

    def test_migrate_to_current(self) -> None:
        """Test migrate_to_current dispatches correctly."""
        v1_data = {"source_path": "/test.pdf"}
        meta = migrate_to_current(v1_data)
        assert meta.ragd_schema_version == CURRENT_SCHEMA

        v2_data = {"ragd_schema_version": "2.0", "dc_title": "Test"}
        meta = migrate_to_current(v2_data)
        assert meta.dc_title == "Test"


class TestMetadataStore:
    """Tests for MetadataStore."""

    @pytest.fixture
    def store(self, tmp_path: Path) -> MetadataStore:
        """Create a temporary metadata store."""
        db_path = tmp_path / "metadata.sqlite"
        return MetadataStore(db_path)

    def test_init_creates_db(self, tmp_path: Path) -> None:
        """Test that initialisation creates database."""
        db_path = tmp_path / "subdir" / "metadata.sqlite"
        store = MetadataStore(db_path)
        assert db_path.exists()

    def test_set_and_get(self, store: MetadataStore) -> None:
        """Test setting and getting metadata."""
        meta = DocumentMetadata(dc_title="Test Document")
        store.set("doc-001", meta)

        retrieved = store.get("doc-001")
        assert retrieved is not None
        assert retrieved.dc_title == "Test Document"

    def test_get_nonexistent(self, store: MetadataStore) -> None:
        """Test getting nonexistent document returns None."""
        result = store.get("nonexistent")
        assert result is None

    def test_update_existing(self, store: MetadataStore) -> None:
        """Test updating existing document."""
        meta = DocumentMetadata(dc_title="Original")
        store.set("doc-001", meta)

        meta2 = DocumentMetadata(dc_title="Updated")
        store.set("doc-001", meta2)

        retrieved = store.get("doc-001")
        assert retrieved is not None
        assert retrieved.dc_title == "Updated"

    def test_update_fields(self, store: MetadataStore) -> None:
        """Test updating specific fields."""
        meta = DocumentMetadata(dc_title="Test", ragd_project="proj-a")
        store.set("doc-001", meta)

        result = store.update("doc-001", dc_title="Updated Title")
        assert result is True

        retrieved = store.get("doc-001")
        assert retrieved is not None
        assert retrieved.dc_title == "Updated Title"
        assert retrieved.ragd_project == "proj-a"  # Unchanged

    def test_update_nonexistent(self, store: MetadataStore) -> None:
        """Test updating nonexistent document returns False."""
        result = store.update("nonexistent", dc_title="Test")
        assert result is False

    def test_delete(self, store: MetadataStore) -> None:
        """Test deleting document."""
        meta = DocumentMetadata(dc_title="Test")
        store.set("doc-001", meta)
        assert store.exists("doc-001") is True

        result = store.delete("doc-001")
        assert result is True
        assert store.exists("doc-001") is False

    def test_delete_nonexistent(self, store: MetadataStore) -> None:
        """Test deleting nonexistent document returns False."""
        result = store.delete("nonexistent")
        assert result is False

    def test_exists(self, store: MetadataStore) -> None:
        """Test exists check."""
        assert store.exists("doc-001") is False

        store.set("doc-001", DocumentMetadata())
        assert store.exists("doc-001") is True

    def test_list_ids(self, store: MetadataStore) -> None:
        """Test listing document IDs."""
        store.set("doc-001", DocumentMetadata())
        store.set("doc-002", DocumentMetadata())
        store.set("doc-003", DocumentMetadata())

        ids = store.list_ids()
        assert len(ids) == 3
        assert "doc-001" in ids
        assert "doc-002" in ids
        assert "doc-003" in ids

    def test_count(self, store: MetadataStore) -> None:
        """Test counting documents."""
        assert store.count() == 0

        store.set("doc-001", DocumentMetadata())
        store.set("doc-002", DocumentMetadata())

        assert store.count() == 2

    def test_query_by_project(self, store: MetadataStore) -> None:
        """Test querying by project."""
        store.set("doc-001", DocumentMetadata(ragd_project="proj-a"))
        store.set("doc-002", DocumentMetadata(ragd_project="proj-b"))
        store.set("doc-003", DocumentMetadata(ragd_project="proj-a"))

        results = store.query(project="proj-a")
        assert len(results) == 2
        assert all(meta.ragd_project == "proj-a" for _, meta in results)

    def test_query_by_tags(self, store: MetadataStore) -> None:
        """Test querying by tags."""
        store.set("doc-001", DocumentMetadata(ragd_tags=["important", "reviewed"]))
        store.set("doc-002", DocumentMetadata(ragd_tags=["important"]))
        store.set("doc-003", DocumentMetadata(ragd_tags=["archived"]))

        results = store.query(tags=["important"])
        assert len(results) == 2

        results = store.query(tags=["important", "reviewed"])
        assert len(results) == 1

    def test_query_by_source_path(self, store: MetadataStore) -> None:
        """Test querying by source path substring."""
        store.set("doc-001", DocumentMetadata(ragd_source_path="/docs/reports/q1.pdf"))
        store.set("doc-002", DocumentMetadata(ragd_source_path="/docs/reports/q2.pdf"))
        store.set("doc-003", DocumentMetadata(ragd_source_path="/docs/invoices/inv1.pdf"))

        results = store.query(source_path_contains="reports")
        assert len(results) == 2

    def test_query_by_date_range(self, store: MetadataStore) -> None:
        """Test querying by ingestion date range."""
        store.set(
            "doc-001",
            DocumentMetadata(ragd_ingestion_date=datetime(2024, 1, 15)),
        )
        store.set(
            "doc-002",
            DocumentMetadata(ragd_ingestion_date=datetime(2024, 2, 15)),
        )
        store.set(
            "doc-003",
            DocumentMetadata(ragd_ingestion_date=datetime(2024, 3, 15)),
        )

        results = store.query(since=datetime(2024, 2, 1))
        assert len(results) == 2

        results = store.query(until=datetime(2024, 2, 28))
        assert len(results) == 2

        results = store.query(
            since=datetime(2024, 2, 1),
            until=datetime(2024, 2, 28),
        )
        assert len(results) == 1

    def test_query_with_limit(self, store: MetadataStore) -> None:
        """Test querying with limit."""
        for i in range(10):
            store.set(f"doc-{i:03d}", DocumentMetadata())

        results = store.query(limit=5)
        assert len(results) == 5

    def test_get_raw(self, store: MetadataStore) -> None:
        """Test getting raw metadata."""
        meta = DocumentMetadata(dc_title="Test")
        store.set("doc-001", meta)

        raw = store.get_raw("doc-001")
        assert raw is not None
        assert raw["dc_title"] == "Test"
        assert isinstance(raw, dict)


class TestMetadataStoreMigration:
    """Tests for MetadataStore lazy migration."""

    @pytest.fixture
    def store(self, tmp_path: Path) -> MetadataStore:
        """Create a temporary metadata store."""
        db_path = tmp_path / "metadata.sqlite"
        return MetadataStore(db_path)

    def test_lazy_migration_on_get(self, store: MetadataStore) -> None:
        """Test that get() migrates v1 data."""
        # Insert v1 data directly
        import sqlite3

        conn = sqlite3.connect(store._db_path)
        v1_data = {
            "source_path": "/docs/test.pdf",
            "content_hash": "abc123",
            "chunk_count": 5,
        }
        now = datetime.now().isoformat()
        conn.execute(
            "INSERT INTO documents (id, metadata, created_at, updated_at) VALUES (?, ?, ?, ?)",
            ("doc-001", json.dumps(v1_data), now, now),
        )
        conn.commit()
        conn.close()

        # Get should migrate
        meta = store.get("doc-001")
        assert meta is not None
        assert meta.ragd_schema_version == SCHEMA_V2
        assert meta.ragd_source_path == "/docs/test.pdf"
        assert meta.dc_title == "test"  # Derived

        # Verify migration was persisted
        raw = store.get_raw("doc-001")
        assert raw is not None
        assert raw["ragd_schema_version"] == SCHEMA_V2

    def test_get_migration_stats(self, store: MetadataStore) -> None:
        """Test getting migration statistics."""
        store.set("doc-001", DocumentMetadata())
        store.set("doc-002", DocumentMetadata())

        stats = store.get_migration_stats()
        assert stats.get(SCHEMA_V2, 0) == 2

    def test_migrate_all(self, store: MetadataStore) -> None:
        """Test batch migration."""
        # Insert v1 data directly
        import sqlite3

        conn = sqlite3.connect(store._db_path)
        now = datetime.now().isoformat()
        for i in range(5):
            v1_data = {
                "source_path": f"/docs/doc{i}.pdf",
                "content_hash": f"hash{i}",
            }
            conn.execute(
                "INSERT INTO documents (id, metadata, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (f"doc-{i:03d}", json.dumps(v1_data), now, now),
            )
        conn.commit()
        conn.close()

        # Migrate all
        migrated = store.migrate_all()
        assert migrated == 5

        # Verify all migrated
        stats = store.get_migration_stats()
        assert stats.get(SCHEMA_V2, 0) == 5
        assert stats.get(SCHEMA_V1, 0) == 0
