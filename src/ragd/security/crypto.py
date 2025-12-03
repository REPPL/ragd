"""Cryptographic utilities for ragd.

This module provides key derivation using Argon2id (winner of the 2015
Password Hashing Competition) and related cryptographic operations.

Key Derivation Parameters (OWASP recommended):
    - Memory: 64 MB (65536 KB)
    - Iterations: 3
    - Parallelism: 4 threads
    - Output: 256 bits (32 bytes)

These parameters balance security against brute-force attacks with
reasonable performance on modern hardware.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Constants for key derivation
DEFAULT_MEMORY_KB = 65536  # 64 MB
DEFAULT_ITERATIONS = 3
DEFAULT_PARALLELISM = 4
DEFAULT_KEY_LENGTH = 32  # 256 bits
SALT_LENGTH = 16  # 128 bits


@dataclass(frozen=True)
class CryptoConfig:
    """Configuration for cryptographic operations.

    Attributes:
        memory_kb: Memory cost in KB (default 64 MB)
        iterations: Time cost (default 3)
        parallelism: Number of parallel threads (default 4)
        key_length: Output key length in bytes (default 32)
    """

    memory_kb: int = DEFAULT_MEMORY_KB
    iterations: int = DEFAULT_ITERATIONS
    parallelism: int = DEFAULT_PARALLELISM
    key_length: int = DEFAULT_KEY_LENGTH

    def validate(self) -> None:
        """Validate configuration parameters.

        Raises:
            ValueError: If parameters are out of acceptable range.
        """
        if self.memory_kb < 8192:  # Minimum 8 MB
            raise ValueError("Memory cost must be at least 8192 KB (8 MB)")
        if self.iterations < 1:
            raise ValueError("Iterations must be at least 1")
        if self.parallelism < 1:
            raise ValueError("Parallelism must be at least 1")
        if self.key_length < 16:
            raise ValueError("Key length must be at least 16 bytes")


def generate_salt(length: int = SALT_LENGTH) -> bytes:
    """Generate a cryptographically secure random salt.

    Args:
        length: Salt length in bytes (default 16).

    Returns:
        Random bytes suitable for use as a salt.
    """
    return secrets.token_bytes(length)


def derive_key(
    password: str,
    salt: bytes,
    config: CryptoConfig | None = None,
) -> bytes:
    """Derive an encryption key from a password using Argon2id.

    Argon2id is a hybrid algorithm combining Argon2i (resistance to
    side-channel attacks) and Argon2d (resistance to GPU cracking).

    Args:
        password: User-provided password.
        salt: Random salt (use generate_salt()).
        config: Optional custom configuration.

    Returns:
        Derived key bytes.

    Raises:
        ImportError: If argon2-cffi is not installed.
        ValueError: If password is empty or config is invalid.
    """
    if not password:
        raise ValueError("Password cannot be empty")

    if len(salt) < 8:
        raise ValueError("Salt must be at least 8 bytes")

    config = config or CryptoConfig()
    config.validate()

    try:
        from argon2.low_level import Type, hash_secret_raw
    except ImportError as e:
        raise ImportError(
            "argon2-cffi is required for encryption. "
            "Install with: pip install ragd[encryption]"
        ) from e

    # Derive key using Argon2id
    key = hash_secret_raw(
        secret=password.encode("utf-8"),
        salt=salt,
        time_cost=config.iterations,
        memory_cost=config.memory_kb,
        parallelism=config.parallelism,
        hash_len=config.key_length,
        type=Type.ID,  # Argon2id
    )

    return key


def verify_key(
    password: str,
    salt: bytes,
    expected_key: bytes,
    config: CryptoConfig | None = None,
) -> bool:
    """Verify a password against an expected key.

    Uses constant-time comparison to prevent timing attacks.

    Args:
        password: Password to verify.
        salt: Salt used for key derivation.
        expected_key: Expected key to compare against.
        config: Optional custom configuration.

    Returns:
        True if password produces the expected key.
    """
    try:
        derived = derive_key(password, salt, config)
        # Constant-time comparison
        return secrets.compare_digest(derived, expected_key)
    except (ValueError, ImportError):
        return False


def derive_key_with_verification(
    password: str,
    salt: bytes,
    config: CryptoConfig | None = None,
) -> tuple[bytes, bytes]:
    """Derive a key and create a verification hash.

    The verification hash is a secondary hash that can be stored to
    verify passwords without storing the actual encryption key.

    Args:
        password: User-provided password.
        salt: Random salt.
        config: Optional custom configuration.

    Returns:
        Tuple of (encryption_key, verification_hash).
    """
    # Derive the main encryption key
    key = derive_key(password, salt, config)

    # Create a verification hash from the key
    # This is derived from the key, not the password directly
    import hashlib

    verification = hashlib.sha256(key).digest()

    return key, verification
