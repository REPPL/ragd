# F-070: Backend Recommendation CLI

## Overview

**Milestone**: v0.6.0
**Priority**: P2
**Depends On**: [F-021](./F-021-vector-store-abstraction.md)

## Problem Statement

Users may not know which vector store backend is optimal for their use case. ragd should recommend backends based on collection size, hardware capabilities, and usage patterns.

## Design Approach

### CLI Commands

```bash
ragd backend recommend --verbose    # Analyse and recommend
ragd backend profile chromadb faiss # Compare performance
```

### Recommendation Logic

Based on:
- **Collection size**: Documents, chunks, embeddings
- **Hardware tier**: RAM, CPU cores, GPU availability
- **Usage patterns**: Metadata-heavy vs speed-priority

### Recommendation Rules

| Collection Size | RAM | Recommendation |
|-----------------|-----|----------------|
| < 10K chunks | Any | ChromaDB (simpler) |
| 10K-100K | < 16GB | ChromaDB |
| 10K-100K | >= 16GB | FAISS (faster) |
| > 100K | Any | FAISS (required) |

## Implementation Tasks

- [ ] Create `src/ragd/storage/recommend.py`
- [ ] Implement hardware detection (RAM, CPU, GPU)
- [ ] Implement collection size analysis
- [ ] Create `ragd backend recommend` command
- [ ] Create `ragd backend profile` command
- [ ] Add Rich output formatting
- [ ] Write unit tests

## Success Criteria

- [ ] `ragd backend recommend` provides actionable guidance
- [ ] Recommendations based on actual hardware and data
- [ ] Profile command shows comparative metrics

## Related Documentation

- [F-021: Vector Store Abstraction](./F-021-vector-store-abstraction.md)
- [F-073: Performance Profiler](./F-073-performance-profiler.md)

---
