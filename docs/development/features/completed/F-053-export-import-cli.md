# F-053: Export/Import CLI

## Overview

**Use Case**: Command-line backup and restore
**Milestone**: v0.2.8
**Priority**: P1

## Problem Statement

The export engine (F-032), import engine (F-033), and archive format (F-034) were implemented in v0.2.0, but users have no CLI interface to create backups or restore from archives. Users need portable archives for backup, migration, and sharing.

## Design Approach

Expose existing export/import backends via CLI commands:

**Export Command:**

```bash
ragd export ~/backup.tar.gz              # Full export
ragd export ~/backup.tar.gz --no-embeddings  # Smaller archive
ragd export ~/ml.tar.gz --tag "topic:ml"     # Export by tag
ragd export ~/research.tar.gz --project Research  # Export by project
ragd export ~/backup.tar.gz --verbose    # Detailed progress
```

**Import Command:**

```bash
ragd import ~/backup.tar.gz              # Import with default settings
ragd import ~/backup.tar.gz --dry-run    # Validate only
ragd import ~/backup.tar.gz --overwrite  # Replace existing documents
ragd import ~/backup.tar.gz --skip-conflicts  # Skip duplicates
ragd import ~/backup.tar.gz --verbose    # Detailed progress
```

## Implementation Tasks

- [x] Add `export_command()` wrapping ExportEngine
- [x] Add `import_command()` wrapping ImportEngine
- [x] Support `--no-embeddings` for smaller archives
- [x] Support `--tag` and `--project` filters for selective export
- [x] Support `--dry-run` for validation without import
- [x] Support `--overwrite` and `--skip-conflicts` for conflict handling
- [x] Support `--verbose` for detailed progress
- [x] Support JSON output format
- [x] Export commands from CLI module

## Success Criteria

- [x] Users can export knowledge base to archive
- [x] Users can import from archive
- [x] Filtering by tag/project works
- [x] Dry-run validation available
- [x] Conflict handling options work
- [x] All existing tests pass

## Dependencies

- [F-032: Export Engine](./F-032-export-engine.md) - ExportEngine backend
- [F-033: Import Engine](./F-033-import-engine.md) - ImportEngine backend
- [F-034: Archive Format](./F-034-archive-format.md) - Archive specification

## Technical Notes

**Archive Format:**

Archives are `.tar.gz` files containing:
- `manifest.json`: Archive metadata and checksums
- `documents/`: Document records as JSON
- `chunks/`: Chunk data as JSON
- `embeddings/`: Embedding vectors (optional, Parquet format)

**Conflict Resolution:**

```python
class ConflictResolution(Enum):
    SKIP = "skip"       # Skip conflicting documents
    OVERWRITE = "overwrite"  # Replace existing
    FAIL = "fail"       # Abort on conflict (default)
```

## Related Documentation

- [F-032: Export Engine](./F-032-export-engine.md)
- [F-033: Import Engine](./F-033-import-engine.md)
- [F-034: Archive Format](./F-034-archive-format.md)
- [v0.2.6-v0.2.9 Milestone](../../milestones/v0.2.6-v0.2.9.md)

---

**Status**: Completed
