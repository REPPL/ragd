# Development Documentation

Documentation for contributors and developers.

## Current Status

| Area | Status |
|------|--------|
| Use Cases | 6 P0 briefs defined |
| Features | 96 features complete, 11 planned |
| Tutorials | Getting Started + 5 tutorials |
| Milestone | v0.9.6 released (preparing v1.0.0) |
| ADRs | 32 architecture decisions |

## Structure

| Directory | Purpose | Timeline |
|-----------|---------|----------|
| [lineage/](./lineage/) | Knowledge transfer from ragged | Reference |
| [research/](./research/) | State-of-the-art techniques | Reference |
| [features/](./features/) | Feature-centric roadmap | Current/Future |
| [milestones/](./milestones/) | Release planning | Future |
| [implementation/](./implementation/) | What was built | Past |
| [process/](./process/) | How it was built | Past |
| [decisions/](./decisions/) | Architecture decisions | All |

## Specification Approach

ragd uses a hybrid specification approach (see [ADR-0004](./decisions/adrs/0004-hybrid-specification-approach.md)):

```
Layer 1: USE CASES (Why)
    ↓ derive
Layer 2: FEATURE SPECS (What)
    ↓ validate
Layer 3: TUTORIALS (How users experience it)
```

## Quick Links

### Planning
- [Use Cases](../use-cases/) - What users want to accomplish
- [Active Features](./features/active/)
- [Planned Features](./features/planned/)
- [Milestones](./milestones/)

### v0.9.6 (Latest Release)
- [v0.9.6 Milestone](./milestones/v0.9.6.md)
- [v0.9.6 Implementation](./implementation/v0.9.6.md)
- [F-098: Advanced HTML Engine](./features/completed/F-098-advanced-html-engine.md)
- [F-099: PDF Layout Intelligence](./features/completed/F-099-pdf-layout-intelligence.md)
- [F-105: Indexing Self-Evaluation](./features/completed/F-105-indexing-self-evaluation.md)
- [F-111: Error Logging & Recovery](./features/completed/F-111-error-logging-recovery.md)
- [F-112: Operation Audit Trail](./features/completed/F-112-operation-audit-trail.md)
- [F-114: CLI User Feedback](./features/completed/F-114-cli-user-feedback.md)
- [F-115: Source Quality Scoring](./features/completed/F-115-source-quality-scoring.md)
- [F-118: Dry-Run Mode](./features/completed/F-118-dry-run-mode.md)

### v0.9.5 (Released)
- [v0.9.5 Milestone](./milestones/v0.9.5.md)
- [v0.9.5 Implementation](./implementation/v0.9.5.md)
- [F-110: Structured Logging](./features/completed/F-110-structured-logging.md)
- [F-113: Exit Codes](./features/completed/F-113-exit-codes.md)
- [F-116: Index Integrity](./features/completed/F-116-index-integrity.md)
- [F-117: Self-Healing](./features/completed/F-117-self-healing.md)

### v0.9.1 (Released)
- [v0.9.1 Milestone](./milestones/v0.9.1.md)
- [v0.9.1 Implementation](./implementation/v0.9.1.md)
- [F-106: Indexing Documentation](./features/completed/F-106-indexing-documentation.md)
- [F-107: CLI Refinements](./features/completed/F-107-cli-refinements.md)
- [F-108: Config Refinements](./features/completed/F-108-config-refinements.md)
- [F-109: Index Statistics](./features/completed/F-109-index-statistics.md)

### v0.9.0 (Released)
- [v0.9.0 Milestone](./milestones/v0.9.0.md)
- [v0.9.0 Implementation](./implementation/v0.9.0.md)
- [F-100: New File Types](./features/completed/F-100-new-file-types.md)
- [F-101: Smart Chunking v2](./features/completed/F-101-smart-chunking-v2.md)
- [F-102: Indexing Resume](./features/completed/F-102-indexing-resume.md)
- [F-103: Content Hashing](./features/completed/F-103-content-hashing.md)
- [F-104: Duplicate Detection](./features/completed/F-104-duplicate-detection.md)

### v0.8.x Series (Released)
- [v0.8.7 Milestone](./milestones/v0.8.7.md) - CLI Polish & Documentation
- [v0.8.6 Milestone](./milestones/v0.8.6.md) - Contextual Retrieval v2
- [v0.8.5 Milestone](./milestones/v0.8.5.md) - Dual-Index Architecture
- [v0.8.2 Milestone](./milestones/v0.8.2.md) - Retrieval Enhancement
- [v0.8.1 Milestone](./milestones/v0.8.1.md) - Intelligent Tagging
- [v0.8.0 Milestone](./milestones/v0.8.0.md) - Metadata Foundation

### v0.7.0 (Released)
- [v0.7.0 Milestone](./milestones/v0.7.0.md)
- [v0.7.0 Implementation](./implementation/v0.7.0.md)
- [F-015: Database Encryption](./features/completed/F-015-database-encryption.md)
- [F-016: Session Management](./features/completed/F-016-session-management.md)
- [F-017: Secure Deletion](./features/completed/F-017-secure-deletion.md)
- [F-023: PII Detection](./features/completed/F-023-pii-detection.md)

### Earlier Releases
- [v0.6.5 Milestone](./milestones/v0.6.5.md) - RAGAS & Polish
- [v0.6.0 Milestone](./milestones/v0.6.0.md) - Vector Store Abstraction
- [v0.5.0 Milestone](./milestones/v0.5.0.md) - LLM Integration
- [v0.4.0 Milestone](./milestones/v0.4.0.md) - Multi-Modal
- [v0.3.0 Milestone](./milestones/v0.3.0.md) - Advanced Search
- [v0.2.0 Milestone](./milestones/v0.2.0.md) - Messy PDFs
- [v0.1.0 Milestone](./milestones/v0.1.0.md) - Core RAG Pipeline

### History
- [Completed Features](./features/completed/)
- [Implementation Records](./implementation/)
- [Development Logs](./process/devlogs/)

### Knowledge Transfer
- [ragged Analysis](./lineage/ragged-analysis.md)
- [Feature Mapping](./lineage/feature-mapping.md)
- [Acknowledgements](./lineage/acknowledgements.md)

### Research
- [State-of-the-Art RAG](./research/state-of-the-art-rag.md)
- [Privacy-Preserving Architecture](./research/state-of-the-art-privacy.md)

### Decisions
- [ADR-0001: Typer + Rich CLI](./decisions/adrs/0001-use-typer-rich-cli.md)
- [ADR-0002: ChromaDB Vector Store](./decisions/adrs/0002-chromadb-vector-store.md)
- [ADR-0003: Privacy-First](./decisions/adrs/0003-privacy-first-architecture.md)
- [ADR-0004: Hybrid Specification](./decisions/adrs/0004-hybrid-specification-approach.md)

## AI Contributions

This project is developed with AI assistance. See [AI Contributions](./ai-contributions.md) for transparency documentation.

---

## Related Documentation

- [Documentation Hub](../README.md)

