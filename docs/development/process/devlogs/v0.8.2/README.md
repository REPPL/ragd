# Devlog: v0.8.2 Retrieval Enhancements

**Date:** 2025-12-03
**Version:** 0.8.2
**Theme:** Intelligence & Organisation - Retrieval Enhancements

## The Story

v0.8.2 focuses on what happens *after* initial retrieval. You've got 50 potentially relevant documents - now what? Two techniques help refine this list:

1. **Reranking** - A second-pass model that looks at query-document pairs more carefully
2. **Query Decomposition** - Breaking complex questions into simpler sub-questions

## What We Built

### Cross-Encoder Reranking (F-065)

The initial retrieval uses bi-encoders: separate embeddings for query and documents, compared via cosine similarity. Fast, but shallow.

Cross-encoders process the query and each document *together*, allowing deeper semantic understanding:

```python
from ragd.search import rerank

# Over-fetch, then rerank
results = hybrid_search(query, limit=50)
top_10 = rerank(query, results, top_k=10)
```

The model is lazy-loaded - no startup cost unless you actually rerank. And if the model isn't available, it gracefully returns the original order.

### Query Decomposition (F-066)

Complex queries often hide multiple information needs. Consider:

> "Compare JWT vs session authentication for security and performance"

This actually asks four things:
1. JWT security
2. Session security
3. JWT performance
4. Session performance

The decomposer identifies patterns and breaks queries down:

```python
from ragd.search import decompose_query

sub_queries = decompose_query("JWT vs sessions for security")
# [SubQuery(text="JWT security"), SubQuery(text="sessions security")]
```

Results from each sub-query are aggregated, de-duplicated, and sorted by combined relevance. Each result tracks *which* sub-queries found it.

## Technical Decisions

**Rule-based first**: LLM decomposition is optional. Simple regex patterns catch most comparison and conjunction queries. No model dependency for basic functionality.

**Aggregation strategies**: Multiple ways to combine scores:
- MAX: Take the best score (conservative)
- SUM: Reward documents found by multiple sub-queries
- WEIGHTED: Weight earlier sub-queries higher

**No CLI integration yet**: Both features are API-only for now. CLI flags would add complexity; better to prove the value first.

## The Numbers

- 44 new tests
- 1201 total tests passing
- ~2 hours implementation time
- Zero breaking changes

## Looking Ahead

The retrieval pipeline is now:
1. **Embed** - Query to vector (existing)
2. **Search** - Hybrid semantic + BM25 (existing)
3. **Rerank** - Cross-encoder precision (new)
4. **Decompose** - Multi-aspect coverage (new)

v0.8.5 adds the intelligence layer: knowledge graphs and dual-index architecture. The foundation is solid.

---

*~2 hours of focussed implementation*
