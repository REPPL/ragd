# Use Cases

User journey specifications for ragd.

## Purpose

Use cases define **what users want to accomplish** with ragd. They are the first layer of the hybrid specification approach:

```
Layer 1: USE CASES (Why) ← You are here
    ↓ derive
Layer 2: FEATURE SPECS (What)
    ↓ validate
Layer 3: TUTORIALS (How users experience it)
```

## Use Case Index

### P0 - Must Have (v0.1-v0.2)

| ID | Use Case | Priority | Milestone |
|----|----------|----------|-----------|
| [UC-001](./briefs/UC-001-index-documents.md) | Index Documents | P0 | v0.1 |
| [UC-002](./briefs/UC-002-search-knowledge.md) | Search Knowledge | P0 | v0.1 |
| [UC-003](./briefs/UC-003-view-system-status.md) | View System Status | P0 | v0.1 |
| [UC-004](./briefs/UC-004-process-messy-pdfs.md) | Process Messy PDFs | P0 | v0.2 |
| [UC-005](./briefs/UC-005-manage-metadata.md) | Manage Metadata | P0 | v0.2 |
| [UC-006](./briefs/UC-006-export-backup.md) | Export & Backup | P0 | v0.2 |

### P1 - Should Have (v0.3-v0.5)

| ID | Use Case | Priority | Milestone |
|----|----------|----------|-----------|
| UC-007 | Advanced Search | P1 | v0.3 |
| UC-008 | Search with Images | P1 | v0.4 |
| UC-009 | Chat with Context | P1 | v0.5 |

### P2 - Could Have (v0.6-v1.0)

| ID | Use Case | Priority | Milestone |
|----|----------|----------|-----------|
| UC-010 | Manage Storage Backends | P2 | v0.6 |
| UC-011 | Protect Privacy | P2 | v0.7 |
| UC-012 | Switch Personas | P2 | v0.8 |
| UC-013 | Upload via Web | P2 | v1.0 |

## Directory Contents

| Directory | Purpose |
|-----------|---------|
| [briefs/](./briefs/) | Lightweight use case specifications |
| [traceability.md](./traceability.md) | Use case → feature mapping |

## Use Case Template

See [briefs/README.md](./briefs/README.md) for the use case brief template.

## What Belongs Here

- Use case briefs (user journeys)
- Traceability matrices
- Actor definitions
- Priority rankings

## What Doesn't Belong Here

- **Feature specifications** → See `../development/features/`
- **Tutorials** → See `../tutorials/`
- **Technical architecture** → See `../development/planning/`
- **Implementation details** → See `../development/implementation/`

## Actors

| Actor | Description |
|-------|-------------|
| **End User** | Primary user wanting to query personal knowledge |
| **Power User** | User wanting advanced configuration/customisation |

## Priority Framework

| Priority | Definition | Criteria |
|----------|------------|----------|
| **P0** | Must have | Without this, ragd is not a RAG tool |
| **P1** | Should have | Users expect this functionality |
| **P2** | Could have | Differentiators, advanced features |
| **P3** | Future | Post-v1.0 enhancements |

## Related Documentation

- [Feature Specifications](../development/features/) - What we build
- [Tutorials](../tutorials/) - How users experience features
- [Milestones](../development/milestones/) - When features ship

---
