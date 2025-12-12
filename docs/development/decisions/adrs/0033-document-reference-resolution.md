# ADR-0033: Document Reference Resolution Strategy

## Status

Accepted

## Context

The chat system's reference resolver correctly identifies document references (e.g., "hummel paper" resolves to `hummel-et-al-2021-data-sovereignty.pdf`), but this resolution was only passed to a small LLM for query rewriting. Small LLMs (3B parameters) often ignored the resolved filename, causing search failures.

**Original Flow:**
```
User: "tell me more about the hummel paper"
  → Reference resolver: "hummel paper" → "hummel-et-al-2021.pdf" ✓
  → LLM query rewrite: Gets filename but ignores it ✗
  → Search: "tell me more about the hummel paper" (unchanged)
  → BM25/semantic: No matches
  → Fallback (0.35 threshold): Returns irrelevant documents
```

**Root Cause:** The system relied entirely on LLM cooperation to use resolved references, creating a single point of failure.

## Decision

Implement a **Hybrid Approach with Fast-Path Optimisation**:

1. **Fast-Path (>=0.9 confidence):** Direct document filtering, bypassing LLM entirely
2. **Boost Path (0.6-0.9 confidence):** Apply document boost in RRF scoring
3. **Fallback (<0.6 confidence):** Continue with existing LLM-based rewriting

### Implementation

**New retrieval cascade:**

1. **Step 0a (Fast-path):** If reference resolver returns >=0.9 confidence matches, filter search results to only those documents
2. **Step 0b (Boost):** For 0.6-0.9 confidence matches, apply document boosts to RRF scoring
3. **Step 1:** Rewritten query with boosting (if applicable)
4. **Step 2:** Original query fallback
5. **Step 3:** Lowered threshold fallback

**Files modified:**
- `src/ragd/search/bm25.py` - Added `document_ids` parameter for multi-document filtering
- `src/ragd/search/hybrid.py` - Added `document_ids` and `document_boosts` parameters
- `src/ragd/chat/session.py` - Integrated reference resolution with retrieval

## Alternatives Considered

### Approach 1: Direct Filter Only

Filter to resolved documents when confidence >= 0.8, bypassing LLM entirely.

| Aspect | Assessment |
|--------|------------|
| Benefits | 100% reliable for high-confidence; fastest; simple |
| Downsides | Binary decision; loses semantic richness; poor multi-document handling |

**Rejected:** Too aggressive filtering loses cross-document insights.

### Approach 2: Query Augmentation

Append resolved filenames directly to the search query string.

| Aspect | Assessment |
|--------|------------|
| Benefits | Leverages BM25 effectively; minimal code changes |
| Downsides | Query pollution; unnatural embeddings; filename tokens dominate |

**Rejected:** Pollutes semantic search quality.

### Approach 3: Hybrid Boosting (Chosen)

Use resolved references as scoring boosts in RRF, with optional hard filter for very high confidence.

| Aspect | Assessment |
|--------|------------|
| Benefits | Best of both worlds; graceful confidence scaling; preserves cross-document insights |
| Downsides | More complex; requires tuning |

**Accepted:** Best balance of reliability and semantic richness.

## Consequences

### Positive

- Reliable document reference resolution regardless of LLM quality
- Graceful degradation across confidence levels
- Preserves semantic richness for complex follow-up queries
- Aligns with F-040 Long-Term Memory architecture (preference boosting)

### Negative

- Increased complexity in retrieval cascade
- Additional strategy types to track ("reference_filter", "rewritten_boosted")

### Neutral

- Hardcoded thresholds (0.9, 0.6) may need tuning per deployment
- Performance impact negligible (confidence check is O(1))

## Related Documentation

- [Reference Resolver](../../../src/ragd/chat/reference_resolver.py) - Document matching implementation
- [ADR-0007](./0007-advanced-retrieval-techniques.md) - Hybrid search architecture
- [F-040](../../features/planned/F-040-long-term-memory.md) - Future memory system compatibility

---

**Status**: Accepted
