# F-065: Cross-Encoder Reranking

## Problem Statement

Initial retrieval (bi-encoder semantic search + BM25) casts a wide net but doesn't deeply analyse query-document relationships. Cross-encoder reranking examines query-document pairs more thoroughly, significantly improving precision at the cost of speed.

## Design Approach

### Cross-Encoder Architecture

Cross-encoders process query and document together (unlike bi-encoders that encode separately):

```
Query + Document → Cross-Encoder → Relevance Score
```

This allows deeper semantic understanding at the cost of O(n) inference calls per query.

### Integration Strategy

Add reranking as an optional post-processing step after hybrid search:

```python
results = searcher.search(query, limit=50)  # Over-fetch
reranked = reranker.rerank(query, results, top_k=10)  # Precise selection
```

### Model Selection

Default to cross-encoder models from sentence-transformers:
- `cross-encoder/ms-marco-MiniLM-L-6-v2` - Fast, good quality
- `cross-encoder/ms-marco-TinyBERT-L-2-v2` - Very fast, acceptable quality
- `BAAI/bge-reranker-base` - High quality, slower

## Implementation Tasks

- [x] Create `src/ragd/search/rerank.py` with Reranker class
- [x] Support cross-encoder models from sentence-transformers
- [x] Add `RerankerConfig` for model selection and parameters
- [x] Integrate with `HybridSearcher.search()` via `rerank` parameter
- [x] Add CLI flag `--rerank` to search command
- [x] Write comprehensive tests

## Success Criteria

- [x] Reranking improves precision@10 on test queries
- [x] Graceful degradation when reranker unavailable
- [x] Performance < 200ms for 50 candidates on CPU
- [x] Model lazy-loading to avoid startup cost

## Dependencies

- sentence-transformers (already available)
- torch (already available)

## Related Documentation

- [HybridSearcher](../../../reference/search/hybrid.md)
- [State-of-the-Art RAG](../../research/state-of-the-art-rag.md)

---

**Status**: Completed
