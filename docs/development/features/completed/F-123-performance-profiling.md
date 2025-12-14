# F-123: Performance Profiling

## Overview

**Milestone**: v1.0
**Priority**: P1
**Extends**: Existing StorageProfiler (src/ragd/storage/profiler.py)

## Problem Statement

Understanding performance characteristics is essential for production use:
- Users cannot identify bottlenecks in their workflows
- No visibility into where time is spent during indexing/search/chat
- Memory usage during operations is not tracked
- No way to compare performance across versions or configurations

## Design Approach

**Comprehensive profiling framework:**
- Extend existing StorageProfiler pattern to all operations
- Track both time and memory for each operation
- Export results to JSON for comparison
- Rich terminal reports for human analysis

**Key components:**
- `ProfileSession`: Container for related profiling measurements
- `OperationProfiler`: Context manager for timing operations
- `@profile` decorator: Easy profiling of functions
- CLI commands: `ragd profile index|search|chat|all`

## Implementation Tasks

- [ ] Create `src/ragd/performance/` module
- [ ] Implement ProfileSession class for grouping related metrics
- [ ] Implement OperationProfiler context manager
- [ ] Implement @profile decorator for function-level profiling
- [ ] Create ProfileMetric, IndexingProfile, SearchProfile, ChatProfile dataclasses
- [ ] Create report generator with Rich output
- [ ] Add `ragd profile` CLI command group
- [ ] Add JSON export/import for profile data
- [ ] Add profile comparison mode (show regression/improvement)
- [ ] Write unit tests for all profiler components
- [ ] Write integration tests for CLI commands
- [ ] Update CLI reference documentation

## Success Criteria

- [ ] `ragd profile index --path <file>` profiles indexing with timing/memory
- [ ] `ragd profile search --query <query>` profiles search operations
- [ ] `ragd profile all --output profile.json` runs full profile suite
- [ ] `ragd profile --compare baseline.json` compares against baseline
- [ ] Profile data exportable to JSON
- [ ] Memory delta tracked during operations
- [ ] Test coverage ≥ 90% for new code

## Dependencies

- psutil (already installed) - for memory tracking
- existing StorageProfiler patterns
- None for other phases

## Technical Notes

### Existing Foundation

`src/ragd/storage/profiler.py` already provides:
- `OperationMetrics` dataclass with timing
- `BenchmarkResult` dataclass
- `StorageProfiler` class with `_time_operation()` pattern
- JSON export capability

This will be generalised and extended.

### Memory Tracking

```python
import psutil
import os

def get_memory_mb() -> float:
    """Get current process memory in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

@contextmanager
def track_memory():
    """Track memory delta during operation."""
    start = get_memory_mb()
    result = {"start_mb": start}
    try:
        yield result
    finally:
        result["end_mb"] = get_memory_mb()
        result["delta_mb"] = result["end_mb"] - start
```

### CLI Commands

```bash
# Profile single operation
ragd profile index --path document.pdf [--iterations 3] [--output profile.json]
ragd profile search --query "test" [--iterations 10]
ragd profile chat --query "what is RAG?"

# Full profile suite
ragd profile all --output full_profile.json

# Compare against baseline
ragd profile --compare baseline.json
```

## Related Documentation

- [F-127: Performance Benchmarks](./F-127-performance-benchmarks.md) - Uses profiling framework
- [F-124: Memory Optimisation](../planned/F-124-memory-optimisation.md) - Uses memory tracking
- [v1.0.0 Milestone](../../milestones/v1.0.0.md)
- [Storage Profiler](../../../../src/ragd/storage/profiler.py) - Existing foundation

---

**Status**: Completed
