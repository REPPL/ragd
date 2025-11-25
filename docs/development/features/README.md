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

### v0.2 Features (Messy PDFs & Metadata)

| ID | Feature | Status | Use Case |
|----|---------|--------|----------|
| F-009 | PDF Quality Detection | 📅 Planned | UC-004 |
| F-010 | Docling Integration | 📅 Planned | UC-004 |
| F-011 | OCR Pipeline | 📅 Planned | UC-004 |
| F-012 | Table Extraction | 📅 Planned | UC-004 |
| F-013 | Metadata Storage | 📅 Planned | UC-005 |
| F-014 | Metadata Extraction | 📅 Planned | UC-005 |
| F-015 | Tag Management | 📅 Planned | UC-005 |
| F-016 | Export Engine | 📅 Planned | UC-006 |
| F-017 | Import Engine | 📅 Planned | UC-006 |
| F-018 | Archive Format | 📅 Planned | UC-006 |

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
