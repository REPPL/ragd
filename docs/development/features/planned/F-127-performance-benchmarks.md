# F-127: Performance Benchmarks

## Overview

**Milestone**: v1.0
**Priority**: P1
**Depends On**: F-123 (Performance Profiling)
**Environment**: Apple Silicon (Local Mac only)

## Problem Statement

Production release needs published performance data:
- Users need to know expected performance characteristics
- No baseline for detecting performance regressions
- Cannot compare ragd to alternatives without benchmarks
- Optimisation claims need evidence

## Design Approach

**Comprehensive benchmark suite:**
- Indexing benchmarks (throughput, memory)
- Search benchmarks (latency percentiles, QPS)
- Chat benchmarks (response time)
- Startup benchmarks (cold/warm)

**Publication:**
- Results documented in `docs/reference/benchmarks.md`
- Environment clearly specified (Apple Silicon Mac)
- Reproducible benchmark scripts included

## Implementation Tasks

- [ ] Create `tests/benchmarks/` directory structure
- [ ] Implement `indexing_benchmark.py` (small, medium datasets)
- [ ] Implement `search_benchmark.py` (latency p50/p95/p99, QPS)
- [ ] Implement `chat_benchmark.py` (response time)
- [ ] Implement `startup_benchmark.py` (cold/warm)
- [ ] Create `src/ragd/benchmark/runner.py` for orchestration
- [ ] Create benchmark data fixtures (100 docs, 1K docs)
- [ ] Run full benchmark suite on Apple Silicon
- [ ] Create `docs/reference/benchmarks.md` with results
- [ ] Add `ragd benchmark` CLI command
- [ ] Write documentation for running benchmarks

## Success Criteria

- [ ] Benchmark suite covers indexing, search, chat, startup
- [ ] Results published in docs/reference/benchmarks.md
- [ ] Environment documented (Apple M-series, RAM, macOS version)
- [ ] Benchmarks reproducible (`ragd benchmark all`)
- [ ] Latency percentiles (p50, p95, p99) calculated
- [ ] Memory usage tracked for all benchmarks
- [ ] Results include methodology explanation

## Dependencies

- F-123 (Performance Profiling) - uses profiling framework
- F-124 (Memory Optimisation) - memory benchmarks use tracking
- F-126 (Bug Fixes) - run after bugs fixed for accurate results

## Technical Notes

### Benchmark Suite

| Benchmark | Dataset | Metrics |
|-----------|---------|---------|
| index-small | 100 docs | time, memory, docs/sec |
| index-medium | 1K docs | time, memory, throughput |
| search-latency | 100 queries | p50, p95, p99 (ms) |
| search-throughput | 1K queries | QPS |
| chat-response | 50 questions | mean, p95 response time |
| startup-cold | - | time to --version (cold) |
| startup-warm | - | time to --version (warm) |

### Benchmark Implementation

```python
# tests/benchmarks/indexing_benchmark.py
import time
from pathlib import Path
from ragd.performance.memory import track_memory

def benchmark_indexing(docs_path: Path, iterations: int = 3) -> dict:
    """Benchmark document indexing."""
    times = []
    memory_deltas = []
    doc_count = len(list(docs_path.glob("*")))

    for _ in range(iterations):
        with track_memory() as mem:
            start = time.perf_counter()
            # Run indexing
            index_documents(docs_path)
            elapsed = time.perf_counter() - start

        times.append(elapsed)
        memory_deltas.append(mem["delta_mb"])

    return {
        "benchmark": "indexing",
        "document_count": doc_count,
        "iterations": iterations,
        "time_mean_s": statistics.mean(times),
        "time_stdev_s": statistics.stdev(times) if len(times) > 1 else 0,
        "docs_per_second": doc_count / statistics.mean(times),
        "memory_peak_mb": max(memory_deltas),
    }
```

### Latency Percentiles

```python
def calculate_percentiles(latencies: list[float]) -> dict:
    """Calculate latency percentiles."""
    sorted_lat = sorted(latencies)
    n = len(sorted_lat)
    return {
        "p50_ms": sorted_lat[int(n * 0.50)],
        "p95_ms": sorted_lat[int(n * 0.95)],
        "p99_ms": sorted_lat[int(n * 0.99)] if n >= 100 else sorted_lat[-1],
        "mean_ms": statistics.mean(sorted_lat),
        "min_ms": min(sorted_lat),
        "max_ms": max(sorted_lat),
    }
```

### Published Results Format

```markdown
# ragd v1.0.0 Performance Benchmarks

## Environment

| Component | Specification |
|-----------|--------------|
| CPU | Apple M2 Pro |
| RAM | 16GB |
| OS | macOS 14.x |
| Python | 3.12.x |
| ragd | 1.0.0 |

## Indexing Performance

| Benchmark | Docs | Time | Throughput | Peak Memory |
|-----------|------|------|------------|-------------|
| index-small | 100 | X.Xs | X.X docs/s | XXX MB |
| index-medium | 1,000 | X.Xs | X.X docs/s | XXX MB |

## Search Performance

| Metric | Value |
|--------|-------|
| p50 latency | X.X ms |
| p95 latency | X.X ms |
| p99 latency | X.X ms |
| Throughput | X.X QPS |

## Startup Performance

| Metric | Time |
|--------|------|
| Cold start (`--version`) | XXX ms |
| Warm start (`--version`) | XXX ms |
| First search | X.X s |

## Methodology

Benchmarks run with:
- Fresh ragd installation
- Default configuration
- 3 iterations per benchmark (mean reported)
- Memory tracked via psutil
```

### CLI Command

```bash
# Run all benchmarks
ragd benchmark all --output benchmarks.json

# Run specific benchmark
ragd benchmark indexing --docs ./test_docs/ --iterations 5
ragd benchmark search --queries 100
ragd benchmark startup --iterations 10

# Generate markdown report
ragd benchmark report --input benchmarks.json --output benchmarks.md
```

## Related Documentation

- [F-123: Performance Profiling](./F-123-performance-profiling.md) - Foundation
- [F-124: Memory Optimisation](./F-124-memory-optimisation.md) - Memory tracking
- [F-125: Startup Time](./F-125-startup-time.md) - Startup benchmarks
- [v1.0.0 Milestone](../../milestones/v1.0.0.md)

---

**Status**: Planned
