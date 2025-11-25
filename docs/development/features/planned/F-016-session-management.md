# F-016: Session Management

## Overview

**Research**: [State-of-the-Art Privacy](../../research/state-of-the-art-privacy.md)
**ADR**: [ADR-0009: Security Architecture](../../decisions/adrs/0009-security-architecture.md)
**Milestone**: v0.7
**Priority**: P0

## Problem Statement

Even with database encryption, an unlocked session leaves data vulnerable:
- Unattended computer allows access
- Keys in memory can be extracted
- No accountability for access

Session management ensures data is protected when not actively in use.

## Design Approach

### Architecture

```
User Authenticates
    ↓
[Load Keys to Memory]
    ↓
Session Active ←──────────────────────┐
    │                                 │
    │ Activity                        │
    ▼                                 │
[Reset Timer] ───────────────────────┘
    │
    │ Timeout (5 min)
    ▼
[Clear Keys from Memory]
    ↓
Session Locked
```

### Session States

| State | Keys in Memory | Access |
|-------|---------------|--------|
| Locked | No | None |
| Active | Yes | Full |
| Idle | Yes (pending clear) | Full |

### Auto-Lock Behaviour

1. Start inactivity timer on each operation
2. After timeout, clear decryption keys
3. Require re-authentication for next operation

## Implementation Tasks

- [ ] Implement session state machine
- [ ] Implement inactivity timer
- [ ] Implement key clearing on lock
- [ ] Add `ragd unlock` command
- [ ] Add `ragd lock` command
- [ ] Add session status to `ragd status`
- [ ] Implement failed attempt tracking
- [ ] Add lockout after N failures
- [ ] Add session persistence option
- [ ] Write security tests

## Success Criteria

- [ ] Auto-lock after configurable timeout
- [ ] Keys cleared from memory on lock
- [ ] Re-authentication required after lock
- [ ] Failed attempt tracking and lockout
- [ ] Session status visible in CLI
- [ ] Graceful handling of locked state

## Dependencies

- F-015: Database Encryption

## Technical Notes

### CLI Commands

```bash
# Check session status
ragd status
Session: 🔓 Unlocked (4:32 remaining)

ragd status
Session: 🔒 Locked

# Manual unlock
ragd unlock
Enter password: ********
✓ Session unlocked for 5 minutes

# Manual lock
ragd lock
✓ Session locked

# Extend session
ragd unlock --extend
✓ Session extended by 5 minutes
```

### Configuration

```yaml
security:
  session:
    auto_lock_minutes: 5       # 0 = disabled
    failed_attempts_lockout: 5
    lockout_minutes: 15
    persist_session: false     # Keep unlocked across restarts
```

### Session File

```yaml
# ~/.ragd/.session (encrypted, temporary)
unlocked_at: 2024-01-15T10:30:00Z
expires_at: 2024-01-15T10:35:00Z
failed_attempts: 0
```

### Error Handling

```
Error: Session locked

Your session has timed out for security.

Run 'ragd unlock' to continue.
```

```
Error: Too many failed attempts

You have entered the wrong password 5 times.
Please wait 15 minutes before trying again.

Or run 'ragd password reset' to reset (warning: deletes all data).
```

### Key Clearing

```python
def lock_session():
    """Clear sensitive data from memory."""
    # Clear key material
    if master_key:
        # Overwrite with zeros
        ctypes.memset(ctypes.addressof(master_key), 0, len(master_key))
        master_key = None

    # Clear session token
    session.clear()

    # Force garbage collection
    gc.collect()
```

### Memory Protection

For additional security (mlock):

```python
import ctypes

def protect_key(key: bytes) -> None:
    """Prevent key from being swapped to disk."""
    libc = ctypes.CDLL("libc.dylib")  # macOS
    libc.mlock(key, len(key))
```

## Related Documentation

- [ADR-0009: Security Architecture](../../decisions/adrs/0009-security-architecture.md)
- [F-015: Database Encryption](./F-015-database-encryption.md)
- [F-017: Secure Deletion](./F-017-secure-deletion.md)
- [State-of-the-Art Privacy Research](../../research/state-of-the-art-privacy.md)

---
