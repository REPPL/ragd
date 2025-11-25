# Architecture Decision Records (ADRs)

Lightweight documentation of significant technical decisions.

## Available ADRs

| ADR | Title | Status |
|-----|-------|--------|
| [0001](./0001-use-typer-rich-cli.md) | Use Typer + Rich for CLI | Accepted |
| [0002](./0002-chromadb-vector-store.md) | Use ChromaDB as Default Vector Store | Accepted |
| [0003](./0003-privacy-first-architecture.md) | Privacy-First Architecture | Accepted |
| [0004](./0004-hybrid-specification-approach.md) | Hybrid Specification Approach | Accepted |

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

