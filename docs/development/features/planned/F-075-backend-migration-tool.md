# F-075: Backend Migration Tool

## Overview

**Milestone**: v0.8 (pending ADR decision)
**Priority**: P2 (conditional)
**Status**: Pending ADR - "Dual-index vs Migration" decision

## Problem Statement

Users who have built up a knowledge base using one storage backend (e.g., ChromaDB) may want to migrate to a different backend (e.g., FAISS) without re-indexing all their documents. Re-indexing large collections is time-consuming and computationally expensive. A migration tool enables seamless backend switching while preserving all indexed data.

This feature is an alternative to the dual-index architecture approach. The ADR decision will determine which approach is implemented.

## Design Approach

### Architecture

```
Source Backend (ChromaDB)
    |
    v
Export Pipeline
    |-- Vector embeddings
    |-- Document metadata
    |-- Chunk content
    v
Intermediate Format (JSON/Parquet)
    |
    v
Import Pipeline
    |-- Validate integrity
    |-- Transform if needed
    |-- Batch insert
    v
Target Backend (FAISS)
```

### Migration Workflow

1. **Pre-flight checks**: Verify source readable, target writable, sufficient space
2. **Export**: Extract all vectors, metadata, and relationships from source
3. **Transform**: Convert data format if backends use different schemas
4. **Import**: Batch load into target backend with progress tracking
5. **Validate**: Compare checksums and counts to ensure data integrity
6. **Cleanup**: Optional removal of source data after successful migration

### CLI Interface

```bash
# Basic migration
ragd migrate --from chromadb --to faiss

# With options
ragd migrate --from chromadb --to faiss \
  --batch-size 1000 \
  --validate \
  --keep-source

# Dry run to check compatibility
ragd migrate --from chromadb --to faiss --dry-run

# Resume interrupted migration
ragd migrate --resume
```

## Implementation Tasks

- [ ] Design intermediate data format for export/import
- [ ] Implement export adapter interface
- [ ] Implement ChromaDB export adapter
- [ ] Implement FAISS export adapter
- [ ] Implement import adapter interface
- [ ] Implement ChromaDB import adapter
- [ ] Implement FAISS import adapter
- [ ] Add batch processing with progress tracking
- [ ] Implement data validation (checksums, counts)
- [ ] Add resume capability for interrupted migrations
- [ ] Create CLI `migrate` command
- [ ] Write unit tests for adapters
- [ ] Write integration tests for full migration flow
- [ ] Document migration procedures

## Success Criteria

- [ ] Can migrate from ChromaDB to FAISS
- [ ] Can migrate from FAISS to ChromaDB
- [ ] Migration preserves all vectors with < 0.001% loss
- [ ] All metadata preserved exactly
- [ ] Search results identical before and after migration
- [ ] Handles collections with 100k+ chunks
- [ ] Progress visible during migration
- [ ] Failed migrations can be resumed
- [ ] Migration completes in reasonable time (< 1 hour for 100k chunks)

## Dependencies

- [F-021: Vector Store Abstraction](../completed/F-021-vector-store-abstraction.md) - Storage adapter interfaces
- Storage adapter implementations (ChromaDB, FAISS)
- Intermediate format library (JSON, or optionally Parquet for large datasets)

## Technical Notes

### Intermediate Format

```json
{
  "version": "1.0",
  "source_backend": "chromadb",
  "export_timestamp": "2024-01-15T10:30:00Z",
  "metadata": {
    "total_documents": 42,
    "total_chunks": 1247,
    "embedding_model": "all-MiniLM-L6-v2",
    "embedding_dimension": 384
  },
  "chunks": [
    {
      "id": "chunk_001",
      "document_id": "doc_001",
      "content": "...",
      "embedding": [0.1, 0.2, ...],
      "metadata": {
        "page": 5,
        "source_file": "report.pdf"
      }
    }
  ]
}
```

### Configuration

```yaml
migration:
  batch_size: 1000          # Chunks per batch
  validate: true            # Run validation after migration
  keep_source: false        # Delete source after success
  checkpoint_interval: 100  # Batches between checkpoints
  format: json              # json or parquet
```

### Error Handling

| Error | Recovery |
|-------|----------|
| Source connection failed | Retry with backoff |
| Target write failed | Checkpoint and resume |
| Validation mismatch | Report discrepancies, option to force |
| Disk space exhausted | Pause, alert user, resume when cleared |

## Related Documentation

- [F-021: Vector Store Abstraction](../completed/F-021-vector-store-abstraction.md) - Foundation for this feature
- [v0.8.0 Milestone](../../milestones/v0.8.0.md) - Release planning
- ADR: Dual-index vs Migration (pending)

---
