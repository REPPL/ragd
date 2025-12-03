# F-018: Data Sensitivity Tiers

## Overview

**Research**: [State-of-the-Art Privacy](../../research/state-of-the-art-privacy.md)
**ADR**: [ADR-0010: Vector Database Security](../../decisions/adrs/0010-vector-database-security.md)
**Milestone**: v0.7
**Priority**: P2

## Problem Statement

Not all data needs the same protection level:
- General notes need basic security
- Medical records need strong protection
- Credentials need maximum security

A one-size-fits-all approach either:
- Over-secures low-sensitivity data (poor UX)
- Under-secures high-sensitivity data (poor security)

## Design Approach

### Architecture

```
Document
    ↓
[Classify Sensitivity]
    ↓
┌─────────────────────────────────────────────┐
│              Sensitivity Tiers              │
├─────────────────────────────────────────────┤
│ PUBLIC      │ Always accessible             │
│ PERSONAL    │ Password unlock               │
│ SENSITIVE   │ + Biometric (future)          │
│ CRITICAL    │ + Hardware key (future)       │
└─────────────────────────────────────────────┘
    ↓
Tier-Appropriate Storage & Access
```

### Tier Definitions

| Tier | Data Type | Access Control | Storage |
|------|-----------|----------------|---------|
| **Public** | Bookmarks, public notes | Always | Encrypted DB |
| **Personal** | Personal notes, preferences | Password | + Per-tier key |
| **Sensitive** | Medical, financial | Password + biometric | + Additional encryption |
| **Critical** | Credentials, legal | Hardware key required | + Time-limited access |

### Access Control Flow

```
Search Request
    ↓
[Determine Max Tier Needed]
    ↓
[Check Current Auth Level]
    │
    ├── Sufficient → Return Results
    │
    └── Insufficient → Prompt for Auth
                           │
                           ▼
                    [Elevate Auth Level]
                           │
                           ▼
                    Return Results (with timeout)
```

## Implementation Tasks

### Phase 1 (v0.7)
- [ ] Implement tier data model
- [ ] Add tier assignment during indexing
- [ ] Add tier-based access control
- [ ] Add `--tier` flag to index command
- [ ] Add tier display in search results
- [ ] Filter results by auth level

### Phase 2 (v0.9+)
- [ ] Add biometric support (macOS Touch ID)
- [ ] Add hardware key support (FIDO2)
- [ ] Add time-limited access for critical tier
- [ ] Add auto-classification hints

## Success Criteria

- [ ] Documents assignable to tiers
- [ ] Access control enforced per tier
- [ ] Search results filtered by auth level
- [ ] Clear UX for tier elevation
- [ ] Tier visible in status/search output

## Dependencies

- F-015: Database Encryption
- F-016: Session Management

## Technical Notes

### CLI Commands

```bash
# Index with tier
ragd index medical-records.pdf --tier sensitive
ragd index bank-statement.pdf --tier sensitive
ragd index api-keys.txt --tier critical
ragd index notes.md  # Default: personal

# Search (prompts if needed)
ragd search "my bank account"
This search includes SENSITIVE documents.
[Biometric prompt or password]
Results: ...

# Search specific tier
ragd search "api keys" --tier critical
Enter password: ********
[Hardware key prompt]
Results: (auto-clear in 30 seconds)

# List documents by tier
ragd list --tier sensitive

# Change document tier
ragd tier set medical.pdf sensitive
```

### Configuration

```yaml
security:
  tiers:
    enabled: true

    # Tier requirements
    public:
      auth: none

    personal:
      auth: password

    sensitive:
      auth: [password, biometric]  # Any of these
      auto_clear_seconds: 60

    critical:
      auth: [password, hardware_key]  # Both required
      auto_clear_seconds: 30
      max_session_minutes: 5
```

### Data Model

```python
class DataTier(Enum):
    PUBLIC = "public"
    PERSONAL = "personal"
    SENSITIVE = "sensitive"
    CRITICAL = "critical"

@dataclass
class TieredDocument:
    id: str
    path: str
    tier: DataTier
    tier_key: bytes | None  # Per-tier encryption key
    access_count: int
    last_accessed: datetime | None
```

### Storage Architecture

```
~/.ragd/
├── data/
│   ├── public/         # Tier-specific storage
│   ├── personal/
│   ├── sensitive/
│   └── critical/
├── keys/
│   ├── master.key      # Encrypted master key
│   └── tiers/
│       ├── personal.key
│       ├── sensitive.key
│       └── critical.key
```

### Auto-Classification (Future)

Hint patterns for automatic tier suggestion:

```yaml
classification:
  hints:
    sensitive:
      - "medical"
      - "health"
      - "financial"
      - "bank"
    critical:
      - "password"
      - "credential"
      - "api.key"
      - "secret"
```

## Related Documentation

- [ADR-0010: Vector Database Security](../../decisions/adrs/0010-vector-database-security.md)
- [ADR-0009: Security Architecture](../../decisions/adrs/0009-security-architecture.md)
- [F-015: Database Encryption](./F-015-database-encryption.md)
- [State-of-the-Art Privacy Research](../../research/state-of-the-art-privacy.md)

---
