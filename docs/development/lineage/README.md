# Knowledge Transfer: ragged → ragd

ragd is a clean rewrite of the ragged project, incorporating lessons learned from ~70K lines of implementation across v0.1-v0.6.

## Purpose

This directory documents the knowledge transfer process from ragged to ragd, preserving:
- Research and analysis that informed ragd's design
- Decision rationale for specification approach
- Feature mapping and prioritisation
- Acknowledgements for research sources

## Source Project

| Attribute | Value |
|-----------|-------|
| **Project** | ragged |
| **Versions Analysed** | v0.1-v0.6 (implemented), v0.7-v2.0 (planned) |
| **Codebase Size** | ~70K lines Python, 35+ CLI commands |

## Contents

| Document | Purpose |
|----------|---------|
| [ragged-analysis.md](./ragged-analysis.md) | Comprehensive research report |
| [planning-prompt.md](./planning-prompt.md) | Original prompt and Q&A that shaped decisions |
| [feature-mapping.md](./feature-mapping.md) | ragged → ragd feature traceability |
| [acknowledgements.md](./acknowledgements.md) | Research sources and citations |

## What Transfers

### Core Vision
- **Privacy-first**: 100% local processing, no external APIs required
- **Zero-cost**: Open source, no API fees
- **Simplicity-first**: CLI-first, minimal configuration
- **Experimentation-friendly**: Modular, pluggable architecture

### Feature Set (Adapted & Prioritised)
- Document ingestion with messy PDF handling (killer feature)
- Advanced chunking strategies
- Hybrid search (BM25 + vector)
- Multi-modal retrieval (ColPali)
- Chat with context (Ollama)
- Storage efficiency (LEANN)
- Privacy & security
- Memory & personalisation

### Architecture Patterns
- Modular, pluggable components
- Factory pattern for swappable backends
- Configuration-driven behaviour
- VectorStore abstraction

### Documentation Standards
- Feature-centric roadmap (not version-centric)
- Hybrid specification (Use Cases → Features → Tutorials)
- Single Source of Truth principle

## What Changes

| Aspect | ragged | ragd |
|--------|--------|------|
| **Development** | Evolved organically | Specification-first |
| **Validation** | Tests after features | Tutorial-driven validation |
| **PDF Processing** | Added later (v0.5+) | Core from v0.2 (killer feature) |
| **Multi-modal** | v0.5+ | v0.4 (earlier priority) |
| **WebUI** | Complex evolution | Simple at v1.0, enhance post-stability |

## Key Lessons Applied

### What Worked (Preserved)
- Feature-centric roadmap structure
- Phase-based development with clear milestones
- AI assistance (3-4x speedup documented)
- Privacy-first architecture
- Typer + Rich CLI framework

### What Improved
- Tests alongside implementation (not deferred)
- Integration testing early
- Documentation as you go
- Fewer, larger phases (10 vs 14)
- Security audit continuous
- Messy PDF handling from the start

## Related Documentation

- [Product Vision](../planning/vision/) - ragd's vision (inherited from ragged)
- [Feature Roadmap](../features/) - Feature specifications
- [Milestones](../milestones/) - Release planning
- [ADRs](../decisions/adrs/) - Architecture decisions

