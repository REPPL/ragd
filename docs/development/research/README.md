# Research

State-of-the-art research informing ragd's roadmap and architecture.

## Purpose

This directory contains research on cutting-edge techniques that inform ragd's feature development. These documents survey external literature and industry best practices rather than documenting ragd's internal development.

## Contents

### State-of-the-Art Surveys

| Document | Description |
|----------|-------------|
| [state-of-the-art-rag.md](./state-of-the-art-rag.md) | Advanced RAG techniques (2024-2025): Agentic RAG, Contextual Retrieval, GraphRAG |
| [state-of-the-art-privacy.md](./state-of-the-art-privacy.md) | Privacy-preserving architecture: encryption, embedding security, threat models |
| [state-of-the-art-pdf-processing.md](./state-of-the-art-pdf-processing.md) | Messy PDF processing: Docling, ColPali, OCR comparison, OHRBench findings |
| [state-of-the-art-metadata.md](./state-of-the-art-metadata.md) | Document metadata: extraction, storage, tagging, provenance, Dublin Core |
| [state-of-the-art-local-rag.md](./state-of-the-art-local-rag.md) | Local RAG: performance, caching, multi-model orchestration, vector/graph storage |
| [state-of-the-art-embeddings.md](./state-of-the-art-embeddings.md) | Embedding model selection: MTEB benchmarks, nomic, BGE-M3, quantisation |
| [state-of-the-art-evaluation.md](./state-of-the-art-evaluation.md) | RAG evaluation frameworks: RAGAS, DeepEval, BEIR, metrics interpretation |
| [state-of-the-art-setup-ux.md](./state-of-the-art-setup-ux.md) | Easy setup patterns: uv, hardware detection, model provisioning, health checks |
| [state-of-the-art-cli-modes.md](./state-of-the-art-cli-modes.md) | CLI dual-mode design: porcelain/plumbing, progressive disclosure, verbosity |
| [state-of-the-art-user-interfaces.md](./state-of-the-art-user-interfaces.md) | TUI & WebUI frameworks: Textual, Gradio, Reflex, prototyping tools |
| [state-of-the-art-multi-modal.md](./state-of-the-art-multi-modal.md) | Multi-modal RAG: ColPali, SigLIP 2, vision retrieval, image understanding |
| [state-of-the-art-knowledge-graphs.md](./state-of-the-art-knowledge-graphs.md) | Knowledge graph integration: GraphRAG, Kuzu, Leiden, entity extraction |
| [state-of-the-art-rag-landscape.md](./state-of-the-art-rag-landscape.md) | RAG tool landscape: PrivateGPT, AnythingLLM, Khoj, differentiation strategy |

### Implementation Research

| Document | Description |
|----------|-------------|
| [cli-best-practices.md](./cli-best-practices.md) | Modern CLI design for non-expert users (clig.dev, Atlassian principles) |
| [citation-systems.md](./citation-systems.md) | RAG citation formats, academic styles, ALCE benchmark |

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

