# ADR-0007: Advanced Retrieval Techniques

## Status

Accepted

## Context

Basic semantic search (v0.1) uses single-vector embeddings per chunk. Research shows significant improvements from advanced techniques:

- **Contextual Retrieval** (Anthropic): 67% reduction in retrieval failures
- **Late Chunking** (Jina AI): Better context preservation without LLM cost
- **Hybrid Search**: BM25 + semantic for better keyword handling

These techniques address the "chunk without context" problem where chunks lose meaning when separated from their document.

## Decision

Implement three complementary retrieval enhancements for v0.3:

### 1. Contextual Retrieval

Prepend generated context to each chunk before embedding:

```
Document → Chunk → [Generate Context with LLM] → Embed(Context + Chunk) → Store
```

Context generation example:
```
"This chunk is from a document about user authentication.
It discusses OAuth 2.0 token validation..."
```

**Trade-off:** LLM cost per chunk. Mitigate with:
- Small/fast models (Ollama, Claude Haiku)
- Batch processing
- Optional per-index setting

### 2. Late Chunking

Use long-context embedding models (8K+ tokens):

```
Document → Embed Full Document → Mean Pool per Chunk → Store
```

**Trade-off:** Requires jina-embeddings-v2-base-en or similar 8K model.

### 3. Hybrid Search

Combine BM25 (keyword) with semantic (vector) search:

```
Query → [BM25 Search] + [Vector Search] → Reciprocal Rank Fusion → Results
```

**Implementation:** ChromaDB with sqlite-vec for BM25, or dedicated BM25 index.

## Consequences

### Positive

- Significant retrieval quality improvements (49-67%)
- Multiple technique options for different use cases
- Contextual retrieval works with existing infrastructure
- Hybrid search handles both keyword and semantic queries

### Negative

- Contextual retrieval adds LLM dependency and cost
- Late chunking requires specific embedding models
- Hybrid search adds index complexity
- Configuration complexity for users

## Implementation Strategy

| Technique | Milestone | Default | Optional |
|-----------|-----------|---------|----------|
| Hybrid Search | v0.3.0 | ✓ | |
| Contextual Retrieval | v0.3.1 | | ✓ (requires LLM) |
| Late Chunking | v0.3.2 | | ✓ (requires 8K model) |

## Related Documentation

- [State-of-the-Art RAG Research](../../research/state-of-the-art-rag.md)
- [F-010: Contextual Retrieval](../../features/planned/F-010-contextual-retrieval.md)
- [F-011: Late Chunking](../../features/planned/F-011-late-chunking.md)
- [F-012: Hybrid Search](../../features/planned/F-012-hybrid-search.md)

---
