# F-015: Database Encryption

## Overview

**Research**: [State-of-the-Art Privacy](../../research/state-of-the-art-privacy.md)
**ADR**: [ADR-0009: Security Architecture](../../decisions/adrs/0009-security-architecture.md)
**Milestone**: v0.7.0
**Priority**: P0

## Problem Statement

ragd stores highly sensitive personal data. Without encryption:
- Stolen devices expose all knowledge base contents
- Shared devices allow unauthorised access
- Discarded devices may leak data forensically

Database encryption protects data at rest against these threats.

## Design Approach

### Architecture

```
User Password
    ↓
[Argon2id KDF]
    ↓
Master Key (256-bit)
    ↓
┌─────────────────────────────────────┐
│           SQLCipher                  │
│  ┌─────────────────────────────────┐│
│  │      ChromaDB (SQLite)          ││
│  │  • Vector embeddings            ││
│  │  • Chunk metadata               ││
│  │  • Document index               ││
│  └─────────────────────────────────┘│
│           [AES-256-GCM]             │
└─────────────────────────────────────┘
```

### Key Derivation (Argon2id)

Winner of 2015 Password Hashing Competition:

```
Password + Salt → [Argon2id] → Master Key

Parameters:
- Memory: 64 MB
- Iterations: 3
- Parallelism: 4 threads
- Output: 256 bits
```

### SQLCipher Integration

SQLCipher provides transparent AES-256 encryption for SQLite:

- **Overhead**: 5-15% performance
- **Compatibility**: Drop-in SQLite replacement
- **Security**: AES-256 in GCM mode

## Implementation Tasks

- [x] Add SQLCipher dependency
- [x] Implement Argon2id key derivation
- [x] Implement master key management
- [x] Modify ChromaDB initialisation for SQLCipher
- [x] Add password prompt on first use
- [x] Add unlock command
- [x] Add lock command
- [x] Implement key rotation
- [x] Handle password changes
- [x] Write security tests
- [x] Document backup procedures

## Success Criteria

- [x] Database encrypted at rest with AES-256
- [x] Password required to unlock
- [x] Argon2id key derivation (64MB, 3 iterations)
- [x] Performance overhead < 15%
- [x] Graceful handling of wrong password
- [x] Key rotation supported

## Dependencies

- sqlcipher3 Python binding
- argon2-cffi library

## Implementation Notes

### Module Structure

```
src/ragd/security/
├── __init__.py
├── crypto.py          # Argon2id key derivation
├── keystore.py        # Master key management
├── encrypted_store.py # SQLCipher wrapper
└── session.py         # Session integration
```

### CLI Commands

```bash
# Initial setup (prompts for password)
ragd init
Enter password: ********
Confirm password: ********
✓ Database initialised with encryption

# Unlock for session
ragd unlock
Enter password: ********
✓ Unlocked for 5 minutes

# Lock immediately
ragd lock
✓ Database locked

# Change password
ragd password change
Current password: ********
New password: ********
Confirm password: ********
✓ Password changed

# Key rotation
ragd password rotate-key
✓ Encryption key rotated
```

### Configuration

```yaml
security:
  encryption:
    enabled: true
    algorithm: AES-256-GCM
    kdf: argon2id
    kdf_memory_mb: 64
    kdf_iterations: 3
    kdf_parallelism: 4

  session:
    auto_lock_minutes: 5
```

## Related Documentation

- [ADR-0009: Security Architecture](../../decisions/adrs/0009-security-architecture.md)
- [F-016: Session Management](./F-016-session-management.md)
- [ADR-0010: Vector Database Security](../../decisions/adrs/0010-vector-database-security.md)
- [State-of-the-Art Privacy Research](../../research/state-of-the-art-privacy.md)

