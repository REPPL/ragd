"""Security module for ragd.

This module provides encryption, session management, and secure deletion
capabilities for protecting sensitive data at rest.

Features:
    - Database encryption using SQLCipher (AES-256-GCM)
    - Key derivation using Argon2id
    - Session management with auto-lock
    - Secure deletion with multiple levels

Usage:
    from ragd.security import (
        derive_key,
        KeyStore,
        EncryptedMetadataStore,
    )

    # Derive encryption key from password
    key = derive_key(password, salt)

    # Create encrypted store
    store = EncryptedMetadataStore(path, key)
"""

from ragd.security.crypto import (
    CryptoConfig,
    derive_key,
    derive_key_with_verification,
    generate_salt,
    verify_key,
)
from ragd.security.keystore import (
    KeyMetadata,
    KeyStore,
    KeyStoreError,
    MemoryProtectionError,
    VerificationStore,
)
from ragd.security.encrypted_store import (
    DatabaseLockedError,
    EncryptedConnection,
    EncryptedConnectionError,
    EncryptedMetadataStore,
    EncryptionError,
    encrypted_connection,
    is_database_encrypted,
    is_sqlcipher_available,
    migrate_to_encrypted,
)
from ragd.security.session import (
    AuthenticationError,
    LockoutError,
    SessionConfig,
    SessionError,
    SessionLockError,
    SessionManager,
    SessionMetadata,
    SessionState,
)
from ragd.security.deletion import (
    AuditLogError,
    DeletionAuditEntry,
    DeletionAuditLog,
    DeletionError,
    DeletionLevel,
    DeletionResult,
    Overwriter,
    SecureDeleter,
)

__all__ = [
    # Crypto
    "CryptoConfig",
    "derive_key",
    "derive_key_with_verification",
    "generate_salt",
    "verify_key",
    # KeyStore
    "KeyMetadata",
    "KeyStore",
    "KeyStoreError",
    "MemoryProtectionError",
    "VerificationStore",
    # Encrypted Store
    "DatabaseLockedError",
    "EncryptedConnection",
    "EncryptedConnectionError",
    "EncryptedMetadataStore",
    "EncryptionError",
    "encrypted_connection",
    "is_database_encrypted",
    "is_sqlcipher_available",
    "migrate_to_encrypted",
    # Session
    "AuthenticationError",
    "LockoutError",
    "SessionConfig",
    "SessionError",
    "SessionLockError",
    "SessionManager",
    "SessionMetadata",
    "SessionState",
    # Deletion
    "AuditLogError",
    "DeletionAuditEntry",
    "DeletionAuditLog",
    "DeletionError",
    "DeletionLevel",
    "DeletionResult",
    "Overwriter",
    "SecureDeleter",
]
