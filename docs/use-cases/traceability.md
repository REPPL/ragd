# Use Case Traceability Matrix

Mapping use cases to features and tutorials for ragd.

## Purpose

This matrix ensures every use case is:
1. Implemented via features
2. Validated via tutorials
3. Tested via acceptance criteria

---

## P0 Use Cases (v0.1-v0.2)

### UC-001: Index Documents

| Aspect | Reference |
|--------|-----------|
| **Use Case** | [UC-001-index-documents.md](./briefs/UC-001-index-documents.md) |
| **Milestone** | v0.1 |
| **Features** | F-001, F-002, F-003, F-004 |
| **Tutorial** | [Getting Started: Index Your First Document](../tutorials/01-getting-started.md) |

### UC-002: Search Knowledge

| Aspect | Reference |
|--------|-----------|
| **Use Case** | [UC-002-search-knowledge.md](./briefs/UC-002-search-knowledge.md) |
| **Milestone** | v0.1 |
| **Features** | F-005, F-006, F-009 |
| **Tutorial** | [Getting Started: Search Your Documents](../tutorials/01-getting-started.md) |

### UC-003: View System Status

| Aspect | Reference |
|--------|-----------|
| **Use Case** | [UC-003-view-system-status.md](./briefs/UC-003-view-system-status.md) |
| **Milestone** | v0.1 |
| **Features** | F-007, F-035 |
| **Tutorial** | [Getting Started: Check Status](../tutorials/01-getting-started.md) |

### UC-004: Process Messy PDFs

| Aspect | Reference |
|--------|-----------|
| **Use Case** | [UC-004-process-messy-pdfs.md](./briefs/UC-004-process-messy-pdfs.md) |
| **Milestone** | v0.2 |
| **Features** | F-025, F-026, F-027, F-028 |
| **Tutorial** | [Processing Difficult PDFs](../tutorials/processing-difficult-pdfs.md) |

### UC-005: Manage Metadata

| Aspect | Reference |
|--------|-----------|
| **Use Case** | [UC-005-manage-metadata.md](./briefs/UC-005-manage-metadata.md) |
| **Milestone** | v0.2 |
| **Features** | F-029, F-030, F-031 |
| **Tutorial** | [Organising Your Knowledge Base](../tutorials/organising-knowledge-base.md) |

### UC-006: Export & Backup

| Aspect | Reference |
|--------|-----------|
| **Use Case** | [UC-006-export-backup.md](./briefs/UC-006-export-backup.md) |
| **Milestone** | v0.2 |
| **Features** | F-032, F-033, F-034 |
| **Tutorial** | [Backing Up Your Data](../tutorials/backing-up-data.md) |

---

## Feature Index

Quick reference for all features derived from P0 use cases:

### v0.1 Features (Spec'd)

| ID | Feature | Use Case | Milestone |
|----|---------|----------|-----------|
| F-001 | Document Ingestion Pipeline | UC-001 | v0.1 |
| F-002 | Text Extraction | UC-001 | v0.1 |
| F-003 | Chunking Engine | UC-001 | v0.1 |
| F-004 | Embedding Generation | UC-001 | v0.1 |
| F-005 | Semantic Search | UC-002 | v0.1 |
| F-006 | Result Formatting | UC-002 | v0.1 |
| F-007 | Status Dashboard | UC-003 | v0.1 |
| F-035 | Health Check Command | UC-003 | v0.1 |
| F-009 | Citation Output | UC-002 | v0.1 |

### v0.2 Features (Complete)

| ID | Feature | Use Case | Milestone |
|----|---------|----------|-----------|
| F-025 | PDF Quality Detection | UC-004 | v0.2 |
| F-026 | Docling Integration | UC-004 | v0.2 |
| F-027 | OCR Pipeline | UC-004 | v0.2 |
| F-028 | Table Extraction | UC-004 | v0.2 |
| F-029 | Metadata Storage | UC-005 | v0.2 |
| F-030 | Metadata Extraction | UC-005 | v0.2 |
| F-031 | Tag Management | UC-005 | v0.2 |
| F-032 | Export Engine | UC-006 | v0.2 |
| F-033 | Import Engine | UC-006 | v0.2 |
| F-034 | Archive Format | UC-006 | v0.2 |
| F-037 | Watch Folder Auto-Indexing | - | v0.2 |
| F-038 | Web Archive Support | - | v0.2 |

---

## Validation Status

| Use Case | Features Spec'd | Tutorial | Tests |
|----------|-----------------|----------|-------|
| UC-001 | ✅ F-001 to F-004 | ✅ | ✅ Unit + Integration |
| UC-002 | ✅ F-005, F-006, F-009 | ✅ | ✅ Unit + Integration |
| UC-003 | ✅ F-007, F-035 | ✅ | ✅ Unit + Integration |
| UC-004 | ✅ F-025 to F-028 | ✅ | ✅ Unit + Integration |
| UC-005 | ✅ F-029 to F-031 | ✅ | ✅ Unit + Integration |
| UC-006 | ✅ F-032 to F-034 | ✅ | ✅ Unit + Integration |

---

## Related Documentation

- [Feature Specifications](../development/features/)
- [Use Case Briefs](./briefs/)
- [Tutorials](../tutorials/)
