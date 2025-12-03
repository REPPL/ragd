# ADR-0022: Personal Vault Isolation

## Status

Accepted

## Context

ragd v2.0 introduces a Personal Information Vault for storing highly sensitive user data (browser history, communications, health records, financial data). This data requires stricter security than the Document Library.

Key questions:
1. Should the Vault share storage with the Document Library?
2. Should encryption keys be shared or separate?
3. How should cross-store queries work?
4. What audit requirements apply?

### Threat Model

| Threat | Mitigation Strategy |
|--------|---------------------|
| Compromised Document Library key | Separate Vault key prevents cascade |
| Forensic analysis | Separate encryption domains |
| Accidental data leakage | Strict store boundaries |
| Compliance (GDPR, HIPAA) | Audit logging, data isolation |

### Options Considered

**Option A: Shared Storage, Single Key**
- Pros: Simpler architecture, unified search
- Cons: Key compromise affects all data, no audit separation

**Option B: Separate Storage, Separate Keys**
- Pros: Defence in depth, compliance-friendly, clear boundaries
- Cons: More complex, duplicate infrastructure

**Option C: Shared Storage, Separate Keys per Data Type**
- Pros: Granular access control
- Cons: Key management complexity, confusing boundaries

## Decision

Use **Option B: Separate Storage with Separate Encryption Keys**.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ragd Storage Architecture                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────┐    ┌─────────────────────────────┐ │
│  │    DOCUMENT LIBRARY     │    │    PERSONAL VAULT           │ │
│  │    ~/.ragd/library/     │    │    ~/.ragd/vault/           │ │
│  ├─────────────────────────┤    ├─────────────────────────────┤ │
│  │                         │    │                             │ │
│  │  ChromaDB: library.db   │    │  ChromaDB: vault.db         │ │
│  │  SQLite: metadata.db    │    │  SQLite: vault_meta.db      │ │
│  │                         │    │  SQLite: audit.db           │ │
│  │  Key: MASTER_KEY_A      │    │  Key: MASTER_KEY_B          │ │
│  │  (derived from pwd +    │    │  (derived from pwd +        │ │
│  │   salt "library")       │    │   salt "vault")             │ │
│  │                         │    │                             │ │
│  └─────────────────────────┘    └─────────────────────────────┘ │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    KEY DERIVATION                            │ │
│  │                                                              │ │
│  │  User Password                                               │ │
│  │       │                                                      │ │
│  │       ├─→ Argon2id(pwd, salt="library") → MASTER_KEY_A      │ │
│  │       │                                                      │ │
│  │       └─→ Argon2id(pwd, salt="vault")   → MASTER_KEY_B      │ │
│  │                                                              │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Separation

```python
from argon2 import PasswordHasher
from pathlib import Path

class KeyManager:
    """Derive separate keys for each store."""

    LIBRARY_SALT_PURPOSE = "ragd_document_library_v1"
    VAULT_SALT_PURPOSE = "ragd_personal_vault_v1"

    def __init__(self, password: str, config_dir: Path):
        self.hasher = PasswordHasher(
            memory_cost=65536,  # 64 MB
            time_cost=3,
            parallelism=4
        )
        self.config_dir = config_dir

    def derive_library_key(self, password: str) -> bytes:
        """Derive key for Document Library."""
        salt = self._get_or_create_salt("library")
        return self._derive(password, salt, self.LIBRARY_SALT_PURPOSE)

    def derive_vault_key(self, password: str) -> bytes:
        """Derive key for Personal Vault."""
        salt = self._get_or_create_salt("vault")
        return self._derive(password, salt, self.VAULT_SALT_PURPOSE)

    def _derive(self, password: str, salt: bytes, purpose: str) -> bytes:
        """Derive key using Argon2id."""
        # Purpose string ensures keys differ even with same password
        combined = f"{password}:{purpose}"
        return self.hasher.hash(combined.encode(), salt=salt)
```

### Store Boundaries

| Aspect | Document Library | Personal Vault |
|--------|-----------------|----------------|
| **Directory** | `~/.ragd/library/` | `~/.ragd/vault/` |
| **Encryption Key** | MASTER_KEY_A | MASTER_KEY_B |
| **Access Command** | `ragd search` | `ragd vault search` |
| **Default Tier** | Personal | Sensitive |
| **Session Timeout** | 5 minutes | 2 minutes |
| **Audit Logging** | Optional | Mandatory |
| **PII Handling** | Warn | Auto-redact |

### Cross-Store Queries

Cross-store queries are **explicitly prohibited** by default:

```bash
# This searches ONLY the Document Library
ragd search "authentication"

# This searches ONLY the Personal Vault
ragd vault search "authentication"

# Cross-store query (requires explicit flag)
ragd search "authentication" --include-vault
# Requires Vault to be unlocked
# Results clearly labelled by source
```

**Rationale:** Preventing accidental exposure of vault data in regular searches. Users must explicitly opt-in to cross-store queries.

### Audit Requirements

All Vault operations are logged:

```python
class VaultAuditLog:
    """Mandatory audit for Personal Vault."""

    LOGGED_ACTIONS = [
        "unlock",      # Vault unlocked
        "lock",        # Vault locked
        "search",      # Query executed
        "view",        # Result viewed
        "add",         # Data added
        "delete",      # Data removed
        "export",      # Data exported
        "import",      # Data imported
    ]

    def log(self, action: str, details: dict) -> None:
        """Log action to audit trail."""
        entry = AuditEntry(
            timestamp=datetime.utcnow(),
            action=action,
            details=details,
            session_id=self.session_id
        )
        self._write(entry)
```

### Session Management

Vault sessions are independent from Library sessions:

```python
class SessionManager:
    """Manage separate sessions for Library and Vault."""

    def __init__(self):
        self.library_session: Session | None = None
        self.vault_session: Session | None = None

    def unlock_library(self, password: str) -> bool:
        """Unlock Document Library."""
        key = self.key_manager.derive_library_key(password)
        self.library_session = Session(key, timeout=300)  # 5 min
        return True

    def unlock_vault(self, password: str) -> bool:
        """Unlock Personal Vault (separate action)."""
        key = self.key_manager.derive_vault_key(password)
        self.vault_session = Session(key, timeout=120)  # 2 min
        self.audit.log("unlock", {})
        return True

    def is_vault_unlocked(self) -> bool:
        """Check if Vault is accessible."""
        return self.vault_session and not self.vault_session.expired
```

## Consequences

### Positive

- **Defence in depth**: Compromised Library key doesn't expose Vault
- **Compliance-ready**: Clear data boundaries for GDPR/HIPAA
- **Audit trail**: All Vault access logged
- **User control**: Explicit Vault unlock required
- **Shorter attack window**: 2-minute Vault timeout

### Negative

- **Added complexity**: Two stores to manage
- **User friction**: Separate unlock for Vault
- **Storage overhead**: Duplicate ChromaDB infrastructure
- **Development cost**: Additional CLI commands and UI

### Mitigations

- Single password derives both keys (no extra passwords)
- Clear CLI separation (`ragd` vs `ragd vault`)
- Shared codebase with store abstraction layer

## Alternatives Rejected

### Single Key with Data Tagging

Tag data as "library" or "vault" within single encrypted store.

**Rejected because:**
- Key compromise exposes all data
- No true isolation
- Complex access control logic

### Hardware Security Module (HSM)

Use HSM for key storage and operations.

**Rejected because:**
- Not available on all platforms
- Adds significant complexity
- Overkill for personal use case

## Related Documentation

- [F-044: Personal Information Vault](../../features/planned/F-044-personal-vault.md)
- [F-015: Database Encryption](../../features/completed/F-015-database-encryption.md)
- [ADR-0009: Security Architecture](./0009-security-architecture.md)
- [ADR-0010: Vector Database Security](./0010-vector-database-security.md)
- [State-of-the-Art Privacy](../../research/state-of-the-art-privacy.md)

---

**Status**: Accepted
