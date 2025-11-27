# F-012: Hybrid Search

## Overview

**Research**: [State-of-the-Art RAG](../../research/state-of-the-art-rag.md)
**ADR**: [ADR-0007: Advanced Retrieval Techniques](../../decisions/adrs/0007-advanced-retrieval-techniques.md)
**Milestone**: v0.3
**Priority**: P0

## Problem Statement

Semantic search excels at understanding meaning but struggles with:
- Exact keyword matches ("error code E1234")
- Rare terms and proper nouns
- Technical identifiers

BM25 (keyword search) complements semantic search by handling these cases.

## Design Approach

### Architecture

```
Query
    ↓
┌───────────────┬───────────────┐
│               │               │
▼               ▼               │
[BM25 Search]   [Vector Search] │
     │               │          │
     ▼               ▼          │
BM25 Results    Vector Results  │
     │               │          │
     └───────┬───────┘          │
             │                  │
             ▼                  │
[Reciprocal Rank Fusion]        │
             │                  │
             ▼                  │
      Final Results             │
```

### Reciprocal Rank Fusion (RRF)

Combines rankings from multiple sources:

```
RRF_score(doc) = Σ 1 / (k + rank_i(doc))

where:
- k = 60 (constant)
- rank_i = rank in result list i
```

### BM25 Implementation Options

| Option | Pros | Cons |
|--------|------|------|
| sqlite-fts5 | Built into SQLite | Separate index |
| rank-bm25 | Pure Python | Slower |
| whoosh | Full-featured | Heavy dependency |

**Recommendation:** sqlite-fts5 for integration with ChromaDB's SQLite backend.

## Implementation Tasks

- [ ] Design hybrid search interface
- [ ] Implement BM25 index using sqlite-fts5
- [ ] Implement parallel query execution
- [ ] Implement Reciprocal Rank Fusion
- [ ] Add BM25 index building to indexing pipeline
- [ ] Add configuration for search weights
- [ ] Add `--mode` flag (hybrid/semantic/keyword)
- [ ] Handle edge cases (empty results, single source)
- [ ] Write unit tests for RRF algorithm
- [ ] Write integration tests for hybrid search
- [ ] Benchmark hybrid vs pure semantic

## Success Criteria

- [ ] Hybrid search enabled by default
- [ ] Improved handling of exact matches
- [ ] Configurable semantic/keyword weights
- [ ] Minimal latency increase (< 50ms)
- [ ] BM25 index updates with document indexing

## Dependencies

- F-005: Semantic Search
- sqlite3 (built-in)

## Technical Notes

### Configuration

```yaml
search:
  mode: hybrid          # hybrid | semantic | keyword
  hybrid:
    semantic_weight: 0.7
    keyword_weight: 0.3
    rrf_k: 60
    bm25_k1: 1.2
    bm25_b: 0.75
```

### CLI

```bash
# Default hybrid search
ragd search "authentication error E1234"

# Pure semantic
ragd search "what is machine learning" --mode semantic

# Pure keyword
ragd search "error code E1234" --mode keyword

# Adjust weights
ragd search "query" --semantic-weight 0.8
```

### Data Model

```python
@dataclass
class HybridSearchResult:
    content: str
    semantic_score: float
    keyword_score: float
    combined_score: float
    rrf_rank: int
    source: SourceMetadata
```

### BM25 Index Schema

```sql
CREATE VIRTUAL TABLE chunks_fts USING fts5(
    content,
    chunk_id UNINDEXED,
    document_id UNINDEXED,
    tokenize='porter unicode61'
);
```

## Related Documentation

- [ADR-0007: Advanced Retrieval Techniques](../../decisions/adrs/0007-advanced-retrieval-techniques.md)
- [F-010: Contextual Retrieval](./F-010-contextual-retrieval.md)
- [F-011: Late Chunking](./F-011-late-chunking.md)
- [F-005: Semantic Search](../completed/F-005-semantic-search.md)

---
