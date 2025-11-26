# F-044: Personal Information Vault

## Overview

**Research**: [State-of-the-Art Personal RAG](../../research/state-of-the-art-personal-rag.md)
**Milestone**: v2.0
**Priority**: P0

## Problem Statement

The Document Library handles general documents (PDFs, notes, research). However, users also want to query their highly sensitive personal data:

- **Browser history** - "When did I research that topic?"
- **Communications** - "What did Sarah email me about the project?"
- **Health records** - "What were my test results from March?"
- **Financial data** - "How much did I spend on X last quarter?"

This data requires:
1. **Higher security** than general documents (separate encryption keys)
2. **Stricter PII handling** (auto-redaction by default)
3. **Audit logging** for compliance
4. **Clear separation** from the Document Library

## Design Approach

### Architecture

Dual-store architecture with separate encryption domains:

```
┌─────────────────────────────────────────────────────────────────┐
│                         ragd Data Stores                         │
├────────────────────────────┬────────────────────────────────────┤
│                            │                                     │
│    DOCUMENT LIBRARY        │      PERSONAL INFORMATION VAULT    │
│    (Primary Store)         │      (High-Security Store)         │
│                            │                                     │
│  ┌──────────────────────┐  │  ┌──────────────────────────────┐  │
│  │ ChromaDB + SQLite    │  │  │ ChromaDB + SQLite            │  │
│  │ SQLCipher (Key A)    │  │  │ SQLCipher (Key B)            │  │
│  ├──────────────────────┤  │  ├──────────────────────────────┤  │
│  │ • PDFs, articles     │  │  │ • Browser history            │  │
│  │ • Research papers    │  │  │ • Email/chat exports         │  │
│  │ • Books, manuals     │  │  │ • Health records (FHIR)      │  │
│  │ • Notes, markdown    │  │  │ • Financial statements       │  │
│  │                      │  │  │ • Purchase receipts          │  │
│  │ Tier: Personal       │  │  │ Tier: Sensitive/Critical     │  │
│  └──────────────────────┘  │  └──────────────────────────────┘  │
│                            │                                     │
│  Accessible via:           │  Accessible via:                   │
│  ragd search               │  ragd vault search                 │
│  ragd add                  │  ragd vault add                    │
│                            │                                     │
└────────────────────────────┴────────────────────────────────────┘
```

### Security Model

| Aspect | Document Library | Personal Vault |
|--------|-----------------|----------------|
| **Encryption Key** | Master Key A | Master Key B (separate) |
| **Default Tier** | Personal | Sensitive |
| **PII Detection** | Warn on detection | Auto-redact by default |
| **Access Logging** | Optional | Mandatory audit log |
| **Session Timeout** | 5 minutes | 2 minutes |
| **Export** | Allowed | Requires confirmation |

### Data Type Connectors

| Type | Connector | Format | Priority |
|------|-----------|--------|----------|
| Browser history | WebArchiveConnector | WARC, HAR, history.db | P2 |
| Email | EmailConnector | MBOX, EML, PST | P3 |
| Chat logs | ChatConnector | JSON, CSV, proprietary | P3 |
| Health records | FHIRConnector | FHIR JSON/XML | P3 |
| Financial data | FinanceConnector | OFX, QIF, CSV | P3 |
| Receipts | ReceiptConnector | PDF, images | P4 |

## Implementation Tasks

### Core Infrastructure
- [ ] Design VaultStore class (separate from DocumentStore)
- [ ] Implement separate encryption key management
- [ ] Create vault-specific database (ChromaDB collection)
- [ ] Implement data type enum (browser, email, health, finance, etc.)
- [ ] Design vault metadata schema

### Security Features
- [ ] Implement Key B derivation (separate from Document Library)
- [ ] Add mandatory audit logging
- [ ] Implement stricter session timeout
- [ ] Add auto-redaction pipeline (PII → vault)
- [ ] Implement export confirmation workflow
- [ ] Add vault-specific backup encryption

### Data Type Connectors (v2.x)
- [ ] Implement base Connector interface
- [ ] Create WebArchiveConnector (WARC, HAR)
- [ ] Create BrowserHistoryConnector (Chrome, Firefox, Safari)
- [ ] Create EmailConnector (MBOX, EML)
- [ ] Create FHIRConnector (health records)
- [ ] Create FinanceConnector (OFX, bank statements)

### CLI Commands
- [ ] Implement `ragd vault status`
- [ ] Implement `ragd vault add <file>`
- [ ] Implement `ragd vault search <query>`
- [ ] Implement `ragd vault import --type <type>`
- [ ] Implement `ragd vault audit`
- [ ] Implement `ragd vault export` (with confirmation)
- [ ] Implement `ragd vault purge` (secure deletion)

### Testing
- [ ] Write unit tests for VaultStore
- [ ] Write integration tests for separate encryption
- [ ] Test audit logging completeness
- [ ] Test PII auto-redaction pipeline
- [ ] Security audit of key separation

## Success Criteria

- [ ] Vault uses separate encryption key from Document Library
- [ ] All vault access logged in audit trail
- [ ] PII auto-redacted before storage
- [ ] Vault data never mixed with Document Library
- [ ] Secure deletion removes all traces
- [ ] Session timeout enforced (2 min default)
- [ ] Export requires explicit confirmation
- [ ] At least one connector functional (browser history)

## Dependencies

### Required (P0)
- F-015 Database Encryption (v0.7)
- F-023 PII Detection (v0.7)
- F-017 Secure Deletion (v0.7)
- F-040 Long-Term Memory (v2.0-alpha)

### Optional
- F-045 Browser History Connector (v2.1+)
- F-046 Communication Parser (v2.1+)
- F-047 Health Record Import (v2.2+)

## Technical Notes

### Vault Schema

```python
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class VaultDataType(str, Enum):
    BROWSER_HISTORY = "browser_history"
    EMAIL = "email"
    CHAT = "chat"
    HEALTH = "health"
    FINANCE = "finance"
    RECEIPT = "receipt"
    OTHER = "other"

class VaultEntry(BaseModel):
    """Entry in the Personal Vault."""
    id: str
    data_type: VaultDataType
    content: str  # Redacted content
    original_hash: str  # For deduplication
    source: str  # Where it came from
    source_date: datetime | None  # Original timestamp
    imported_at: datetime
    metadata: dict = {}

    # Security
    pii_redacted: bool = True
    redaction_map: dict = {}  # Encrypted map for re-insertion

class VaultAuditEntry(BaseModel):
    """Audit log entry."""
    id: str
    timestamp: datetime
    action: str  # search, view, export, delete
    vault_entry_id: str | None
    query: str | None
    result_count: int | None
    ip_address: str | None  # For multi-device future
```

### Key Separation

```python
from argon2 import PasswordHasher
import secrets

class VaultKeyManager:
    """Manages separate encryption keys for vault."""

    def __init__(self, master_password: str):
        self.hasher = PasswordHasher(
            memory_cost=65536,  # 64 MB
            time_cost=3,
            parallelism=4
        )

        # Derive separate keys using different salts
        self.document_key = self._derive_key(
            master_password,
            salt_purpose="document_library"
        )
        self.vault_key = self._derive_key(
            master_password,
            salt_purpose="personal_vault"
        )

    def _derive_key(self, password: str, salt_purpose: str) -> bytes:
        """Derive key with purpose-specific salt."""
        # Salt stored in config, generated on first run
        salt = self._get_or_create_salt(salt_purpose)
        return self.hasher.hash(password + salt_purpose)
```

### PII Auto-Redaction Pipeline

```python
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

class VaultRedactionPipeline:
    """Auto-redact PII before vault storage."""

    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

        # Vault-specific entity types (stricter than library)
        self.entities = [
            "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER",
            "CREDIT_CARD", "IBAN_CODE", "US_SSN",
            "UK_NHS", "MEDICAL_LICENSE", "DATE_TIME",
            "LOCATION", "IP_ADDRESS", "URL"
        ]

    async def redact(self, content: str) -> tuple[str, dict]:
        """Redact PII, return redacted text and map."""
        results = self.analyzer.analyze(
            text=content,
            entities=self.entities,
            language="en"
        )

        # Create reversible redaction map (encrypted storage)
        redaction_map = {}
        for result in results:
            placeholder = f"[{result.entity_type}_{len(redaction_map)}]"
            redaction_map[placeholder] = content[result.start:result.end]

        # Anonymise
        redacted = self.anonymizer.anonymize(
            text=content,
            analyzer_results=results
        )

        return redacted.text, redaction_map
```

### Audit Logging

```python
import sqlite3
from datetime import datetime

class VaultAuditLog:
    """Mandatory audit logging for vault access."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    action TEXT NOT NULL,
                    vault_entry_id TEXT,
                    query TEXT,
                    result_count INTEGER,
                    success INTEGER NOT NULL
                )
            """)

    async def log(
        self,
        action: str,
        entry_id: str | None = None,
        query: str | None = None,
        result_count: int | None = None,
        success: bool = True
    ):
        """Log vault access."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO audit_log
                   (id, timestamp, action, vault_entry_id, query, result_count, success)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    secrets.token_hex(16),
                    datetime.utcnow().isoformat(),
                    action,
                    entry_id,
                    query,
                    result_count,
                    1 if success else 0
                )
            )

    async def get_audit_trail(
        self,
        since: datetime | None = None,
        action: str | None = None,
        limit: int = 100
    ) -> list[VaultAuditEntry]:
        """Retrieve audit trail."""
        pass
```

### Configuration

```yaml
vault:
  enabled: true
  database: ~/.ragd/vault.db
  audit_log: ~/.ragd/vault_audit.db

  # Separate encryption (uses different salt)
  encryption:
    enabled: true
    key_derivation: argon2id
    separate_key: true  # Critical: separate from document library

  # Stricter security settings
  security:
    default_tier: sensitive
    session_timeout: 120  # 2 minutes (vs 5 for library)
    require_confirmation_for_export: true
    pii_auto_redact: true

  # Audit logging (mandatory)
  audit:
    enabled: true
    log_searches: true
    log_views: true
    log_exports: true
    retention_days: 365

  # Data type settings
  data_types:
    browser_history:
      enabled: true
      sources: [chrome, firefox, safari]
    email:
      enabled: false
    health:
      enabled: false
      fhir_version: R4
    finance:
      enabled: false
```

### CLI Commands

```bash
# Vault status
ragd vault status
# Output:
# Personal Vault: Locked
# Entries: 1,234
# Data types: browser_history (890), email (344)
# Last accessed: 2 hours ago
# Audit entries: 5,678

# Unlock vault (separate from document library)
ragd vault unlock

# Add to vault (auto-redacts PII)
ragd vault add ~/Downloads/bank-statement.pdf --type finance
ragd vault add ~/export/chrome-history.json --type browser_history

# Search vault
ragd vault search "medical appointment March"
ragd vault search "purchase from Amazon" --type finance

# Import from sources
ragd vault import --type browser_history --source chrome
ragd vault import --type email --source ~/mail-export.mbox

# View audit trail
ragd vault audit
ragd vault audit --since 7d --action search

# Export (requires confirmation)
ragd vault export --type health --output health-records.json
# Warning: This will export sensitive data. Continue? [y/N]

# Secure deletion
ragd vault purge --older-than 1y
ragd vault purge --type browser_history --confirm
```

### Connector Interface

```python
from abc import ABC, abstractmethod

class VaultConnector(ABC):
    """Base class for vault data connectors."""

    @property
    @abstractmethod
    def data_type(self) -> VaultDataType:
        """Return the data type this connector handles."""
        pass

    @property
    @abstractmethod
    def supported_formats(self) -> list[str]:
        """Return supported file formats."""
        pass

    @abstractmethod
    async def import_file(self, path: str) -> list[VaultEntry]:
        """Import data from file."""
        pass

    @abstractmethod
    async def import_from_source(self, source: str) -> list[VaultEntry]:
        """Import directly from source (e.g., Chrome)."""
        pass


class BrowserHistoryConnector(VaultConnector):
    """Import browser history."""

    data_type = VaultDataType.BROWSER_HISTORY
    supported_formats = ["json", "sqlite", "har", "warc"]

    async def import_from_source(self, source: str) -> list[VaultEntry]:
        """Import from browser."""
        if source == "chrome":
            return await self._import_chrome()
        elif source == "firefox":
            return await self._import_firefox()
        # ...
```

## Related Documentation

- [State-of-the-Art Personal RAG](../../research/state-of-the-art-personal-rag.md) - Research basis
- [State-of-the-Art Privacy](../../research/state-of-the-art-privacy.md) - Security architecture
- [F-015: Database Encryption](./F-015-database-encryption.md) - Encryption foundation
- [F-023: PII Detection](./F-023-pii-detection.md) - Redaction pipeline
- [F-040: Long-Term Memory](./F-040-long-term-memory.md) - Memory integration
- [ADR-0022: Personal Vault Isolation](../../decisions/adrs/0022-personal-vault-isolation.md) - Architecture decision

---

**Status**: Planned
