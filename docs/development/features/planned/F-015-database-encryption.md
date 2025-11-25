# F-015: Database Encryption

## Overview

**Research**: [State-of-the-Art Privacy](../../research/state-of-the-art-privacy.md)
**ADR**: [ADR-0009: Security Architecture](../../decisions/adrs/0009-security-architecture.md)
**Milestone**: v0.7
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

- [ ] Add SQLCipher dependency
- [ ] Implement Argon2id key derivation
- [ ] Implement master key management
- [ ] Modify ChromaDB initialisation for SQLCipher
- [ ] Add password prompt on first use
- [ ] Add unlock command
- [ ] Add lock command
- [ ] Implement key rotation
- [ ] Handle password changes
- [ ] Write security tests
- [ ] Document backup procedures

## Success Criteria

- [ ] Database encrypted at rest with AES-256
- [ ] Password required to unlock
- [ ] Argon2id key derivation (64MB, 3 iterations)
- [ ] Performance overhead < 15%
- [ ] Graceful handling of wrong password
- [ ] Key rotation supported

## Dependencies

- sqlcipher3 Python binding
- argon2-cffi library

## Technical Notes

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

### ChromaDB with SQLCipher

```python
import sqlcipher3

def create_encrypted_client(path: str, key: bytes) -> chromadb.Client:
    # SQLCipher connection
    conn = sqlcipher3.connect(f"{path}/chroma.db")
    conn.execute(f"PRAGMA key = \"x'{key.hex()}'\"")

    # ChromaDB with custom SQLite
    return chromadb.Client(
        Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=path,
            anonymized_telemetry=False
        )
    )
```

### Error Handling

```
Error: Incorrect password

The password you entered is incorrect.

Suggestions:
  • Check caps lock is off
  • Try your password again
  • Use 'ragd password reset' if you've forgotten
    (Warning: This will delete all data)
```

### Migration from Unencrypted

```bash
ragd migrate --encrypt
Enter new password: ********

Migrating to encrypted database...
  ├─ Exporting current data... done
  ├─ Creating encrypted database... done
  ├─ Importing data... done
  └─ Verifying... done

✓ Migration complete. Old database backed up to ~/.ragd/backup/
```

## Related Documentation

- [ADR-0009: Security Architecture](../../decisions/adrs/0009-security-architecture.md)
- [F-016: Session Management](./F-016-session-management.md)
- [ADR-0010: Vector Database Security](../../decisions/adrs/0010-vector-database-security.md)
- [State-of-the-Art Privacy Research](../../research/state-of-the-art-privacy.md)

---
