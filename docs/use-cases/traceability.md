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
| **Tutorial** | [Getting Started: Index Your First Document](../tutorials/getting-started.md) |

### UC-002: Search Knowledge

| Aspect | Reference |
|--------|-----------|
| **Use Case** | [UC-002-search-knowledge.md](./briefs/UC-002-search-knowledge.md) |
| **Milestone** | v0.1 |
| **Features** | F-005, F-006, F-009 |
| **Tutorial** | [Getting Started: Search Your Documents](../tutorials/getting-started.md) |

### UC-003: View System Status

| Aspect | Reference |
|--------|-----------|
| **Use Case** | [UC-003-view-system-status.md](./briefs/UC-003-view-system-status.md) |
| **Milestone** | v0.1 |
| **Features** | F-007, F-008 |
| **Tutorial** | [Getting Started: Check Status](../tutorials/getting-started.md) |

### UC-004: Process Messy PDFs

| Aspect | Reference |
|--------|-----------|
| **Use Case** | [UC-004-process-messy-pdfs.md](./briefs/UC-004-process-messy-pdfs.md) |
| **Milestone** | v0.2 |
| **Features** | TBD (pending research) |
| **Tutorial** | [Processing Difficult PDFs](../tutorials/messy-pdfs.md) |

### UC-005: Manage Metadata

| Aspect | Reference |
|--------|-----------|
| **Use Case** | [UC-005-manage-metadata.md](./briefs/UC-005-manage-metadata.md) |
| **Milestone** | v0.2 |
| **Features** | TBD (pending research) |
| **Tutorial** | [Organising Your Knowledge Base](../tutorials/metadata-management.md) |

### UC-006: Export & Backup

| Aspect | Reference |
|--------|-----------|
| **Use Case** | [UC-006-export-backup.md](./briefs/UC-006-export-backup.md) |
| **Milestone** | v0.2 |
| **Features** | TBD (pending research) |
| **Tutorial** | [Backing Up Your Data](../tutorials/backup-restore.md) |

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
| F-008 | Health Checks | UC-003 | v0.1 |
| F-009 | Citation Output | UC-002 | v0.1 |

### v0.2 Features (Pending Research)

Features for UC-004 (Process Messy PDFs), UC-005 (Manage Metadata), and UC-006 (Export & Backup) are pending research. Feature numbers will be assigned once specifications are complete.

See: [State-of-the-Art RAG Research](../development/research/state-of-the-art-rag.md)

---

## Validation Status

| Use Case | Features Spec'd | Tutorial Written | Acceptance Tests |
|----------|-----------------|------------------|------------------|
| UC-001 | ✅ F-001 to F-004 | ⏳ Pending | ⏳ Pending |
| UC-002 | ✅ F-005, F-006, F-009 | ⏳ Pending | ⏳ Pending |
| UC-003 | ✅ F-007, F-008 | ⏳ Pending | ⏳ Pending |
| UC-004 | ⏳ Research needed | ⏳ Pending | ⏳ Pending |
| UC-005 | ⏳ Research needed | ⏳ Pending | ⏳ Pending |
| UC-006 | ⏳ Research needed | ⏳ Pending | ⏳ Pending |

---
