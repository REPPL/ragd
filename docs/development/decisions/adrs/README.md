# Architecture Decision Records (ADRs)

Lightweight documentation of significant technical decisions.

## Available ADRs

### Foundation (v0.1)

| ADR | Title | Status |
|-----|-------|--------|
| [0001](./0001-use-typer-rich-cli.md) | Use Typer + Rich for CLI | Accepted |
| [0002](./0002-chromadb-vector-store.md) | Use ChromaDB as Default Vector Store | Accepted |
| [0003](./0003-privacy-first-architecture.md) | Privacy-First Architecture | Accepted |
| [0004](./0004-hybrid-specification-approach.md) | Hybrid Specification Approach | Accepted |
| [0005](./0005-cli-design-principles.md) | CLI Design Principles | Accepted |
| [0006](./0006-citation-system.md) | Citation System Architecture | Accepted |

### Advanced Retrieval (v0.3)

| ADR | Title | Status |
|-----|-------|--------|
| [0007](./0007-advanced-retrieval-techniques.md) | Advanced Retrieval Techniques | Accepted |
| [0008](./0008-evaluation-framework.md) | Evaluation Framework (RAGAS) | Accepted |

### Platform & Infrastructure (v0.2)

| ADR | Title | Status |
|-----|-------|--------|
| [0011](./0011-hardware-detection.md) | Hardware Detection and Tier-Based Configuration | Accepted |
| [0012](./0012-distribution-strategy.md) | Package Distribution Strategy | Accepted |
| [0013](./0013-configuration-schema.md) | Configuration Schema and Management | Accepted |
| [0014](./0014-daemon-management.md) | Daemon Process Management | Accepted |
| [0015](./0015-web-archive-processing.md) | Web Archive Processing Architecture | Accepted |
| [0016](./0016-document-deduplication.md) | Document Deduplication Strategy | Accepted |
| [0017](./0017-html-to-text-conversion.md) | HTML-to-Text Conversion Strategy | Accepted |
| [0018](./0018-chunking-strategy.md) | Text Chunking Strategy | Accepted |
| [0019](./0019-pdf-processing.md) | PDF Processing Library Selection | Accepted |
| [0023](./0023-metadata-schema-evolution.md) | Metadata Schema Evolution | Accepted |
| [0024](./0024-optional-dependencies.md) | Optional Dependencies Strategy | Accepted |
| [0025](./0025-advanced-html-architecture.md) | Advanced HTML Processing Architecture | Accepted |

### Multi-Model Architecture (v0.5)

| ADR | Title | Status |
|-----|-------|--------|
| [0026](./0026-multi-model-architecture.md) | Multi-Model Architecture | Accepted |
| [0030](./0030-model-quantisation-strategy.md) | Model Quantisation Strategy | Accepted |

### Fine-Tuning (v0.9)

| ADR | Title | Status |
|-----|-------|--------|
| [0027](./0027-fine-tuning-strategy.md) | Fine-Tuning Strategy | Proposed |

### Privacy & Security (v0.7+)

| ADR | Title | Status |
|-----|-------|--------|
| [0009](./0009-security-architecture.md) | Security Architecture | Accepted |
| [0010](./0010-vector-database-security.md) | Vector Database Security | Accepted |
| [0028](./0028-pii-handling-architecture.md) | PII Handling Architecture | Proposed |
| [0029](./0029-embedding-privacy-strategy.md) | Privacy-Preserving Embedding Strategy | Proposed |

### Personal Knowledge Assistant (v2.0)

| ADR | Title | Status |
|-----|-------|--------|
| [0022](./0022-personal-vault-isolation.md) | Personal Vault Isolation | Accepted |

## ADR Template

```markdown
# ADR-NNNN: [Title]

## Status
[Proposed/Accepted/Deprecated/Superseded]

## Context
What is the issue that we're seeing that is motivating this decision?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult to do because of this change?

## Alternatives Considered
What other options were evaluated?
```

## Naming Convention

Files named: `NNNN-title.md` (e.g., `0001-use-typer-for-cli.md`)

## ADR Statuses

| Status | Meaning |
|--------|---------|
| **Proposed** | Under discussion |
| **Accepted** | Decision made, in effect |
| **Deprecated** | No longer applies |
| **Superseded** | Replaced by another ADR |

## When to Create an ADR

- Choosing a framework or library
- Defining a coding pattern
- Making infrastructure decisions
- Establishing conventions

## What Doesn't Belong Here

- Implementation details → [implementation/](../../implementation/)
- Feature specifications → [features/](../../features/)
- Temporary decisions (use comments instead)

---

## Related Documentation

- [Decisions Hub](../README.md)
- [Implementation Records](../../implementation/)

