"""Tests for ragd.security.keystore module."""

import pytest

from ragd.security.keystore import (
    KeyMetadata,
    KeyStore,
    KeyStoreError,
    VerificationStore,
)


class TestKeyStore:
    """Tests for KeyStore class."""

    def test_initial_state_empty(self) -> None:
        """KeyStore starts with no key."""
        store = KeyStore()
        assert not store.has_key()

    def test_store_key(self) -> None:
        """Can store a key."""
        store = KeyStore()
        key = b"test_key_32_bytes_for_encryption"
        store.store_key(key)
        assert store.has_key()

    def test_get_key(self) -> None:
        """Can retrieve stored key."""
        store = KeyStore()
        key = b"test_key_32_bytes_for_encryption"
        store.store_key(key)
        retrieved = store.get_key()
        assert retrieved == key

    def test_get_key_returns_copy(self) -> None:
        """Get key returns a copy, not the original."""
        store = KeyStore()
        key = b"test_key_32_bytes_for_encryption"
        store.store_key(key)
        retrieved1 = store.get_key()
        retrieved2 = store.get_key()
        # Both should equal the original
        assert retrieved1 == key
        assert retrieved2 == key
        # But be independent copies (modifying one doesn't affect others)
        # Note: bytes are immutable so this is implicit

    def test_get_key_without_store_raises(self) -> None:
        """Get key without storing raises error."""
        store = KeyStore()
        with pytest.raises(KeyStoreError, match="No key stored"):
            store.get_key()

    def test_store_empty_key_raises(self) -> None:
        """Storing empty key raises error."""
        store = KeyStore()
        with pytest.raises(ValueError, match="empty key"):
            store.store_key(b"")

    def test_store_key_clears_previous(self) -> None:
        """Storing new key clears the previous one."""
        store = KeyStore()
        key1 = b"first_key_32_bytes_xxxxxxxxxx"
        key2 = b"second_key_32_bytes_xxxxxxxxx"
        store.store_key(key1)
        store.store_key(key2)
        assert store.get_key() == key2

    def test_clear_removes_key(self) -> None:
        """Clear removes the stored key."""
        store = KeyStore()
        store.store_key(b"test_key_32_bytes_for_encryption")
        store.clear()
        assert not store.has_key()

    def test_clear_without_key_is_safe(self) -> None:
        """Clear without key doesn't raise."""
        store = KeyStore()
        store.clear()  # Should not raise

    def test_rotate_key(self) -> None:
        """Rotate replaces key with new one."""
        store = KeyStore()
        old_key = b"old_key_32_bytes_for_encryption"
        new_key = b"new_key_32_bytes_for_encryption"
        store.store_key(old_key)
        store.rotate(new_key)
        assert store.get_key() == new_key

    def test_context_manager_clears_on_exit(self) -> None:
        """Context manager clears key on exit."""
        key = b"test_key_32_bytes_for_encryption"
        with KeyStore() as store:
            store.store_key(key)
            assert store.has_key()
        assert not store.has_key()

    def test_context_manager_clears_on_exception(self) -> None:
        """Context manager clears key even on exception."""
        store = KeyStore()
        with pytest.raises(RuntimeError):
            with store:
                store.store_key(b"test_key_32_bytes_for_encryption")
                raise RuntimeError("Test error")
        assert not store.has_key()


class TestKeyMetadata:
    """Tests for KeyMetadata dataclass."""

    def test_metadata_returned_on_store(self) -> None:
        """Store key returns metadata."""
        store = KeyStore()
        metadata = store.store_key(b"test_key_32_bytes_for_encryption")
        assert isinstance(metadata, KeyMetadata)

    def test_metadata_has_created_at(self) -> None:
        """Metadata includes creation time."""
        store = KeyStore()
        metadata = store.store_key(b"test_key_32_bytes_for_encryption")
        assert metadata.created_at is not None

    def test_metadata_access_count_increments(self) -> None:
        """Access count increments on each get."""
        store = KeyStore()
        store.store_key(b"test_key_32_bytes_for_encryption")
        assert store.get_metadata().access_count == 0
        store.get_key()
        assert store.get_metadata().access_count == 1
        store.get_key()
        assert store.get_metadata().access_count == 2

    def test_metadata_last_accessed_updates(self) -> None:
        """Last accessed time updates on get."""
        store = KeyStore()
        store.store_key(b"test_key_32_bytes_for_encryption")
        initial_accessed = store.get_metadata().last_accessed
        store.get_key()
        # Should be same or later
        assert store.get_metadata().last_accessed >= initial_accessed

    def test_get_metadata_without_key(self) -> None:
        """Get metadata returns None without key."""
        store = KeyStore()
        assert store.get_metadata() is None


class TestVerificationStore:
    """Tests for VerificationStore class."""

    def test_init(self) -> None:
        """Can create verification store."""
        salt = b"test_salt_16_byt"
        hash_val = b"test_hash_32_bytes_xxxxxxxxxx"
        store = VerificationStore(salt, hash_val)
        assert store.salt == salt
        assert store.verification_hash == hash_val

    def test_verify_correct_key(self) -> None:
        """Verify returns True for correct key."""
        import hashlib

        key = b"correct_key_32_bytes_for_test!"
        verification_hash = hashlib.sha256(key).digest()
        store = VerificationStore(b"any_salt_16_byte", verification_hash)
        assert store.verify(key)

    def test_verify_wrong_key(self) -> None:
        """Verify returns False for wrong key."""
        import hashlib

        key = b"correct_key_32_bytes_for_test!"
        verification_hash = hashlib.sha256(key).digest()
        store = VerificationStore(b"any_salt_16_byte", verification_hash)
        assert not store.verify(b"wrong_key_32_bytes_xxxxxxxxxxx")

    def test_to_dict(self) -> None:
        """To dict serialises correctly."""
        salt = b"test_salt_16_byt"
        hash_val = b"test_hash_32_bytes_xxxxxxxxxx"
        store = VerificationStore(salt, hash_val)
        data = store.to_dict()
        assert data["salt"] == salt.hex()
        assert data["verification_hash"] == hash_val.hex()

    def test_from_dict(self) -> None:
        """From dict deserialises correctly."""
        salt = b"test_salt_16_byt"
        hash_val = b"test_hash_32_bytes_xxxxxxxxxx"
        data = {"salt": salt.hex(), "verification_hash": hash_val.hex()}
        store = VerificationStore.from_dict(data)
        assert store.salt == salt
        assert store.verification_hash == hash_val

    def test_roundtrip(self) -> None:
        """To dict and from dict roundtrip."""
        original = VerificationStore(
            b"original_salt_16", b"original_hash_32_bytes_xxxxx"
        )
        data = original.to_dict()
        restored = VerificationStore.from_dict(data)
        assert restored.salt == original.salt
        assert restored.verification_hash == original.verification_hash


class TestMemoryProtection:
    """Tests for memory protection features."""

    def test_is_protected_reports_status(self) -> None:
        """Is protected reports protection status."""
        store = KeyStore()
        store.store_key(b"test_key_32_bytes_for_encryption")
        # May or may not be protected depending on platform
        # Just verify it returns a boolean
        assert isinstance(store.is_protected(), bool)

    def test_metadata_has_protection_status(self) -> None:
        """Metadata includes protection status."""
        store = KeyStore()
        metadata = store.store_key(b"test_key_32_bytes_for_encryption")
        assert isinstance(metadata.is_protected, bool)
