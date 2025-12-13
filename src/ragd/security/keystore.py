"""Key storage and memory protection for ragd.

This module provides secure key storage with memory protection features:
- Keys stored in memory with mlock() to prevent swapping
- Secure zeroing of key material when no longer needed
- Reference counting for safe key lifecycle management

Security Considerations:
    - Keys should never be written to disk unencrypted
    - Memory should be locked to prevent swapping (mlock)
    - Key material must be zeroed before deallocation
    - Keys should have a limited lifetime in memory
"""

from __future__ import annotations

import ctypes
import gc
import platform
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class KeyStoreError(Exception):
    """Base exception for key store operations."""

    pass


class MemoryProtectionError(KeyStoreError):
    """Exception raised when memory protection fails."""

    pass


@dataclass
class KeyMetadata:
    """Metadata about a stored key.

    Attributes:
        created_at: When the key was created/loaded.
        last_accessed: When the key was last used.
        access_count: Number of times the key has been accessed.
        is_protected: Whether memory protection (mlock) succeeded.
    """

    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(UTC))
    access_count: int = 0
    is_protected: bool = False


class KeyStore:
    """Secure in-memory key storage.

    Provides secure storage for encryption keys with memory protection
    and automatic zeroing on cleanup.

    Usage:
        store = KeyStore()
        store.store_key(key_bytes)

        # Use the key
        key = store.get_key()

        # Clear when done
        store.clear()

    Security Features:
        - mlock() to prevent key from being swapped to disk
        - Secure zeroing using ctypes.memset
        - Automatic clearing on garbage collection
    """

    def __init__(self) -> None:
        """Initialise the key store."""
        self._key: bytearray | None = None
        self._metadata: KeyMetadata | None = None
        self._libc = self._get_libc()

    def _get_libc(self) -> ctypes.CDLL | None:
        """Get the C library for memory protection.

        Returns:
            C library handle, or None if unavailable.
        """
        system = platform.system()
        try:
            if system == "Darwin":
                return ctypes.CDLL("libc.dylib")
            elif system == "Linux":
                return ctypes.CDLL("libc.so.6")
            # Windows doesn't support mlock the same way
            return None
        except OSError:
            return None

    def _mlock(self, data: bytearray) -> bool:
        """Lock memory to prevent swapping.

        Args:
            data: Data to lock in memory.

        Returns:
            True if locking succeeded, False otherwise.
        """
        if self._libc is None:
            return False

        try:
            # Get pointer to the data
            ptr = (ctypes.c_char * len(data)).from_buffer(data)
            result = self._libc.mlock(ctypes.addressof(ptr), len(data))
            return result == 0
        except Exception:
            return False

    def _munlock(self, data: bytearray) -> bool:
        """Unlock memory.

        Args:
            data: Data to unlock.

        Returns:
            True if unlocking succeeded.
        """
        if self._libc is None:
            return False

        try:
            ptr = (ctypes.c_char * len(data)).from_buffer(data)
            result = self._libc.munlock(ctypes.addressof(ptr), len(data))
            return result == 0
        except Exception:
            return False

    def _secure_zero(self, data: bytearray) -> None:
        """Securely zero memory.

        Uses ctypes.memset to ensure the compiler doesn't optimise
        away the zeroing operation.

        Args:
            data: Data to zero.
        """
        if not data:
            return

        try:
            ptr = (ctypes.c_char * len(data)).from_buffer(data)
            ctypes.memset(ctypes.addressof(ptr), 0, len(data))
        except Exception:
            # Fallback: manual zeroing
            for i in range(len(data)):
                data[i] = 0

    def store_key(self, key: bytes) -> KeyMetadata:
        """Store a key securely in memory.

        Any existing key is cleared before storing the new one.

        Args:
            key: Key bytes to store.

        Returns:
            Metadata about the stored key.

        Raises:
            ValueError: If key is empty.
        """
        if not key:
            raise ValueError("Cannot store empty key")

        # Clear any existing key
        self.clear()

        # Store as bytearray (mutable for zeroing)
        self._key = bytearray(key)

        # Attempt to lock memory
        is_protected = self._mlock(self._key)

        self._metadata = KeyMetadata(is_protected=is_protected)

        return self._metadata

    def get_key(self) -> bytes:
        """Retrieve the stored key.

        Returns:
            Copy of the stored key.

        Raises:
            KeyStoreError: If no key is stored.
        """
        if self._key is None:
            raise KeyStoreError("No key stored")

        if self._metadata:
            self._metadata.last_accessed = datetime.now(UTC)
            self._metadata.access_count += 1

        # Return a copy to prevent external modification
        return bytes(self._key)

    def has_key(self) -> bool:
        """Check if a key is stored.

        Returns:
            True if a key is currently stored.
        """
        return self._key is not None

    def get_metadata(self) -> KeyMetadata | None:
        """Get metadata about the stored key.

        Returns:
            Key metadata, or None if no key is stored.
        """
        return self._metadata

    def is_protected(self) -> bool:
        """Check if the key is protected (mlock'd).

        Returns:
            True if memory protection is active.
        """
        return self._metadata is not None and self._metadata.is_protected

    def clear(self) -> None:
        """Clear the stored key securely.

        Zeros the key memory and unlocks it from memory.
        """
        if self._key is not None:
            # Unlock memory first
            self._munlock(self._key)

            # Securely zero the key
            self._secure_zero(self._key)

            # Clear references
            self._key = None

        self._metadata = None

        # Force garbage collection to ensure memory is freed
        gc.collect()

    def rotate(self, new_key: bytes) -> KeyMetadata:
        """Rotate to a new key.

        Atomically replaces the current key with a new one,
        ensuring the old key is securely cleared.

        Args:
            new_key: New key to store.

        Returns:
            Metadata for the new key.
        """
        # Store new key (this clears the old one)
        return self.store_key(new_key)

    def __del__(self) -> None:
        """Clean up on garbage collection."""
        self.clear()

    def __enter__(self) -> KeyStore:
        """Context manager entry."""
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit - clear the key."""
        self.clear()


class VerificationStore:
    """Store for password verification data.

    Stores the salt and verification hash needed to verify passwords
    without storing the actual encryption key.

    The verification hash is derived from the key, allowing password
    verification without the key being present in memory.
    """

    def __init__(self, salt: bytes, verification_hash: bytes) -> None:
        """Initialise verification store.

        Args:
            salt: Salt used for key derivation.
            verification_hash: Hash for password verification.
        """
        self._salt = salt
        self._verification_hash = verification_hash

    @property
    def salt(self) -> bytes:
        """Get the salt."""
        return self._salt

    @property
    def verification_hash(self) -> bytes:
        """Get the verification hash."""
        return self._verification_hash

    def verify(self, key: bytes) -> bool:
        """Verify a key against the stored hash.

        Args:
            key: Key to verify.

        Returns:
            True if the key matches.
        """
        import hashlib

        computed = hashlib.sha256(key).digest()
        return secrets.compare_digest(computed, self._verification_hash)

    def to_dict(self) -> dict[str, str]:
        """Serialise to dictionary.

        Returns:
            Dictionary with hex-encoded values.
        """
        return {
            "salt": self._salt.hex(),
            "verification_hash": self._verification_hash.hex(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> VerificationStore:
        """Create from dictionary.

        Args:
            data: Dictionary with hex-encoded values.

        Returns:
            VerificationStore instance.
        """
        return cls(
            salt=bytes.fromhex(data["salt"]),
            verification_hash=bytes.fromhex(data["verification_hash"]),
        )
