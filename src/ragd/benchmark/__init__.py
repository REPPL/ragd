"""Performance benchmark module for ragd (F-127).

Provides benchmark runners and reporters for measuring:
- Indexing throughput (docs/sec)
- Search latency (p50, p95, p99)
- Chat response time
- Startup time
"""

from ragd.benchmark.runner import (
    BenchmarkResult,
    BenchmarkRunner,
    BenchmarkSuite,
    IndexingBenchmark,
    SearchBenchmark,
    StartupBenchmark,
)

__all__ = [
    "BenchmarkResult",
    "BenchmarkRunner",
    "BenchmarkSuite",
    "IndexingBenchmark",
    "SearchBenchmark",
    "StartupBenchmark",
]
