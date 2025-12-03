# Feature Specifications

Feature-centric roadmap for ragd development.

## Purpose

Features are the primary unit of work. Each feature specification describes:
- **What** the feature does
- **Why** it matters
- **How** it will be implemented
- **When** it's considered done

## Status by Location

| Directory | Status | Meaning |
|-----------|--------|---------|
| [active/](./active/) | 🔄 In Progress | Currently being implemented |
| [planned/](./planned/) | 📅 Queued | Designed, awaiting implementation |
| [completed/](./completed/) | ✅ Done | Shipped and documented |

## Feature Index

### v0.1 Features (Core RAG)

| ID | Feature | Status | Use Case |
|----|---------|--------|----------|
| [F-001](./completed/F-001-document-ingestion.md) | Document Ingestion Pipeline | ✅ Complete | UC-001 |
| [F-002](./completed/F-002-text-extraction.md) | Text Extraction | ✅ Complete | UC-001 |
| [F-003](./completed/F-003-chunking-engine.md) | Chunking Engine | ✅ Complete | UC-001 |
| [F-004](./completed/F-004-embedding-generation.md) | Embedding Generation | ✅ Complete | UC-001 |
| [F-005](./completed/F-005-semantic-search.md) | Semantic Search | ✅ Complete | UC-002 |
| [F-006](./completed/F-006-result-formatting.md) | Result Formatting | ✅ Complete | UC-002 |
| [F-007](./completed/F-007-status-dashboard.md) | Status Dashboard | ✅ Complete | UC-003 |
| [F-035](./completed/F-035-health-check.md) | Health Check Command | ✅ Complete | UC-003 |
| [F-036](./completed/F-036-guided-setup.md) | Guided Setup | ✅ Complete | - |

### v0.2 Features (Killer Feature)

#### PDF Processing

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-025](./completed/F-025-pdf-quality-detection.md) | PDF Quality Detection | ✅ Complete | [State-of-the-Art PDF Processing](../research/state-of-the-art-pdf-processing.md) |
| [F-026](./completed/F-026-docling-integration.md) | Docling Integration | ✅ Complete | [State-of-the-Art PDF Processing](../research/state-of-the-art-pdf-processing.md) |
| [F-027](./completed/F-027-ocr-pipeline.md) | OCR Pipeline | ✅ Complete | [State-of-the-Art PDF Processing](../research/state-of-the-art-pdf-processing.md) |
| [F-028](./completed/F-028-table-extraction.md) | Table Extraction | ✅ Complete | [State-of-the-Art PDF Processing](../research/state-of-the-art-pdf-processing.md) |

#### Metadata Management

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-029](./completed/F-029-metadata-storage.md) | Metadata Storage | ✅ Complete | [State-of-the-Art Metadata](../research/state-of-the-art-metadata.md) |
| [F-030](./completed/F-030-metadata-extraction.md) | Metadata Extraction | ✅ Complete | [State-of-the-Art Metadata](../research/state-of-the-art-metadata.md) |
| [F-031](./completed/F-031-tag-management.md) | Tag Management | ✅ Complete | [State-of-the-Art Metadata](../research/state-of-the-art-metadata.md) |

#### Export & Backup

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-032](./completed/F-032-export-engine.md) | Export Engine | ✅ Complete | - |
| [F-033](./completed/F-033-import-engine.md) | Import Engine | ✅ Complete | - |
| [F-034](./completed/F-034-archive-format.md) | Archive Format | ✅ Complete | - |

#### Watch Folder

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-037](./completed/F-037-watch-folder.md) | Watch Folder Auto-Indexing | ✅ Complete | [State-of-the-Art RAG Landscape](../research/state-of-the-art-rag-landscape.md) |

#### Web Archive

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-038](./completed/F-038-web-archive-support.md) | Web Archive Support | ✅ Complete | [State-of-the-Art HTML Processing](../research/state-of-the-art-html-processing.md) |

### v0.3 Features (Advanced Retrieval)

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-009](./completed/F-009-citation-output.md) | Citation Output | ✅ Complete | - |
| [F-010](./completed/F-010-contextual-retrieval.md) | Contextual Retrieval | ✅ Complete | ADR-0007 |
| [F-011](./completed/F-011-late-chunking.md) | Late Chunking | ✅ Complete | ADR-0007 |
| [F-012](./completed/F-012-hybrid-search.md) | Hybrid Search | ✅ Complete | ADR-0007 |

### v0.4 Features (Multi-Modal)

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-019](./completed/F-019-multi-modal-support.md) | Multi-Modal Support | ✅ Complete | State-of-the-Art Multi-Modal |

### v0.5 Features (Chat & Evaluation)

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-013](./completed/F-013-ragas-evaluation.md) | RAGAS Evaluation | ✅ Complete | ADR-0008 |
| [F-014](./completed/F-014-agentic-rag.md) | Agentic RAG | ✅ Complete | State-of-the-Art RAG |
| [F-020](./completed/F-020-ollama-llm-integration.md) | Ollama LLM Integration | ✅ Complete | State-of-the-Art Local RAG |
| [F-055](./completed/F-055-multi-model-orchestration.md) | Multi-Model Orchestration | ✅ Complete | [State-of-the-Art Multi-Model RAG](../research/state-of-the-art-multi-model-rag.md) |

### v0.6.0 Features (Storage)

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-021](./completed/F-021-vector-store-abstraction.md) | Vector Store Abstraction | ✅ Complete | ADR-0002 |
| [F-070](./completed/F-070-backend-recommendation.md) | Backend Recommendation | ✅ Complete | - |
| [F-071](./completed/F-071-metadata-proxy-layer.md) | Metadata Proxy Layer | ✅ Complete | - |
| [F-072](./completed/F-072-backend-health-checks.md) | Backend Health Checks | ✅ Complete | - |
| [F-073](./completed/F-073-performance-profiler.md) | Performance Profiler | ✅ Complete | - |
| [F-074](./completed/F-074-model-recommendation.md) | Model Recommendation | ✅ Complete | - |

### v0.6.5 Features (Polish & Stability)

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-076](./completed/F-076-ragas-evaluation-metrics.md) | RAGAS Evaluation Metrics | ✅ Complete | - |
| [F-077](./completed/F-077-cli-visual-polish.md) | CLI Visual Polish | ✅ Complete | - |
| [F-078](./completed/F-078-configuration-validation.md) | Configuration Validation | ✅ Complete | - |
| [F-079](./completed/F-079-dependency-error-handling.md) | Dependency Error Handling | ✅ Complete | - |

### v0.7 Features (Privacy & Security)

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-015](./planned/F-015-database-encryption.md) | Database Encryption | 📅 Planned | ADR-0009 |
| [F-016](./planned/F-016-session-management.md) | Session Management | 📅 Planned | ADR-0009 |
| [F-017](./planned/F-017-secure-deletion.md) | Secure Deletion | 📅 Planned | ADR-0009 |
| [F-018](./planned/F-018-data-tiers.md) | Data Sensitivity Tiers | 📅 Planned | ADR-0010 |
| [F-023](./planned/F-023-pii-detection.md) | PII Detection | 📅 Planned | State-of-the-Art Privacy |

### v0.8 Features (Intelligence)

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-022](./planned/F-022-knowledge-graph.md) | Knowledge Graph Integration | 📅 Planned | State-of-the-Art Knowledge Graphs |

### v1.0 Features (Platform)

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-024](./planned/F-024-basic-webui.md) | Basic WebUI | 📅 Planned | State-of-the-Art User Interfaces |
| [F-056](./planned/F-056-specialised-task-models.md) | Specialised Task Models | 📅 Planned | [State-of-the-Art Multi-Model RAG](../research/state-of-the-art-multi-model-rag.md) |
| [F-057](./planned/F-057-model-comparison.md) | Model Comparison Mode | 📅 Planned | [State-of-the-Art Multi-Model RAG](../research/state-of-the-art-multi-model-rag.md) |

### v2.0 Features (Personal Knowledge Assistant)

v2.0 transforms ragd from a document RAG system into a personal knowledge assistant with persistent memory, user profiles, and a secure personal information vault.

#### Memory Layer (v2.0-alpha)

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-040](./planned/F-040-long-term-memory.md) | Long-Term Memory Store | 📅 Planned | [State-of-the-Art Personal RAG](../research/state-of-the-art-personal-rag.md) |
| F-043 | Memory Consolidation | 📅 Planned | [State-of-the-Art Personal RAG](../research/state-of-the-art-personal-rag.md) |

#### Persona Agents (v2.0-beta)

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-041](./planned/F-041-user-profile-management.md) | User Profile Management | 📅 Planned | [State-of-the-Art Personal RAG](../research/state-of-the-art-personal-rag.md) |
| F-042 | Persona Agent System | 📅 Planned | [State-of-the-Art Personal RAG](../research/state-of-the-art-personal-rag.md) |

#### Personal Vault (v2.0)

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-044](./planned/F-044-personal-vault.md) | Personal Information Vault | 📅 Planned | [State-of-the-Art Personal RAG](../research/state-of-the-art-personal-rag.md) |

### v2.x Features (Personal Data Connectors)

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| F-045 | Browser History Connector | 📅 Planned | [State-of-the-Art Personal RAG](../research/state-of-the-art-personal-rag.md) |
| F-046 | Communication Parser | 📅 Planned | [State-of-the-Art Personal RAG](../research/state-of-the-art-personal-rag.md) |
| F-047 | Health Record Import (FHIR) | 📅 Planned | [State-of-the-Art Personal RAG](../research/state-of-the-art-personal-rag.md) |
| F-048 | Financial Data Import | 📅 Planned | [State-of-the-Art Personal RAG](../research/state-of-the-art-personal-rag.md) |

## Workflow

1. **Plan:** Create feature document in `planned/`
2. **Start:** Move to `active/` when development begins
3. **Complete:** Move to `completed/` when feature is released

## Feature Numbering Convention

Features are numbered sequentially with milestone-based ranges:

| Range | Milestone | Theme |
|-------|-----------|-------|
| F-001 to F-007, F-035-F-036 | v0.1 | Core RAG |
| F-025 to F-034, F-037-F-038 | v0.2 | Killer Feature (PDFs, Metadata, Export, Watch, Web) |
| F-009 to F-012 | v0.3 | Advanced Search (Citation, Contextual, Late Chunking, Hybrid) |
| F-019 | v0.4 | Multi-Modal |
| F-013, F-014, F-020, F-055 | v0.5 | Chat & Evaluation |
| F-021, F-070 to F-074 | v0.6.0 | Storage |
| F-076 to F-079 | v0.6.5 | Polish & Stability |
| F-015 to F-018, F-023 | v0.7 | Privacy & Security |
| F-022 | v0.8 | Intelligence |
| F-024, F-056, F-057 | v1.0+ | Platform & Multi-Model Advanced |
| F-040, F-043 | v2.0-alpha | Memory Layer |
| F-041, F-042 | v2.0-beta | Persona Agents |
| F-044 | v2.0 | Personal Vault |
| F-045 to F-048 | v2.x | Personal Data Connectors |

**Guidelines:**
- Numbers are assigned sequentially as features are designed
- A feature keeps its number even if its milestone changes
- Gaps in numbering (e.g., no F-025) are expected as features are added over time
- Use the next available number for new features

## Feature Template

```markdown
# F-NNN: [Feature Name]

## Overview

**Use Case**: [UC-NNN](../../use-cases/briefs/UC-NNN-name.md)
**Milestone**: vX.Y
**Priority**: P0 | P1 | P2

## Problem Statement

[Why this feature matters - the pain point it solves]

## Design Approach

[How we solve the problem - architecture, patterns, technologies]

## Implementation Tasks

- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

## Success Criteria

- [ ] Criterion 1 (measurable)
- [ ] Criterion 2 (measurable)

## Dependencies

- [Dependency 1]
- [Dependency 2]

## Technical Notes

[Implementation details, edge cases, considerations]

## Related Documentation

- [Link 1](./path) - Description
- [Link 2](./path) - Description

---
```

## What Belongs Here

- Feature specification documents (F-NNN-name.md)
- Technical design decisions
- Implementation task breakdowns

## What Doesn't Belong Here

- **Use case briefs** → `../../use-cases/briefs/`
- **Tutorials** → `../../tutorials/`
- **Architecture decisions** → `../decisions/adrs/`
- **Milestone planning** → `../milestones/`

## Related Documentation

- [Use Cases](../../use-cases/) - What users want to accomplish
- [Milestones](../milestones/) - When features ship
- [Tutorials](../../tutorials/) - How users experience features

---
