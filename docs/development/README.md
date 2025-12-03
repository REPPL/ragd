# Development Documentation

Documentation for contributors and developers.

## Current Status

| Area | Status |
|------|--------|
| Use Cases | 6 P0 briefs defined |
| Features | v0.1 (9), v0.2 (12), v0.3 (4), v0.4 (1), v0.5 (4) = 30 features complete |
| Tutorials | Getting Started + 3 v0.2 tutorials |
| Milestone | v0.5.0 released |
| ADRs | 29+ architecture decisions |

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

### v0.5.0 (Latest Release)
- [v0.5.0 Milestone](./milestones/v0.5.0.md)
- [v0.5.0 Implementation](./implementation/v0.5.0.md)
- [F-013: RAGAS Evaluation](./features/completed/F-013-ragas-evaluation.md)
- [F-014: Agentic RAG](./features/completed/F-014-agentic-rag.md)
- [F-020: Ollama LLM Integration](./features/completed/F-020-ollama-llm-integration.md)
- [F-055: Multi-Model Orchestration](./features/completed/F-055-multi-model-orchestration.md)

### v0.4.0 (Released)
- [v0.4.0 Milestone](./milestones/v0.4.0.md)
- [v0.4.0 Implementation](./implementation/v0.4.0.md)
- [F-019: Multi-Modal Support](./features/completed/F-019-multi-modal-support.md)

### v0.3.0 (Released)
- [v0.3.0 Milestone](./milestones/v0.3.0.md)
- [v0.3.0 Implementation](./implementation/v0.3.0.md)
- [F-009: Citation Output](./features/completed/F-009-citation-output.md)
- [F-010: Contextual Retrieval](./features/completed/F-010-contextual-retrieval.md)
- [F-011: Late Chunking](./features/completed/F-011-late-chunking.md)
- [F-012: Hybrid Search](./features/completed/F-012-hybrid-search.md)

### v0.2.0 (Released)
- [v0.2.0 Milestone](./milestones/v0.2.0.md)
- [v0.2.0 Implementation](./implementation/v0.2.0.md)

### v0.1.0 (Released)
- [v0.1.0 Milestone](./milestones/v0.1.0.md)
- [v0.1.0 Implementation](./implementation/v0.1.0.md)

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

