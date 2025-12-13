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
from ragd.security.keystore import (
    KeyMetadata,
    KeyStore,
    KeyStoreError,
    MemoryProtectionError,
    VerificationStore,
)
from ragd.security.secrets import (
    SecretsFilter,
    SecretString,
    get_all_secrets,
    is_secret_env_var,
    load_secret,
    mask_secrets_in_string,
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
from ragd.security.tiers import (
    DataTier,
    TierAccessError,
    TierConfig,
    TierManager,
    get_tier_colour,
    get_tier_icon,
)
from ragd.security.validation import (
    ValidationError,
    sanitise_search_query,
    validate_document_id,
    validate_file_size,
    validate_limit,
    validate_path,
    validate_tag_name,
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
    # Tiers
    "DataTier",
    "TierAccessError",
    "TierConfig",
    "TierManager",
    "get_tier_colour",
    "get_tier_icon",
    # Validation (F-082)
    "ValidationError",
    "validate_document_id",
    "validate_file_size",
    "validate_limit",
    "validate_path",
    "validate_tag_name",
    "sanitise_search_query",
    # Secrets (F-083)
    "SecretString",
    "SecretsFilter",
    "get_all_secrets",
    "is_secret_env_var",
    "load_secret",
    "mask_secrets_in_string",
]
