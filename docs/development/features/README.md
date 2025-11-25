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
| [F-001](./planned/F-001-document-ingestion.md) | Document Ingestion Pipeline | 📅 Planned | UC-001 |
| [F-002](./planned/F-002-text-extraction.md) | Text Extraction | 📅 Planned | UC-001 |
| [F-003](./planned/F-003-chunking-engine.md) | Chunking Engine | 📅 Planned | UC-001 |
| [F-004](./planned/F-004-embedding-generation.md) | Embedding Generation | 📅 Planned | UC-001 |
| [F-005](./planned/F-005-semantic-search.md) | Semantic Search | 📅 Planned | UC-002 |
| [F-006](./planned/F-006-result-formatting.md) | Result Formatting | 📅 Planned | UC-002 |
| [F-007](./planned/F-007-status-dashboard.md) | Status Dashboard | 📅 Planned | UC-003 |
| [F-008](./planned/F-008-health-checks.md) | Health Checks | 📅 Planned | UC-003 |
| [F-009](./planned/F-009-citation-output.md) | Citation Output | 📅 Planned | UC-002 |

### v0.3 Features (Advanced Retrieval)

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-010](./planned/F-010-contextual-retrieval.md) | Contextual Retrieval | 📅 Planned | ADR-0007 |
| [F-011](./planned/F-011-late-chunking.md) | Late Chunking | 📅 Planned | ADR-0007 |
| [F-012](./planned/F-012-hybrid-search.md) | Hybrid Search | 📅 Planned | ADR-0007 |

### v0.5 Features (Chat & Evaluation)

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-013](./planned/F-013-ragas-evaluation.md) | RAGAS Evaluation | 📅 Planned | ADR-0008 |
| [F-014](./planned/F-014-agentic-rag.md) | Agentic RAG | 📅 Planned | State-of-the-Art |

### v0.7 Features (Privacy & Security)

| ID | Feature | Status | Research |
|----|---------|--------|----------|
| [F-015](./planned/F-015-database-encryption.md) | Database Encryption | 📅 Planned | ADR-0009 |
| [F-016](./planned/F-016-session-management.md) | Session Management | 📅 Planned | ADR-0009 |
| [F-017](./planned/F-017-secure-deletion.md) | Secure Deletion | 📅 Planned | ADR-0009 |
| [F-018](./planned/F-018-data-tiers.md) | Data Sensitivity Tiers | 📅 Planned | ADR-0010 |

## Workflow

1. **Plan:** Create feature document in `planned/`
2. **Start:** Move to `active/` when development begins
3. **Complete:** Move to `completed/` when feature is released

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
