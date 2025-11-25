# F-017: Secure Deletion

## Overview

**Research**: [State-of-the-Art Privacy](../../research/state-of-the-art-privacy.md)
**ADR**: [ADR-0009: Security Architecture](../../decisions/adrs/0009-security-architecture.md)
**Milestone**: v0.7
**Priority**: P1

## Problem Statement

Standard file deletion doesn't remove data:
- SSDs use wear-levelling, leaving data in hidden areas
- Deleted files remain until overwritten
- Forensic tools can recover "deleted" content

For highly sensitive data, users need true secure deletion.

## Design Approach

### Architecture

```
Delete Request
    ↓
┌─────────────────────────────────┐
│        Secure Deletion          │
├─────────────────────────────────┤
│ 1. Remove from vector index     │
│ 2. Remove encrypted chunks      │
│ 3. Overwrite metadata           │
│ 4. Update encryption key*       │
│ 5. Sync to disk                 │
└─────────────────────────────────┘
    ↓
Deletion Complete

* Key rotation ensures old data unrecoverable
  even if fragments exist on disk
```

### Deletion Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| Standard | Remove from index | Normal cleanup |
| Secure | + Overwrite storage locations | Sensitive documents |
| Cryptographic | + Rotate encryption key | Maximum security |

### The SSD Challenge

Traditional overwrite doesn't work on SSDs due to:
- Wear-levelling spreads data across cells
- TRIM marks blocks as free but doesn't erase
- Controller may retain copies

**Solution:** Cryptographic erasure - destroy the key, data becomes unrecoverable.

## Implementation Tasks

- [ ] Implement standard deletion (remove from index)
- [ ] Implement metadata overwrite
- [ ] Implement cryptographic erasure (key rotation)
- [ ] Add `ragd delete` command
- [ ] Add `--secure` flag for secure deletion
- [ ] Add `--purge` for cryptographic erasure
- [ ] Add bulk deletion support
- [ ] Add deletion confirmation prompts
- [ ] Implement deletion audit log
- [ ] Write tests

## Success Criteria

- [ ] Documents removable from index
- [ ] Secure deletion overwrites storage
- [ ] Cryptographic erasure rotates keys
- [ ] Deletion audit trail maintained
- [ ] Bulk deletion supported
- [ ] Clear user feedback on deletion type

## Dependencies

- F-015: Database Encryption
- F-016: Session Management

## Technical Notes

### CLI Commands

```bash
# Standard deletion
ragd delete document.pdf
Delete "document.pdf" from index? [y/N] y
✓ Removed from index

# Secure deletion
ragd delete document.pdf --secure
Secure delete "document.pdf"? This cannot be undone. [y/N] y
  ├─ Removing from vector index... done
  ├─ Overwriting chunk storage... done
  └─ Syncing to disk... done
✓ Securely deleted

# Cryptographic erasure (maximum security)
ragd delete document.pdf --purge
PURGE "document.pdf"? This rotates the encryption key. [y/N] y
Enter password to confirm: ********
  ├─ Removing from vector index... done
  ├─ Rotating encryption key... done
  └─ Re-encrypting remaining data... done
✓ Purged with key rotation

# Bulk deletion
ragd delete --all --source ~/old-docs/
Delete 47 documents from ~/old-docs/? [y/N] y
```

### Configuration

```yaml
security:
  deletion:
    default_level: standard    # standard | secure | purge
    require_confirmation: true
    audit_log: true
    audit_path: ~/.ragd/audit/deletions.log
```

### Deletion Audit Log

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "action": "secure_delete",
  "document": "medical-record.pdf",
  "document_hash": "sha256:abc123...",
  "chunks_removed": 15,
  "key_rotated": false,
  "user_confirmed": true
}
```

### Cryptographic Erasure Flow

```python
def purge_with_key_rotation(document_id: str, password: str):
    """Securely delete with key rotation."""
    # 1. Verify password
    verify_password(password)

    # 2. Generate new key
    new_key = derive_key(password, new_salt())

    # 3. Remove target document
    remove_from_index(document_id)

    # 4. Re-encrypt remaining data with new key
    for chunk in get_all_chunks():
        decrypted = decrypt(chunk, old_key)
        encrypted = encrypt(decrypted, new_key)
        store(chunk.id, encrypted)

    # 5. Destroy old key
    secure_clear(old_key)

    # 6. Store new salt
    store_salt(new_salt)
```

## Related Documentation

- [ADR-0009: Security Architecture](../../decisions/adrs/0009-security-architecture.md)
- [F-015: Database Encryption](./F-015-database-encryption.md)
- [F-016: Session Management](./F-016-session-management.md)
- [State-of-the-Art Privacy Research](../../research/state-of-the-art-privacy.md)

---
