# Research

State-of-the-art research informing ragd's roadmap and architecture.

## Purpose

This directory contains research on cutting-edge techniques that inform ragd's feature development. These documents survey external literature and industry best practices rather than documenting ragd's internal development.

## Contents

### State-of-the-Art Surveys

| Document | Description |
|----------|-------------|
| [state-of-the-art-rag.md](./state-of-the-art-rag.md) | Advanced RAG techniques (2024-2025): Agentic RAG, Contextual Retrieval, GraphRAG |
| [state-of-the-art-chunking.md](./state-of-the-art-chunking.md) | Text chunking strategies: size optimisation, semantic chunking, overlap, late chunking |
| [state-of-the-art-privacy.md](./state-of-the-art-privacy.md) | Privacy-preserving architecture: encryption, embedding security, threat models |
| [state-of-the-art-pii-removal.md](./state-of-the-art-pii-removal.md) | PII detection and removal: Presidio, NER, redaction, GDPR compliance, embedding protection |
| [state-of-the-art-pdf-processing.md](./state-of-the-art-pdf-processing.md) | Messy PDF processing: Docling, ColPali, OCR comparison, OHRBench findings |
| [state-of-the-art-metadata.md](./state-of-the-art-metadata.md) | Document metadata: extraction, storage, tagging, provenance, Dublin Core |
| [state-of-the-art-data-schemas.md](./state-of-the-art-data-schemas.md) | RAG data schemas: Pydantic models, ChromaDB patterns, parent-child relationships, citations |
| [state-of-the-art-local-rag.md](./state-of-the-art-local-rag.md) | Local RAG: performance, caching, multi-model orchestration, vector/graph storage |
| [state-of-the-art-multi-model-rag.md](./state-of-the-art-multi-model-rag.md) | Multi-model RAG: SLMs, model routing, SLIM models, LLM-as-Judge, ensembles |
| [state-of-the-art-embeddings.md](./state-of-the-art-embeddings.md) | Embedding model selection: MTEB benchmarks, nomic, BGE-M3, quantisation |
| [state-of-the-art-fine-tuning.md](./state-of-the-art-fine-tuning.md) | Fine-tuning local models: embeddings, LLMs (RAFT), rerankers, MLX, Unsloth |
| [state-of-the-art-quantisation.md](./state-of-the-art-quantisation.md) | LLM quantisation: GGUF K-quants, Apple Silicon optimisation, KV cache, multi-model memory |
| [state-of-the-art-evaluation.md](./state-of-the-art-evaluation.md) | RAG evaluation frameworks: RAGAS, DeepEval, BEIR, metrics interpretation |
| [state-of-the-art-setup-ux.md](./state-of-the-art-setup-ux.md) | Easy setup patterns: uv, hardware detection, model provisioning, health checks |
| [state-of-the-art-cli-modes.md](./state-of-the-art-cli-modes.md) | CLI dual-mode design: porcelain/plumbing, progressive disclosure, verbosity |
| [state-of-the-art-user-interfaces.md](./state-of-the-art-user-interfaces.md) | TUI & WebUI frameworks: Textual, Gradio, Reflex, prototyping tools |
| [state-of-the-art-multi-modal.md](./state-of-the-art-multi-modal.md) | Multi-modal RAG: ColPali, SigLIP 2, vision retrieval, image understanding |
| [state-of-the-art-knowledge-graphs.md](./state-of-the-art-knowledge-graphs.md) | Knowledge graph integration: GraphRAG, Kuzu, Leiden, entity extraction |
| [state-of-the-art-rag-landscape.md](./state-of-the-art-rag-landscape.md) | RAG tool landscape: PrivateGPT, AnythingLLM, Khoj, differentiation strategy |
| [state-of-the-art-configuration.md](./state-of-the-art-configuration.md) | Configuration management: XDG directories, Pydantic, defaults, schema versioning |
| [state-of-the-art-personal-rag.md](./state-of-the-art-personal-rag.md) | Personal RAG: memory architectures (Mem0, Letta), PersonaRAG, user context, privacy |
| [state-of-the-art-tagging.md](./state-of-the-art-tagging.md) | Document tagging: automated/manual tagging, tag libraries, provenance, smart collections |

### Implementation Research

| Document | Description |
|----------|-------------|
| [cli-best-practices.md](./cli-best-practices.md) | Modern CLI design for non-expert users (clig.dev, Atlassian principles) |
| [cli-documentation-standards.md](./cli-documentation-standards.md) | CLI reference documentation: man pages, help text, auto-generation (git, kubectl, docker, gh) |
| [citation-systems.md](./citation-systems.md) | RAG citation formats, academic styles, ALCE benchmark |

### v0.2 Integration Guides

| Document | Description |
|----------|-------------|
| [docling-integration-guide.md](./docling-integration-guide.md) | IBM Docling: API patterns, PipelineOptions, lazy loading, table extraction |
| [paddleocr-integration-guide.md](./paddleocr-integration-guide.md) | PaddleOCR + EasyOCR: fallback pattern, confidence scoring, batch processing |
| [nlp-library-integration.md](./nlp-library-integration.md) | KeyBERT, spaCy, langdetect: model sharing, lazy loading, MetadataExtractor design |

## Research Status

All research documents are complete and inform the roadmap.

| Document | Status | Informs Features |
|----------|--------|------------------|
| state-of-the-art-rag.md | ✅ Complete | F-010, F-011, F-014 |
| state-of-the-art-chunking.md | ✅ Complete | F-003, F-011 |
| state-of-the-art-privacy.md | ✅ Complete | F-015, F-016, F-017, F-018, F-023 |
| state-of-the-art-pii-removal.md | ✅ Complete | F-023, F-056, F-057, ADR-0028, ADR-0029 |
| state-of-the-art-pdf-processing.md | ✅ Complete | v0.2 features |
| state-of-the-art-metadata.md | ✅ Complete | v0.2 features |
| state-of-the-art-data-schemas.md | ✅ Complete | F-002, F-003, F-009 |
| state-of-the-art-local-rag.md | ✅ Complete | F-020, v0.3+ features |
| state-of-the-art-multi-model-rag.md | ✅ Complete | F-020, F-055, F-056, F-057, ADR-0026 |
| state-of-the-art-embeddings.md | ✅ Complete | F-004 |
| state-of-the-art-fine-tuning.md | ✅ Complete | F-058, ADR-0027 |
| state-of-the-art-quantisation.md | ✅ Complete | ADR-0030, F-020 |
| state-of-the-art-evaluation.md | ✅ Complete | F-013 |
| state-of-the-art-setup-ux.md | ✅ Complete | F-007, F-035 |
| state-of-the-art-cli-modes.md | ✅ Complete | F-006 |
| state-of-the-art-user-interfaces.md | ✅ Complete | F-024 |
| state-of-the-art-multi-modal.md | ✅ Complete | F-019 |
| state-of-the-art-knowledge-graphs.md | ✅ Complete | F-022 |
| state-of-the-art-rag-landscape.md | ✅ Complete | Strategic positioning |
| state-of-the-art-configuration.md | ✅ Complete | ADR-0013, F-035, F-036 |
| state-of-the-art-personal-rag.md | ✅ Complete | F-040, F-041, F-042, F-044 (v2.0) |
| state-of-the-art-tagging.md | ✅ Complete | F-031, F-061, F-062, F-063, F-064 |
| cli-best-practices.md | ✅ Complete | F-001, F-006 |
| cli-documentation-standards.md | ✅ Complete | CLI reference docs (v0.2+) |
| citation-systems.md | ✅ Complete | F-009 |
| docling-integration-guide.md | ✅ Complete | F-026, F-028 |
| paddleocr-integration-guide.md | ✅ Complete | F-027 |
| nlp-library-integration.md | ✅ Complete | F-030 |

## What Belongs Here

- Literature surveys on techniques relevant to ragd
- Research summaries with implementation recommendations
- Comparative analysis of approaches
- References to papers, projects, and industry best practices

## What Doesn't Belong Here

- Internal design decisions → [ADRs](../decisions/adrs/)
- Feature specifications → [Features](../features/)
- Knowledge transfer from ragged → [Lineage](../lineage/)
- User-facing explanations → [Explanation](../../explanation/)

---

## Related Documentation

- [Lineage](../lineage/) - Knowledge transfer from ragged predecessor
- [ADRs](../decisions/adrs/) - Architecture decisions applying this research
- [Feature Roadmap](../features/) - Features informed by this research

