# F-081: Query Decomposition

## Problem Statement

Complex queries often contain multiple information needs. A single vector search may not capture all aspects of "What are the security implications of using OAuth for a Python REST API?".

Query decomposition breaks such queries into sub-queries, retrieves for each, and aggregates results.

## Design Approach

### Decomposition Strategies

1. **Rule-Based Decomposition**
   - Split on conjunctions (and, also, as well as)
   - Identify question components
   - Fast, no model dependency

2. **LLM-Based Decomposition**
   - Use local LLM to identify sub-questions
   - Higher quality, slower
   - Falls back to rule-based if unavailable

### Result Aggregation

After retrieving for each sub-query, combine results:
- De-duplicate by chunk_id
- Score aggregation (max, weighted sum)
- Maintain provenance (which sub-query found each result)

### Example

Input: "Compare JWT vs session-based auth for security and performance"

Decomposition:
1. "JWT authentication security"
2. "Session-based authentication security"
3. "JWT authentication performance"
4. "Session-based authentication performance"

Results merged with provenance tracking.

## Implementation Tasks

- [x] Create `src/ragd/search/decompose.py` with QueryDecomposer
- [x] Implement rule-based decomposition
- [x] Implement LLM-based decomposition (optional)
- [x] Add result aggregation with de-duplication
- [x] Integrate with `HybridSearcher` via `decompose` parameter
- [x] Add CLI flag `--decompose` to search command
- [x] Write comprehensive tests

## Success Criteria

- [x] Complex queries return more relevant results
- [x] Sub-query provenance tracked in results
- [x] Rule-based works without LLM dependency
- [x] LLM decomposition quality validated

## Dependencies

- ragd.llm (for LLM-based decomposition)
- Existing query parsing infrastructure

## Related Documentation

- [F-080: Cross-Encoder Reranking](./F-080-cross-encoder-reranking.md)
- [Search Syntax Reference](../../../reference/search-syntax.md)

---

**Status**: Completed
