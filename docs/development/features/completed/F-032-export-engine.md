# F-032: Export Engine

## Overview

**Use Case**: [UC-006](../../../use-cases/briefs/UC-006-export-backup.md)
**Milestone**: v0.2
**Priority**: P0

## Problem Statement

Users need to backup their knowledge base for disaster recovery, migrate to new machines, or share with others. Without export functionality, data is trapped in ragd's internal format with no portability.

## Design Approach

Implement a comprehensive export engine that creates portable archives containing all data needed to fully restore a ragd knowledge base.

**Export Contents:**

| Component | Format | Purpose |
|-----------|--------|---------|
| Documents metadata | JSON | Document properties, tags |
| Chunks | JSON | Text content, chunk metadata |
| Embeddings | NumPy/Parquet | Vector data |
| Configuration | YAML | Settings, model info |
| Manifest | JSON | Archive metadata, checksums |

**Archive Structure:**
```
ragd-export-2024-01-15.tar.gz
├── manifest.json           # Archive metadata, version, checksums
├── config.yaml             # ragd configuration
├── documents/
│   └── documents.json      # All document metadata
├── chunks/
│   └── chunks.json         # All chunk data
├── embeddings/
│   └── embeddings.parquet  # Vector embeddings
└── checksums.sha256        # Integrity verification
```

## Implementation Tasks

- [ ] Create export archive format specification
- [ ] Implement document metadata export (JSON)
- [ ] Implement chunk data export (JSON)
- [ ] Implement embedding export (Parquet for efficiency)
- [ ] Create archive manifest with version and checksums
- [ ] Implement `ragd export <path>` CLI command
- [ ] Add progress feedback for large exports
- [ ] Support partial export (by tag, date, project)
- [ ] Add compression options (gzip, zstd)

## Success Criteria

- [ ] Full knowledge base exportable to single archive
- [ ] Archive is portable across machines
- [ ] Export includes all data needed for full restore
- [ ] Progress shown for large exports
- [ ] Partial export by filter supported
- [ ] Archive integrity verifiable via checksums

## Dependencies

- [F-029: Metadata Storage](./F-029-metadata-storage.md) - Source of document metadata
- [F-001: Document Ingestion](./F-001-document-ingestion.md) - Source of chunk data

## Technical Notes

**Manifest Format:**
```json
{
  "version": "1.0",
  "ragd_version": "0.2.0",
  "created_at": "2024-01-15T10:30:00Z",
  "document_count": 150,
  "chunk_count": 2340,
  "embedding_model": "voyage-3",
  "embedding_dimensions": 1024,
  "compression": "gzip",
  "checksums": {
    "documents.json": "sha256:abc123...",
    "chunks.json": "sha256:def456...",
    "embeddings.parquet": "sha256:ghi789..."
  }
}
```

**CLI Usage:**
```bash
# Full export
ragd export ~/backup/ragd-backup.tar.gz

# Export specific project
ragd export ~/backup/project-alpha.tar.gz --project alpha

# Export by date range
ragd export ~/backup/recent.tar.gz --since 2024-01-01

# Export metadata only (no embeddings)
ragd export ~/backup/metadata-only.tar.gz --metadata-only
```

**Embedding Export (Parquet):**
```python
import pyarrow as pa
import pyarrow.parquet as pq

# Efficient columnar storage for embeddings
table = pa.table({
    "chunk_id": chunk_ids,
    "embedding": embeddings  # List of floats
})
pq.write_table(table, "embeddings.parquet", compression="zstd")
```

## Related Documentation

- [F-033: Import Engine](./F-033-import-engine.md)
- [F-034: Archive Format](./F-034-archive-format.md)
- [UC-006: Export & Backup](../../../use-cases/briefs/UC-006-export-backup.md)

---

**Status**: Completed
