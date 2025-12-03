"""Tests for ragd.security.deletion module."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ragd.security.deletion import (
    AuditLogError,
    DeletionAuditEntry,
    DeletionAuditLog,
    DeletionLevel,
    DeletionResult,
    Overwriter,
    SecureDeleter,
)


@pytest.fixture
def temp_dir() -> Path:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestDeletionLevel:
    """Tests for DeletionLevel enum."""

    def test_levels_exist(self) -> None:
        """All expected levels exist."""
        assert DeletionLevel.STANDARD.value == "standard"
        assert DeletionLevel.SECURE.value == "secure"
        assert DeletionLevel.CRYPTOGRAPHIC.value == "cryptographic"

    def test_levels_from_string(self) -> None:
        """Can create levels from string values."""
        assert DeletionLevel("standard") == DeletionLevel.STANDARD
        assert DeletionLevel("secure") == DeletionLevel.SECURE
        assert DeletionLevel("cryptographic") == DeletionLevel.CRYPTOGRAPHIC


class TestDeletionResult:
    """Tests for DeletionResult dataclass."""

    def test_default_values(self) -> None:
        """Default values are set correctly."""
        result = DeletionResult(
            document_id="doc-123",
            level=DeletionLevel.STANDARD,
        )

        assert result.document_id == "doc-123"
        assert result.level == DeletionLevel.STANDARD
        assert result.chunks_deleted == 0
        assert result.vectors_deleted == 0
        assert result.key_rotated is False
        assert result.audit_logged is False
        assert result.timestamp is not None

    def test_to_dict(self) -> None:
        """Result serialises to dictionary."""
        result = DeletionResult(
            document_id="doc-123",
            level=DeletionLevel.SECURE,
            chunks_deleted=5,
            vectors_deleted=5,
        )

        data = result.to_dict()
        assert data["document_id"] == "doc-123"
        assert data["level"] == "secure"
        assert data["chunks_deleted"] == 5


class TestDeletionAuditEntry:
    """Tests for DeletionAuditEntry dataclass."""

    def test_create(self) -> None:
        """Can create audit entry."""
        entry = DeletionAuditEntry.create(
            document_id="doc-123",
            level=DeletionLevel.SECURE,
            chunks_removed=10,
            key_rotated=False,
        )

        assert entry.document_id == "doc-123"
        assert entry.action == "secure_delete"
        assert entry.chunks_removed == 10
        assert entry.key_rotated is False
        assert entry.level == DeletionLevel.SECURE
        assert len(entry.document_hash) == 16  # SHA-256 truncated

    def test_create_cryptographic(self) -> None:
        """Cryptographic level sets correct action."""
        entry = DeletionAuditEntry.create(
            document_id="doc-456",
            level=DeletionLevel.CRYPTOGRAPHIC,
            chunks_removed=5,
            key_rotated=True,
        )

        assert entry.action == "cryptographic_erase"
        assert entry.key_rotated is True

    def test_to_dict(self) -> None:
        """Entry serialises to dictionary."""
        entry = DeletionAuditEntry.create(
            document_id="doc-123",
            level=DeletionLevel.STANDARD,
            chunks_removed=3,
            key_rotated=False,
        )

        data = entry.to_dict()
        assert data["document_id"] == "doc-123"
        assert data["action"] == "delete"
        assert data["level"] == "standard"
        assert "timestamp" in data


class TestDeletionAuditLog:
    """Tests for DeletionAuditLog class."""

    def test_write_and_read(self, temp_dir: Path) -> None:
        """Can write and read audit entries."""
        log_path = temp_dir / "deletions.log"
        log = DeletionAuditLog(log_path)

        entry = DeletionAuditEntry.create(
            document_id="doc-123",
            level=DeletionLevel.SECURE,
            chunks_removed=5,
            key_rotated=False,
        )

        log.write(entry)

        entries = log.read_all()
        assert len(entries) == 1
        assert entries[0].document_id == "doc-123"
        assert entries[0].level == DeletionLevel.SECURE

    def test_multiple_entries(self, temp_dir: Path) -> None:
        """Can write multiple entries."""
        log_path = temp_dir / "deletions.log"
        log = DeletionAuditLog(log_path)

        for i in range(3):
            entry = DeletionAuditEntry.create(
                document_id=f"doc-{i}",
                level=DeletionLevel.STANDARD,
                chunks_removed=i,
                key_rotated=False,
            )
            log.write(entry)

        assert log.count() == 3
        entries = log.read_all()
        assert len(entries) == 3

    def test_count_empty_log(self, temp_dir: Path) -> None:
        """Count returns 0 for empty/nonexistent log."""
        log_path = temp_dir / "nonexistent.log"
        log = DeletionAuditLog(log_path)

        assert log.count() == 0
        assert log.read_all() == []

    def test_creates_parent_directories(self, temp_dir: Path) -> None:
        """Creates parent directories if needed."""
        log_path = temp_dir / "audit" / "nested" / "deletions.log"
        log = DeletionAuditLog(log_path)

        entry = DeletionAuditEntry.create(
            document_id="doc-123",
            level=DeletionLevel.STANDARD,
            chunks_removed=1,
            key_rotated=False,
        )
        log.write(entry)

        assert log_path.exists()


class TestOverwriter:
    """Tests for Overwriter class."""

    def test_overwrite_bytes(self) -> None:
        """Overwrites byte array in place."""
        original = bytearray(b"sensitive data here")
        original_copy = bytes(original)

        Overwriter.overwrite_bytes(original)

        # Should be all zeros after overwrite
        assert all(b == 0 for b in original)
        # Should not equal original
        assert bytes(original) != original_copy

    def test_overwrite_string(self) -> None:
        """Overwrites string data."""
        data = bytearray(b"password123")

        Overwriter.overwrite_string(data)

        assert all(b == 0 for b in data)

    def test_secure_delete_file(self, temp_dir: Path) -> None:
        """Securely deletes a file."""
        test_file = temp_dir / "sensitive.txt"
        test_file.write_bytes(b"sensitive content")

        assert test_file.exists()

        result = Overwriter.secure_delete_file(test_file)

        assert result is True
        assert not test_file.exists()

    def test_secure_delete_nonexistent(self, temp_dir: Path) -> None:
        """Returns False for nonexistent file."""
        test_file = temp_dir / "nonexistent.txt"

        result = Overwriter.secure_delete_file(test_file)

        assert result is False


class MockVectorStore:
    """Mock vector store for testing."""

    def __init__(self) -> None:
        self.vectors: dict[str, dict] = {}
        self.persisted = False

    def delete(self, ids: list[str]) -> int:
        deleted = 0
        for id_ in ids:
            if id_ in self.vectors:
                del self.vectors[id_]
                deleted += 1
        return deleted

    def persist(self) -> None:
        self.persisted = True


class MockMetadataStore:
    """Mock metadata store for testing."""

    def __init__(self) -> None:
        self.metadata: dict[str, list] = {}  # doc_id -> [chunk_ids]

    def delete_by_document(self, document_id: str) -> int:
        if document_id in self.metadata:
            count = len(self.metadata[document_id])
            del self.metadata[document_id]
            return count
        return 0


class TestSecureDeleter:
    """Tests for SecureDeleter class."""

    def test_standard_deletion(self, temp_dir: Path) -> None:
        """Standard deletion removes from index."""
        vector_store = MockVectorStore()
        vector_store.vectors = {"chunk-1": {}, "chunk-2": {}}
        metadata_store = MockMetadataStore()
        metadata_store.metadata = {"doc-123": ["chunk-1", "chunk-2"]}

        deleter = SecureDeleter(
            vector_store=vector_store,
            metadata_store=metadata_store,
            enable_audit=False,
        )

        result = deleter.delete(
            "doc-123",
            DeletionLevel.STANDARD,
            chunk_ids=["chunk-1", "chunk-2"],
        )

        assert result.document_id == "doc-123"
        assert result.level == DeletionLevel.STANDARD
        assert result.vectors_deleted == 2
        assert result.chunks_deleted == 2
        assert result.key_rotated is False

    def test_secure_deletion(self, temp_dir: Path) -> None:
        """Secure deletion overwrites and persists."""
        vector_store = MockVectorStore()
        metadata_store = MockMetadataStore()
        metadata_store.metadata = {"doc-123": ["chunk-1"]}

        deleter = SecureDeleter(
            vector_store=vector_store,
            metadata_store=metadata_store,
            enable_audit=False,
        )

        result = deleter.delete("doc-123", DeletionLevel.SECURE)

        assert result.level == DeletionLevel.SECURE
        assert vector_store.persisted is True

    def test_cryptographic_requires_password(self) -> None:
        """Cryptographic level requires password."""
        deleter = SecureDeleter(enable_audit=False)

        with pytest.raises(ValueError, match="Password required"):
            deleter.delete("doc-123", DeletionLevel.CRYPTOGRAPHIC)

    def test_with_audit_log(self, temp_dir: Path) -> None:
        """Deletion writes to audit log."""
        log_path = temp_dir / "audit.log"
        metadata_store = MockMetadataStore()
        metadata_store.metadata = {"doc-123": ["chunk-1", "chunk-2", "chunk-3"]}

        deleter = SecureDeleter(
            metadata_store=metadata_store,
            audit_log_path=log_path,
            enable_audit=True,
        )

        result = deleter.delete("doc-123", DeletionLevel.STANDARD)

        assert result.audit_logged is True
        assert log_path.exists()

        # Verify audit content
        entries = deleter.get_audit_log()
        assert entries is not None
        assert len(entries) == 1
        assert entries[0].document_id == "doc-123"
        assert entries[0].chunks_removed == 3

    def test_audit_disabled(self) -> None:
        """Can disable audit logging."""
        deleter = SecureDeleter(enable_audit=False)

        result = deleter.delete("doc-123", DeletionLevel.STANDARD)

        assert result.audit_logged is False
        assert deleter.get_audit_log() is None
        assert deleter.get_audit_count() == 0

    def test_bulk_delete(self, temp_dir: Path) -> None:
        """Bulk deletion processes multiple documents."""
        metadata_store = MockMetadataStore()
        metadata_store.metadata = {
            "doc-1": ["c1"],
            "doc-2": ["c2", "c3"],
            "doc-3": ["c4"],
        }

        deleter = SecureDeleter(
            metadata_store=metadata_store,
            enable_audit=False,
        )

        results = deleter.bulk_delete(
            ["doc-1", "doc-2", "doc-3"],
            DeletionLevel.STANDARD,
        )

        assert len(results) == 3
        assert results[0].document_id == "doc-1"
        assert results[1].document_id == "doc-2"
        assert results[2].document_id == "doc-3"

    def test_progress_callback(self) -> None:
        """Progress callback is invoked."""
        deleter = SecureDeleter(enable_audit=False)
        progress_calls = []

        def callback(msg: str) -> None:
            progress_calls.append(msg)

        deleter.delete("doc-123", DeletionLevel.STANDARD, progress_callback=callback)

        assert len(progress_calls) > 0
        assert any("complete" in msg.lower() for msg in progress_calls)
