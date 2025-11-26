# F-034: Archive Format

## Overview

**Use Case**: [UC-006](../../../use-cases/briefs/UC-006-export-backup.md)
**Milestone**: v0.2
**Priority**: P1

## Problem Statement

A well-defined archive format is essential for long-term data portability and tool interoperability. Without a specification, archives become implementation details that may break with future versions.

## Design Approach

Define a versioned, self-describing archive format that can evolve while maintaining backwards compatibility.

**Format Specification v1.0:**

```
ragd-archive-v1.tar.gz
│
├── manifest.json           # REQUIRED: Archive metadata
├── config.yaml             # REQUIRED: ragd configuration snapshot
│
├── documents/              # REQUIRED: Document metadata
│   ├── index.json          # Document ID list
│   └── metadata/
│       ├── doc_001.json    # Per-document metadata
│       ├── doc_002.json
│       └── ...
│
├── chunks/                 # REQUIRED: Chunk data
│   ├── index.json          # Chunk ID list with doc references
│   └── data/
│       ├── doc_001/
│       │   ├── chunk_001.json
│       │   └── chunk_002.json
│       └── doc_002/
│           └── ...
│
├── embeddings/             # OPTIONAL: Vector embeddings
│   └── embeddings.parquet  # Columnar format for efficiency
│
└── checksums.sha256        # REQUIRED: Integrity verification
```

## Implementation Tasks

- [ ] Document archive format specification (this document)
- [ ] Implement manifest schema validation
- [ ] Implement config.yaml schema
- [ ] Implement document metadata schema
- [ ] Implement chunk data schema
- [ ] Implement embedding storage format (Parquet)
- [ ] Create checksum generation and verification
- [ ] Add format version detection
- [ ] Document migration paths for future versions

## Success Criteria

- [ ] Format specification documented and versioned
- [ ] Archives self-describing (version in manifest)
- [ ] Checksums verify archive integrity
- [ ] Format supports incremental evolution
- [ ] Documentation enables third-party tool integration

## Dependencies

- [F-032: Export Engine](./F-032-export-engine.md) - Creates archives
- [F-033: Import Engine](./F-033-import-engine.md) - Reads archives

## Technical Notes

**Manifest Schema (manifest.json):**
```json
{
  "$schema": "ragd-archive-v1",
  "version": "1.0",
  "created_at": "2024-01-15T10:30:00Z",
  "ragd_version": "0.2.0",

  "statistics": {
    "document_count": 150,
    "chunk_count": 2340,
    "total_size_bytes": 52428800
  },

  "embeddings": {
    "included": true,
    "model": "voyage-3",
    "dimensions": 1024,
    "format": "parquet"
  },

  "compression": "gzip",

  "filters": {
    "tags": ["work", "project-alpha"],
    "date_from": null,
    "date_to": null
  }
}
```

**Document Metadata Schema:**
```json
{
  "id": "doc_001",
  "dc_title": "Q3 Financial Report",
  "dc_creator": ["Jane Smith"],
  "dc_date": "2024-01-15",
  "dc_subject": ["finance", "quarterly"],
  "ragd_source_path": "~/Documents/reports/q3-2024.pdf",
  "ragd_source_hash": "sha256:abc123...",
  "ragd_tags": ["work", "finance"],
  "ragd_ingestion_date": "2024-01-20T14:30:00Z",
  "ragd_chunk_count": 45
}
```

**Chunk Data Schema:**
```json
{
  "id": "chunk_001",
  "document_id": "doc_001",
  "text": "The quarterly revenue increased by 15%...",
  "page_numbers": [5, 6],
  "section": "Revenue Analysis",
  "char_start": 1024,
  "char_end": 2048,
  "metadata": {
    "has_table": false,
    "has_code": false
  }
}
```

**Version Evolution:**

| Version | Changes |
|---------|---------|
| 1.0 | Initial format |
| 1.1 (future) | Add provenance tracking |
| 2.0 (future) | Breaking changes (new schema) |

**Backwards Compatibility:**
- Minor versions (1.x) maintain backwards compatibility
- Major versions (2.x) may break compatibility
- Import engine checks version before processing
- Migration tools provided for major version upgrades

## Related Documentation

- [F-032: Export Engine](./F-032-export-engine.md)
- [F-033: Import Engine](./F-033-import-engine.md)
- [UC-006: Export & Backup](../../../use-cases/briefs/UC-006-export-backup.md)

---

**Status**: Planned
