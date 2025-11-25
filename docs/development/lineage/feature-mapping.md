# Feature Mapping: ragged → ragd

Traceability matrix mapping ragged features to ragd milestones.

## Mapping Overview

This document tracks which ragged features transfer to ragd, their priority, and target milestone.

---

## Legend

| Priority | Meaning |
|----------|---------|
| **P0** | Must have - core RAG functionality |
| **P1** | Should have - expected features |
| **P2** | Could have - differentiators |
| **P3** | Future - post-v1.0 |

| Status | Meaning |
|--------|---------|
| **Transfer** | Feature transfers to ragd |
| **Adapt** | Feature transfers with modifications |
| **Defer** | Feature deferred to later version |
| **Skip** | Feature not included in ragd |

---

## Document Processing

| ragged Feature | ragged Version | ragd Version | Priority | Status | Notes |
|----------------|----------------|--------------|----------|--------|-------|
| PDF ingestion | v0.1 | v0.1 | P0 | Transfer | Core functionality |
| TXT/Markdown support | v0.1 | v0.1 | P0 | Transfer | Basic formats |
| HTML support | v0.2 | v0.2 | P0 | Transfer | Web content |
| DOCX support | v0.3 | v0.2 | P0 | Transfer | Office docs |
| EPUB support | v0.4 | v0.2 | P0 | Transfer | E-books |
| **PDF quality detection** | v0.5 | **v0.2** | **P0** | **Adapt** | **Earlier - killer feature** |
| **OCR pipeline** | v0.5 | **v0.2** | **P0** | **Adapt** | **Earlier - killer feature** |
| **Docling integration** | v0.5 | **v0.2** | **P0** | **Transfer** | **Earlier - killer feature** |
| Scan preprocessing | v0.5 | v0.4 | P1 | Transfer | Deskew, denoise |
| Batch ingestion | v0.2 | v0.2 | P0 | Transfer | Progress tracking |
| Metadata extraction | v0.2 | v0.2 | P0 | Transfer | Auto-tagging |

---

## Chunking & Text Processing

| ragged Feature | ragged Version | ragd Version | Priority | Status | Notes |
|----------------|----------------|--------------|----------|--------|-------|
| Fixed chunking | v0.1 | v0.1 | P0 | Transfer | Basic strategy |
| Semantic chunking | v0.3 | v0.1 | P0 | Transfer | Sentence-aware |
| Recursive chunking | v0.3 | v0.1 | P0 | Transfer | Document structure |
| **Hierarchical chunking** | v0.3 | **v0.3** | **P1** | **Transfer** | Parent-child |
| **Contextual chunking** | v0.3 | **v0.3** | **P1** | **Transfer** | Context preservation |
| Late chunking | v0.4 | v0.3 | P1 | Transfer | Delayed processing |
| Token counting | v0.1 | v0.1 | P0 | Transfer | tiktoken |

---

## Embeddings

| ragged Feature | ragged Version | ragd Version | Priority | Status | Notes |
|----------------|----------------|--------------|----------|--------|-------|
| sentence-transformers | v0.1 | v0.1 | P0 | Transfer | Default embedder |
| Ollama embeddings | v0.1 | v0.1 | P0 | Transfer | API-based |
| **ColPali vision** | v0.5 | **v0.4** | **P1** | **Adapt** | **Earlier priority** |
| Embedder factory | v0.1 | v0.1 | P0 | Transfer | Swappable backends |
| Batch tuning | v0.4 | v0.4 | P1 | Transfer | Optimisation |

---

## Storage

| ragged Feature | ragged Version | ragd Version | Priority | Status | Notes |
|----------------|----------------|--------------|----------|--------|-------|
| ChromaDB | v0.1 | v0.1 | P0 | Transfer | Default backend |
| VectorStore abstraction | v0.4 | v0.6 | P2 | Transfer | Backend switching |
| **LEANN integration** | v0.4 | **v0.6** | **P2** | **Transfer** | 97% storage savings |
| Dual storage | v0.5 | v0.8 | P2 | Transfer | Vector + graph |
| Version tracking | v0.4 | v0.6 | P2 | Transfer | Document versions |
| Schema migration | v0.5 | v0.6 | P2 | Transfer | Backend upgrades |

---

## Retrieval & Search

| ragged Feature | ragged Version | ragd Version | Priority | Status | Notes |
|----------------|----------------|--------------|----------|--------|-------|
| Semantic search | v0.1 | v0.1 | P0 | Transfer | Vector similarity |
| BM25 lexical search | v0.2 | v0.3 | P1 | Transfer | Keyword matching |
| **Hybrid search (RRF)** | v0.2 | **v0.3** | **P1** | **Transfer** | Combined ranking |
| Metadata filtering | v0.2 | v0.3 | P1 | Transfer | Tag-based |
| Reranking | v0.3 | v0.3 | P1 | Transfer | Result refinement |
| **Query decomposition** | v0.3 | **v0.3** | **P1** | **Transfer** | Complex queries |
| **Query classification** | v0.3 | **v0.3** | **P1** | **Transfer** | Routing |
| **HyDE** | v0.3 | **v0.3** | **P1** | **Transfer** | Hypothetical docs |
| Vision retrieval | v0.5 | v0.4 | P1 | Transfer | Image search |
| Personalised retrieval | v0.4 | v0.8 | P2 | Transfer | User profiles |

---

## Generation & Chat

| ragged Feature | ragged Version | ragd Version | Priority | Status | Notes |
|----------------|----------------|--------------|----------|--------|-------|
| Ollama client | v0.1 | v0.5 | P1 | Transfer | LLM integration |
| Response streaming | v0.2 | v0.5 | P1 | Transfer | Progressive output |
| Citation formatting | v0.2 | v0.5 | P1 | Transfer | Source references |
| Conversation history | v0.3 | v0.5 | P1 | Transfer | Memory |
| Few-shot prompting | v0.3 | v0.5 | P1 | Transfer | Examples |

---

## Memory & Personalisation

| ragged Feature | ragged Version | ragd Version | Priority | Status | Notes |
|----------------|----------------|--------------|----------|--------|-------|
| Interaction tracking | v0.4 | v0.8 | P2 | Transfer | User history |
| **Persona system** | v0.4 | **v0.8** | **P2** | **Transfer** | Context switching |
| User profiles | v0.4 | v0.8 | P2 | Transfer | Preferences |
| **Temporal awareness** | v0.4 | **v0.8** | **P2** | **Transfer** | Time-based queries |
| Topic tracking | v0.4 | v0.8 | P2 | Transfer | Interest areas |
| Knowledge graph | v0.4 | v0.8 | P2 | Transfer | Kuzu integration |

---

## Privacy & Security

| ragged Feature | ragged Version | ragd Version | Priority | Status | Notes |
|----------------|----------------|--------------|----------|--------|-------|
| Local-only processing | v0.1 | v0.1 | P0 | Transfer | Core principle |
| **PII detection** | v0.6 | **v0.7** | **P2** | **Transfer** | Visual scanning |
| Data encryption | v0.6 | v0.7 | P2 | Transfer | Sensitive data |
| GDPR compliance | v0.6 | v0.7 | P2 | Transfer | Data lifecycle |
| Audit logging | v0.6 | v0.7 | P2 | Transfer | Access trails |
| Security middleware | v0.6 | v0.7 | P2 | Transfer | CSRF, XSS |

---

## CLI Commands

| ragged Command | ragged Version | ragd Version | Priority | Status |
|----------------|----------------|--------------|----------|--------|
| `ingest pdf` | v0.1 | v0.1 | P0 | Transfer |
| `ingest batch` | v0.2 | v0.2 | P0 | Transfer |
| `query text` | v0.1 | v0.1 | P0 | Transfer |
| `query image` | v0.5 | v0.4 | P1 | Transfer |
| `query hybrid` | v0.2 | v0.3 | P1 | Transfer |
| `query interactive` | v0.3 | v0.5 | P1 | Transfer |
| `config show/set` | v0.1 | v0.1 | P0 | Transfer |
| `storage info` | v0.2 | v0.6 | P2 | Transfer |
| `gpu list/info` | v0.5 | v0.4 | P1 | Transfer |
| `health` | v0.1 | v0.1 | P0 | Transfer |
| `serve` | v0.6 | v1.0 | P2 | Transfer |

---

## Web UI

| ragged Feature | ragged Version | ragd Version | Priority | Status | Notes |
|----------------|----------------|--------------|----------|--------|-------|
| FastAPI backend | v0.6 | v1.0 | P2 | Transfer | API server |
| **Basic chat UI** | v0.6 | **v1.0** | **P2** | **Transfer** | Simple interface |
| **Document upload** | v0.6 | **v1.0** | **P2** | **Transfer** | Drag & drop |
| Document browser | v0.7 | v1.1+ | P3 | Defer | Library view |
| Dark mode | v0.9 | v1.1+ | P3 | Defer | Theming |
| Knowledge graph viz | v0.9 | v1.2+ | P3 | Defer | D3 graphs |
| PWA support | v0.9 | v1.2+ | P3 | Defer | Offline |

---

## Features NOT Transferred

| ragged Feature | Reason | Alternative |
|----------------|--------|-------------|
| Block editor | Over-engineered for v1.0 | Defer to v1.3+ |
| Visual workflow editor | Over-engineered for v1.0 | Defer to v1.3+ |
| Collaboration | Scope creep | Defer indefinitely |
| Plugin marketplace | Complexity | Defer indefinitely |
| Enterprise SSO | Out of scope | Consider v2.0 |

---

## Summary Statistics

| Category | Transfer | Adapt | Defer | Skip | Total |
|----------|----------|-------|-------|------|-------|
| Document Processing | 9 | 3 | 0 | 0 | 12 |
| Chunking | 6 | 0 | 0 | 0 | 6 |
| Embeddings | 4 | 1 | 0 | 0 | 5 |
| Storage | 5 | 1 | 0 | 0 | 6 |
| Retrieval | 9 | 1 | 0 | 0 | 10 |
| Generation | 5 | 0 | 0 | 0 | 5 |
| Memory | 6 | 0 | 0 | 0 | 6 |
| Privacy | 5 | 0 | 0 | 0 | 5 |
| CLI | 11 | 0 | 0 | 0 | 11 |
| Web UI | 2 | 0 | 4 | 3 | 9 |
| **Total** | **62** | **6** | **4** | **3** | **75** |

