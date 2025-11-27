# F-011: Late Chunking

## Overview

**Research**: [State-of-the-Art RAG](../../research/state-of-the-art-rag.md)
**ADR**: [ADR-0007: Advanced Retrieval Techniques](../../decisions/adrs/0007-advanced-retrieval-techniques.md)
**Milestone**: v0.3
**Priority**: P2

## Problem Statement

Traditional "chunk-then-embed" loses cross-chunk context. Information about entity X in chunk 1 doesn't inform the embedding of chunk 2, even if they're semantically related.

Late chunking embeds the full document first, preserving context in the embeddings before chunking.

## Design Approach

### Architecture

```
Document (up to 8K tokens)
    ↓
[Long-Context Embedding Model]
    ↓
Full Document Embedding (token-level)
    ↓
[Mean Pool per Chunk Boundary]
    ↓
Chunk Embeddings (with document context)
    ↓
Store
```

### How It Works

1. **Embed full document**: Use 8K+ context embedding model
2. **Get token embeddings**: Extract per-token vectors
3. **Define chunk boundaries**: Same as regular chunking
4. **Mean pool**: Average token embeddings within each boundary
5. **Store**: Chunk embeddings preserve full document context

### Model Requirements

| Model | Context | Notes |
|-------|---------|-------|
| jina-embeddings-v2-base-en | 8,192 tokens | Recommended |
| nomic-embed-text-v1.5 | 8,192 tokens | Alternative |

## Implementation Tasks

- [ ] Research and select long-context embedding model
- [ ] Implement document-level embedding
- [ ] Extract token-level embeddings
- [ ] Implement chunk boundary detection
- [ ] Implement mean pooling per chunk
- [ ] Add configuration for late chunking enable/disable
- [ ] Handle documents exceeding model context
- [ ] Add fallback to standard chunking for long documents
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Benchmark vs standard chunking

## Success Criteria

- [ ] Documents up to 8K tokens processed with late chunking
- [ ] Graceful fallback for longer documents
- [ ] Configurable enable/disable
- [ ] Measurable retrieval improvement
- [ ] No LLM cost (embedding only)

## Dependencies

- F-003: Chunking Engine
- F-004: Embedding Generation
- Long-context embedding model

## Technical Notes

### Configuration

```yaml
retrieval:
  late_chunking:
    enabled: true
    model: jina-embeddings-v2-base-en
    max_tokens: 8192
    fallback: standard  # standard | skip
```

### Algorithm

```python
def late_chunk_embed(document: str, chunk_boundaries: list[tuple[int, int]]) -> list[np.ndarray]:
    # 1. Embed full document with token-level output
    token_embeddings = model.encode(document, output_token_embeddings=True)

    # 2. Mean pool per chunk
    chunk_embeddings = []
    for start, end in chunk_boundaries:
        chunk_tokens = token_embeddings[start:end]
        chunk_embedding = np.mean(chunk_tokens, axis=0)
        chunk_embeddings.append(chunk_embedding)

    return chunk_embeddings
```

### Trade-offs vs Contextual Retrieval

| Aspect | Late Chunking | Contextual Retrieval |
|--------|--------------|---------------------|
| LLM required | No | Yes |
| Cost | Free | Per-chunk LLM call |
| Context quality | Good | Better |
| Max document size | 8K tokens | Unlimited |
| Model dependency | Specific models | Any embedding model |

## Related Documentation

- [ADR-0007: Advanced Retrieval Techniques](../../decisions/adrs/0007-advanced-retrieval-techniques.md)
- [F-010: Contextual Retrieval](./F-010-contextual-retrieval.md) - Alternative approach
- [F-012: Hybrid Search](./F-012-hybrid-search.md) - Complementary feature
- [Jina AI Late Chunking](https://jina.ai/news/late-chunking-in-long-context-embedding-models/)

---
