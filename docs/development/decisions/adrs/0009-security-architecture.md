# ADR-0009: Security Architecture

## Status

Accepted

## Context

ragd handles highly sensitive personal data: medical records, financial documents, journals, credentials. The threat model includes:

- **Physical access**: Stolen/shared device
- **Code access**: Direct database file access
- **Memory attacks**: Cold boot, swap analysis

A privacy-first architecture is essential for user trust.

## Decision

Implement a layered security architecture for v0.7:

### Layer 1: Encryption at Rest

**Database Encryption (SQLCipher):**
```
User Password → [Argon2id KDF] → Master Key → [AES-256] → Encrypted Database
```

ChromaDB uses SQLite internally. SQLCipher provides:
- Transparent 256-bit AES encryption
- 5-15% performance overhead
- No application code changes

### Layer 2: Key Derivation (Argon2id)

Winner of 2015 Password Hashing Competition:
```
Password + Salt → [Argon2id: 64MB memory, 3 iterations, 4 threads] → 256-bit Key
```

Resists GPU and side-channel attacks.

### Layer 3: Session Management

```
Last Activity → [Timeout: 5 min] → Lock Screen → [Re-auth Required]
```

- Auto-lock after inactivity
- Clear keys from memory on lock
- Configurable timeout

### Layer 4: Memory Protection

- Prevent key material from swapping (mlock)
- Disable core dumps
- Clear buffers after use

### Configuration

```yaml
security:
  encryption:
    algorithm: AES-256-GCM
    kdf: argon2id
    kdf_memory_mb: 64
    kdf_iterations: 3

  session:
    auto_lock_minutes: 5
    failed_attempts_lockout: 5

  authentication:
    require_password: true
    allow_biometric: true  # Future
```

## Consequences

### Positive

- Strong protection against physical access threats
- Industry-standard encryption (AES-256)
- Memory-hard key derivation (Argon2id)
- Transparent to most user workflows
- Foundation for advanced security features

### Negative

- Performance overhead (5-15%)
- User must remember password
- Session lock interrupts workflow
- SQLCipher dependency

## Implementation Phases

| Feature | Phase | Priority |
|---------|-------|----------|
| SQLCipher integration | v0.7.0 | Critical |
| Argon2id KDF | v0.7.0 | Critical |
| Session lock | v0.7.0 | High |
| Memory protection | v0.7.1 | Medium |
| Biometric unlock | v0.9+ | Low |

## Related Documentation

- [State-of-the-Art Privacy Research](../../research/state-of-the-art-privacy.md)
- [F-015: Database Encryption](../../features/completed/F-015-database-encryption.md)
- [F-016: Session Management](../../features/completed/F-016-session-management.md)
- [ADR-0010: Vector Database Security](./0010-vector-database-security.md)

---
