"""Tests for ragd.security.encrypted_store module."""

import tempfile
from pathlib import Path

import pytest

from ragd.security.crypto import derive_key, generate_salt, CryptoConfig
from ragd.security.encrypted_store import (
    is_database_encrypted,
    is_sqlcipher_available,
)

# Skip all tests if SQLCipher is not available
pytestmark = pytest.mark.skipif(
    not is_sqlcipher_available(),
    reason="SQLCipher not available (requires system installation)",
)


@pytest.fixture
def temp_dir() -> Path:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def encryption_key() -> bytes:
    """Generate a test encryption key."""
    salt = generate_salt()
    config = CryptoConfig(memory_kb=8192, iterations=1, parallelism=1)
    return derive_key("test_password", salt, config)


class TestIsSqlcipherAvailable:
    """Tests for is_sqlcipher_available function."""

    def test_returns_boolean(self) -> None:
        """Function returns a boolean."""
        result = is_sqlcipher_available()
        assert isinstance(result, bool)

    def test_returns_true_when_available(self) -> None:
        """Returns True when SQLCipher is available (if test runs)."""
        # If this test runs, SQLCipher must be available
        assert is_sqlcipher_available()


class TestIsDatabaseEncrypted:
    """Tests for is_database_encrypted function."""

    def test_nonexistent_file_returns_false(self, temp_dir: Path) -> None:
        """Nonexistent file returns False."""
        db_path = temp_dir / "nonexistent.db"
        assert not is_database_encrypted(db_path)

    def test_unencrypted_database_returns_false(self, temp_dir: Path) -> None:
        """Unencrypted SQLite database returns False."""
        import sqlite3

        db_path = temp_dir / "unencrypted.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.close()

        assert not is_database_encrypted(db_path)


class TestEncryptedConnection:
    """Tests for EncryptedConnection class."""

    def test_can_create_encrypted_database(
        self, temp_dir: Path, encryption_key: bytes
    ) -> None:
        """Can create a new encrypted database."""
        from ragd.security.encrypted_store import EncryptedConnection

        db_path = temp_dir / "encrypted.db"

        with EncryptedConnection(db_path, encryption_key) as conn:
            conn.execute("CREATE TABLE test (id INTEGER, data TEXT)")
            conn.execute("INSERT INTO test VALUES (1, 'hello')")
            conn.commit()

        # File should exist
        assert db_path.exists()

    def test_can_read_encrypted_database(
        self, temp_dir: Path, encryption_key: bytes
    ) -> None:
        """Can read from encrypted database with correct key."""
        from ragd.security.encrypted_store import EncryptedConnection

        db_path = temp_dir / "encrypted.db"

        # Create database
        with EncryptedConnection(db_path, encryption_key) as conn:
            conn.execute("CREATE TABLE test (id INTEGER, data TEXT)")
            conn.execute("INSERT INTO test VALUES (1, 'hello')")
            conn.commit()

        # Read back
        with EncryptedConnection(db_path, encryption_key) as conn:
            cursor = conn.execute("SELECT * FROM test")
            row = cursor.fetchone()
            assert row[0] == 1
            assert row[1] == "hello"

    def test_wrong_key_fails(
        self, temp_dir: Path, encryption_key: bytes
    ) -> None:
        """Wrong key fails to open database."""
        from ragd.security.encrypted_store import (
            DatabaseLockedError,
            EncryptedConnection,
        )

        db_path = temp_dir / "encrypted.db"

        # Create database
        with EncryptedConnection(db_path, encryption_key) as conn:
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.commit()

        # Try with wrong key
        wrong_key = b"wrong_key_32_bytes_for_testing!"
        with pytest.raises(DatabaseLockedError):
            with EncryptedConnection(db_path, wrong_key):
                pass

    def test_encrypted_database_detected(
        self, temp_dir: Path, encryption_key: bytes
    ) -> None:
        """Encrypted database is detected as encrypted."""
        from ragd.security.encrypted_store import EncryptedConnection

        db_path = temp_dir / "encrypted.db"

        with EncryptedConnection(db_path, encryption_key) as conn:
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.commit()

        assert is_database_encrypted(db_path)


class TestEncryptedMetadataStore:
    """Tests for EncryptedMetadataStore class."""

    def test_can_create_store(
        self, temp_dir: Path, encryption_key: bytes
    ) -> None:
        """Can create an encrypted metadata store."""
        from ragd.security.encrypted_store import EncryptedMetadataStore

        db_path = temp_dir / "metadata.db"
        store = EncryptedMetadataStore(db_path, encryption_key)
        assert store.count() == 0

    def test_add_and_get(
        self, temp_dir: Path, encryption_key: bytes
    ) -> None:
        """Can add and retrieve metadata."""
        from ragd.security.encrypted_store import EncryptedMetadataStore

        db_path = temp_dir / "metadata.db"
        store = EncryptedMetadataStore(db_path, encryption_key)

        store.add(
            vector_id=1,
            chunk_id="chunk_001",
            document_id="doc_001",
            content="Test content",
            metadata={"source": "test.txt"},
        )

        result = store.get("chunk_001")
        assert result is not None
        assert result["vector_id"] == 1
        assert result["document_id"] == "doc_001"
        assert result["content"] == "Test content"
        assert result["metadata"]["source"] == "test.txt"

    def test_count(
        self, temp_dir: Path, encryption_key: bytes
    ) -> None:
        """Count returns correct number."""
        from ragd.security.encrypted_store import EncryptedMetadataStore

        db_path = temp_dir / "metadata.db"
        store = EncryptedMetadataStore(db_path, encryption_key)

        assert store.count() == 0

        store.add(1, "c1", "d1", "content1", {})
        assert store.count() == 1

        store.add(2, "c2", "d1", "content2", {})
        assert store.count() == 2

    def test_delete(
        self, temp_dir: Path, encryption_key: bytes
    ) -> None:
        """Can delete entries."""
        from ragd.security.encrypted_store import EncryptedMetadataStore

        db_path = temp_dir / "metadata.db"
        store = EncryptedMetadataStore(db_path, encryption_key)

        store.add(1, "c1", "d1", "content1", {})
        store.add(2, "c2", "d1", "content2", {})

        deleted = store.delete(["c1"])
        assert deleted == 1
        assert store.count() == 1
        assert store.get("c1") is None
        assert store.get("c2") is not None

    def test_filter(
        self, temp_dir: Path, encryption_key: bytes
    ) -> None:
        """Can filter by metadata."""
        from ragd.security.encrypted_store import EncryptedMetadataStore

        db_path = temp_dir / "metadata.db"
        store = EncryptedMetadataStore(db_path, encryption_key)

        store.add(1, "c1", "doc1", "content1", {"type": "text"})
        store.add(2, "c2", "doc2", "content2", {"type": "code"})
        store.add(3, "c3", "doc1", "content3", {"type": "text"})

        # Filter by document_id
        results = store.filter({"document_id": "doc1"})
        assert len(results) == 2
        assert 1 in results
        assert 3 in results


class TestMigration:
    """Tests for migration functionality."""

    def test_migrate_to_encrypted(
        self, temp_dir: Path, encryption_key: bytes
    ) -> None:
        """Can migrate unencrypted database to encrypted."""
        import sqlite3

        from ragd.security.encrypted_store import (
            EncryptedConnection,
            migrate_to_encrypted,
        )

        # Create unencrypted source
        source_path = temp_dir / "source.db"
        conn = sqlite3.connect(str(source_path))
        conn.execute("CREATE TABLE test (id INTEGER, data TEXT)")
        conn.execute("INSERT INTO test VALUES (1, 'hello')")
        conn.execute("INSERT INTO test VALUES (2, 'world')")
        conn.commit()
        conn.close()

        # Migrate
        dest_path = temp_dir / "encrypted.db"
        migrate_to_encrypted(source_path, dest_path, encryption_key)

        # Verify
        with EncryptedConnection(dest_path, encryption_key) as conn:
            cursor = conn.execute("SELECT * FROM test ORDER BY id")
            rows = cursor.fetchall()
            assert len(rows) == 2
            assert rows[0][1] == "hello"
            assert rows[1][1] == "world"

    def test_migrate_preserves_indices(
        self, temp_dir: Path, encryption_key: bytes
    ) -> None:
        """Migration preserves indices."""
        import sqlite3

        from ragd.security.encrypted_store import (
            EncryptedConnection,
            migrate_to_encrypted,
        )

        # Create source with index
        source_path = temp_dir / "source.db"
        conn = sqlite3.connect(str(source_path))
        conn.execute("CREATE TABLE test (id INTEGER, data TEXT)")
        conn.execute("CREATE INDEX idx_data ON test(data)")
        conn.commit()
        conn.close()

        # Migrate
        dest_path = temp_dir / "encrypted.db"
        migrate_to_encrypted(source_path, dest_path, encryption_key)

        # Verify index exists
        with EncryptedConnection(dest_path, encryption_key) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_data'"
            )
            row = cursor.fetchone()
            assert row is not None
