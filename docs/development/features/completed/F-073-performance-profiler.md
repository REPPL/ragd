# F-073: Performance Profiler & Benchmarks

## Overview

**Milestone**: v0.6.0
**Priority**: P2
**Depends On**: [F-021](./F-021-vector-store-abstraction.md)

## Problem Statement

Users need objective data to compare backend performance. ragd should provide automated benchmarks measuring query latency, index build time, memory usage, and recall accuracy.

## Design Approach

### CLI Command

```bash
ragd backend profile chromadb faiss --queries 100
```

### Benchmark Metrics

| Metric | Target |
|--------|--------|
| Query latency p95 | < 10ms (FAISS), < 50ms (ChromaDB) |
| Index build (100K) | < 30 minutes |
| Memory (1M vectors) | < 3GB |
| Recall@10 | > 95% |

### Output Format

```
Backend Comparison (1000 queries, 10K vectors)
──────────────────────────────────────────────

                ChromaDB    FAISS
Query p50         12ms       3ms
Query p95         45ms       8ms
Query p99         89ms      12ms
Memory           512MB     128MB
Index build        15s       8s
Recall@10         97%       96%

Recommendation: FAISS (3.8x faster queries)
```

### Benchmark Test Suite

```
tests/benchmarks/
├── conftest.py           # Fixtures
├── test_query_latency.py
├── test_index_build.py
├── test_memory.py
└── test_recall.py
```

## Implementation Tasks

- [ ] Create `src/ragd/storage/profiler.py`
- [ ] Implement latency profiling
- [ ] Implement memory tracking
- [ ] Implement recall calculation
- [ ] Create `ragd backend profile` command
- [ ] Create benchmark test suite
- [ ] Add `--benchmark` pytest marker
- [ ] Write unit tests

## Success Criteria

- [ ] Profile command provides comparative metrics
- [ ] Benchmarks reproducible via pytest
- [ ] Results inform backend recommendation
- [ ] Memory tracking accurate

## Related Documentation

- [F-021: Vector Store Abstraction](./F-021-vector-store-abstraction.md)
- [F-070: Backend Recommendation](./F-070-backend-recommendation.md)

---
