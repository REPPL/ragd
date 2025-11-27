# F-033: Import Engine

## Overview

**Use Case**: [UC-006](../../../use-cases/briefs/UC-006-export-backup.md)
**Milestone**: v0.2
**Priority**: P0

## Problem Statement

Export is only useful if data can be restored. Users need to import archives to recover from backups, migrate between machines, or merge knowledge bases.

## Design Approach

Implement a robust import engine that validates archives before restoration and handles version compatibility.

**Import Pipeline:**
```
Archive File
      ↓
┌─────────────────────────────────────────────────────┐
│ Stage 1: Validation                                  │
│   - Verify archive integrity (checksums)             │
│   - Check version compatibility                      │
│   - Validate manifest structure                      │
└─────────────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────────────┐
│ Stage 2: Conflict Detection                          │
│   - Check for existing documents                     │
│   - Identify potential duplicates                    │
│   - Present merge options to user                    │
└─────────────────────────────────────────────────────┘
      ↓
┌─────────────────────────────────────────────────────┐
│ Stage 3: Restoration                                 │
│   - Import document metadata                         │
│   - Import chunks                                    │
│   - Import embeddings (or re-generate)               │
│   - Verify import success                            │
└─────────────────────────────────────────────────────┘
```

**Conflict Resolution Options:**

| Option | Behaviour |
|--------|-----------|
| `--skip` | Skip documents that already exist |
| `--replace` | Replace existing with imported version |
| `--merge` | Merge metadata, keep latest chunks |
| `--rename` | Import with new ID, keep both versions |

## Implementation Tasks

- [ ] Implement archive validation (checksum verification)
- [ ] Implement version compatibility checking
- [ ] Create conflict detection logic
- [ ] Implement document metadata import
- [ ] Implement chunk data import
- [ ] Implement embedding import/regeneration
- [ ] Create `ragd import <path>` CLI command
- [ ] Add dry-run mode (`--dry-run`)
- [ ] Add progress feedback for large imports
- [ ] Handle partial/corrupt archives gracefully

## Success Criteria

- [ ] Archives restore complete knowledge base
- [ ] Checksum verification catches corruption
- [ ] Version incompatibility detected and reported
- [ ] Conflicts detected and user prompted
- [ ] Dry-run mode shows what would be imported
- [ ] Large archives import with progress feedback

## Dependencies

- [F-032: Export Engine](./F-032-export-engine.md) - Creates archives
- [F-029: Metadata Storage](./F-029-metadata-storage.md) - Target for import
- [F-004: Embedding Generation](./F-004-embedding-generation.md) - For re-embedding

## Technical Notes

**Version Compatibility:**
```python
CURRENT_VERSION = "1.0"
COMPATIBLE_VERSIONS = ["1.0"]  # Versions we can import

def check_compatibility(manifest):
    if manifest["version"] not in COMPATIBLE_VERSIONS:
        raise IncompatibleVersionError(
            f"Archive version {manifest['version']} not supported. "
            f"Compatible versions: {COMPATIBLE_VERSIONS}"
        )
```

**Embedding Handling:**
```python
def import_embeddings(archive, regenerate=False):
    if regenerate:
        # Re-generate embeddings with current model
        # Useful when switching embedding models
        for chunk in archive.chunks:
            new_embedding = embed(chunk.text)
            store_embedding(chunk.id, new_embedding)
    else:
        # Use archived embeddings
        # Verify dimensions match current config
        if archive.embedding_dimensions != config.embedding_dimensions:
            raise DimensionMismatchError(...)
        import_embeddings_directly(archive.embeddings)
```

**CLI Usage:**
```bash
# Full import
ragd import ~/backup/ragd-backup.tar.gz

# Dry run (show what would be imported)
ragd import ~/backup/ragd-backup.tar.gz --dry-run

# Skip existing documents
ragd import ~/backup/ragd-backup.tar.gz --skip

# Replace existing with imported
ragd import ~/backup/ragd-backup.tar.gz --replace

# Re-generate embeddings (for model changes)
ragd import ~/backup/ragd-backup.tar.gz --regenerate-embeddings
```

## Related Documentation

- [F-032: Export Engine](./F-032-export-engine.md)
- [F-034: Archive Format](./F-034-archive-format.md)
- [UC-006: Export & Backup](../../../use-cases/briefs/UC-006-export-backup.md)

---

**Status**: Completed
