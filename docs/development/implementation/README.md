# Implementation Records

Documentation of what was built.

## Purpose

Implementation records capture technical details of completed features. They answer "what was built and how" after the fact.

## Available Records

| Version | Description | Status |
|---------|-------------|--------|
| [v0.1.0](./v0.1.0.md) | Core RAG - Document ingestion, text extraction, chunking, embedding, semantic search | Complete |
| [v0.2.0](./v0.2.0.md) | Killer Feature - Messy PDFs, Docling, OCR, table extraction, metadata | Complete |
| [v0.3.0](./v0.3.0.md) | Advanced Search - Hybrid search, contextual retrieval, late chunking, citations | Complete |
| [v0.4.0](./v0.4.0.md) | Multi-Modal - Vision embeddings, image extraction, multi-modal search | Complete |
| [v0.5.0](./v0.5.0.md) | Chat - LLM integration, conversational interface, session management | Complete |
| [v0.6.0](./v0.6.0.md) | Storage - Backend abstraction, FAISS integration, score normalisation | Complete |
| [v0.6.5](./v0.6.5.md) | Polish & Stability - RAGAS metrics, CLI improvements, config validation | Complete |
| [v0.7.0](./v0.7.0.md) | Privacy & Security - Encryption, session management, secure deletion, PII detection | Complete |
| [v0.8.0](./v0.8.0.md) | Intelligence Foundation - Tag provenance, data sensitivity tiers | Complete |
| [v0.8.1](./v0.8.1.md) | Intelligent Tagging - Smart collections, auto-tag suggestions, tag library | Complete |
| [v0.8.2](./v0.8.2.md) | Retrieval Enhancements - Cross-encoder reranking, query decomposition | Complete |
| [v0.8.5](./v0.8.5.md) | Knowledge Graph - Entity extraction, graph storage, co-occurrence relationships | Complete |

## Record Template

```markdown
# Implementation: [Feature Name]

## Overview
What was implemented.

## Architecture
How it was structured.

## Key Decisions
Important choices made during implementation.

## Files Changed
- `path/to/file.py` - Description

## Status
Completed
```

## What Belongs Here

- Technical implementation details
- Architecture documentation for completed work
- Post-implementation analysis

## What Doesn't Belong Here

- Future plans → [features/](../features/)
- Development narrative → [process/devlogs/](../process/devlogs/)
- Architecture decisions → [decisions/adrs/](../decisions/adrs/)

---

## Related Documentation

- [Development Hub](../README.md)
- [Completed Features](../features/completed/)
