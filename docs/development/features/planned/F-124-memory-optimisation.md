# F-124: Memory Optimisation

## Overview

**Milestone**: v1.0
**Priority**: P1
**Depends On**: F-123 (Performance Profiling)

## Problem Statement

Peak memory usage during operations affects usability:
- Large document collections can cause memory pressure
- Embedding generation loads entire batches into memory
- PDF processing may load large files entirely
- Users on memory-constrained systems (8GB) may experience issues
- No visibility into memory consumption patterns

## Design Approach

**Target: Peak memory < 1GB for typical workloads.**

**Optimisation strategies:**
1. Streaming embeddings - process in smaller batches
2. Page-by-page PDF processing - don't load entire documents
3. Explicit garbage collection at key points
4. Configurable memory limits and batch sizes

**Memory tracking utilities:**
- Real-time memory monitoring
- Peak tracking across operations
- Memory budget enforcement (warning/abort on exceed)

## Implementation Tasks

- [ ] Create `src/ragd/performance/memory.py` with tracking utilities
- [ ] Implement `get_current_memory_mb()` and `get_peak_memory_mb()`
- [ ] Implement `track_memory()` context manager
- [ ] Create `src/ragd/embedding/streaming.py` for streaming embeddings
- [ ] Create `src/ragd/ingestion/pdf_streaming.py` for page-by-page PDF
- [ ] Add MemoryConfig section to config.py
- [ ] Add memory budget warnings/enforcement
- [ ] Add `--memory-limit` flag to relevant CLI commands
- [ ] Profile current memory usage (baseline)
- [ ] Optimise top memory consumers identified
- [ ] Write unit tests for memory utilities
- [ ] Write integration tests comparing streaming vs batch
- [ ] Document memory configuration options

## Success Criteria

- [ ] Peak memory < 1GB for indexing 100 typical documents
- [ ] Peak memory < 500MB for search operations
- [ ] Streaming embedding reduces peak by ≥ 30% vs batch
- [ ] Memory budget enforcement works (warn at threshold)
- [ ] `ragd profile` shows memory delta for all operations
- [ ] Large PDF (100+ pages) processed without memory spike
- [ ] Test coverage ≥ 90% for new code

## Dependencies

- F-123 (Performance Profiling) - for measurement
- psutil (already installed)

## Technical Notes

### Memory Tracking

```python
# memory.py
import gc
import psutil
import os
from contextlib import contextmanager
from typing import Generator

def get_current_memory_mb() -> float:
    """Current RSS memory in MB."""
    return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)

def get_peak_memory_mb() -> float:
    """Peak memory (platform-specific)."""
    import resource
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # macOS: bytes

@contextmanager
def track_memory(gc_before: bool = True) -> Generator[dict, None, None]:
    """Track memory delta during operation."""
    if gc_before:
        gc.collect()
    start = get_current_memory_mb()
    result = {"start_mb": start, "peak_mb": start}
    try:
        yield result
    finally:
        gc.collect()
        result["end_mb"] = get_current_memory_mb()
        result["delta_mb"] = result["end_mb"] - start
```

### Streaming Embeddings

```python
# streaming.py
def embed_streaming(
    texts: Iterable[str],
    model: SentenceTransformer,
    batch_size: int = 32
) -> Generator[list[float], None, None]:
    """Generate embeddings in streaming fashion."""
    batch = []
    for text in texts:
        batch.append(text)
        if len(batch) >= batch_size:
            embeddings = model.encode(batch)
            for emb in embeddings:
                yield emb.tolist()
            batch = []
    if batch:
        embeddings = model.encode(batch)
        for emb in embeddings:
            yield emb.tolist()
```

### Config Additions

```yaml
# ragd.yaml
memory:
  max_peak_mb: 2048        # Warn if exceeded
  streaming_threshold_mb: 100  # Use streaming above this
  embedding_batch_size: 32     # Batch size for embeddings
  gc_frequency: per_document   # When to run gc
```

## Related Documentation

- [F-123: Performance Profiling](./F-123-performance-profiling.md) - Measurement framework
- [F-125: Startup Time](./F-125-startup-time.md) - Related optimisation
- [v1.0.0 Milestone](../../milestones/v1.0.0.md)

---

**Status**: Planned
