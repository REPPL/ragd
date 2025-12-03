"""Performance profiler for vector store operations.

This module provides benchmarking and profiling capabilities for
comparing storage backend performance across operations.
"""

from __future__ import annotations

import logging
import statistics
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from ragd.storage.protocols import VectorStore
from ragd.storage.types import VectorSearchResult

logger = logging.getLogger(__name__)


@dataclass
class OperationMetrics:
    """Metrics for a single operation type."""

    operation: str
    count: int = 0
    total_time_ms: float = 0.0
    times_ms: list[float] = field(default_factory=list)

    @property
    def mean_ms(self) -> float:
        """Mean execution time in milliseconds."""
        return statistics.mean(self.times_ms) if self.times_ms else 0.0

    @property
    def median_ms(self) -> float:
        """Median execution time in milliseconds."""
        return statistics.median(self.times_ms) if self.times_ms else 0.0

    @property
    def min_ms(self) -> float:
        """Minimum execution time in milliseconds."""
        return min(self.times_ms) if self.times_ms else 0.0

    @property
    def max_ms(self) -> float:
        """Maximum execution time in milliseconds."""
        return max(self.times_ms) if self.times_ms else 0.0

    @property
    def std_ms(self) -> float:
        """Standard deviation of execution time in milliseconds."""
        if len(self.times_ms) < 2:
            return 0.0
        return statistics.stdev(self.times_ms)

    @property
    def ops_per_second(self) -> float:
        """Operations per second throughput."""
        if self.total_time_ms == 0:
            return 0.0
        return (self.count / self.total_time_ms) * 1000

    def record(self, duration_ms: float) -> None:
        """Record an operation duration.

        Args:
            duration_ms: Duration in milliseconds
        """
        self.count += 1
        self.total_time_ms += duration_ms
        self.times_ms.append(duration_ms)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "operation": self.operation,
            "count": self.count,
            "total_time_ms": self.total_time_ms,
            "mean_ms": self.mean_ms,
            "median_ms": self.median_ms,
            "min_ms": self.min_ms,
            "max_ms": self.max_ms,
            "std_ms": self.std_ms,
            "ops_per_second": self.ops_per_second,
        }


@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""

    backend: str
    metrics: dict[str, OperationMetrics] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_metric(self, operation: str) -> OperationMetrics:
        """Get or create metrics for an operation.

        Args:
            operation: Operation name

        Returns:
            OperationMetrics instance
        """
        if operation not in self.metrics:
            self.metrics[operation] = OperationMetrics(operation=operation)
        return self.metrics[operation]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "backend": self.backend,
            "metrics": {k: v.to_dict() for k, v in self.metrics.items()},
            "metadata": self.metadata,
        }


class StorageProfiler:
    """Profiler for vector store operations.

    Measures performance of common operations:
    - add: Adding vectors
    - search: Vector similarity search
    - delete: Deleting vectors
    - get_stats: Retrieving statistics
    - health_check: Health check latency
    """

    def __init__(self, store: VectorStore, backend_name: str | None = None):
        """Initialise profiler.

        Args:
            store: VectorStore instance to profile
            backend_name: Name for reporting (auto-detected if None)
        """
        self.store = store
        self.backend_name = backend_name or type(store).__name__
        self.result = BenchmarkResult(backend=self.backend_name)

    def _time_operation(
        self,
        operation: str,
        func: Callable[[], Any],
        warmup: int = 0,
    ) -> Any:
        """Time an operation.

        Args:
            operation: Operation name for recording
            func: Function to time
            warmup: Number of warmup iterations

        Returns:
            Result from the function
        """
        # Warmup iterations
        for _ in range(warmup):
            func()

        # Timed iteration
        start = time.perf_counter()
        result = func()
        duration_ms = (time.perf_counter() - start) * 1000

        self.result.get_metric(operation).record(duration_ms)
        return result

    def benchmark_add(
        self,
        vectors: list[list[float]],
        ids: list[str],
        contents: list[str],
        metadatas: list[dict[str, Any]],
        batch_size: int = 100,
    ) -> None:
        """Benchmark vector addition.

        Args:
            vectors: Vectors to add
            ids: Vector IDs
            contents: Text contents
            metadatas: Metadata dictionaries
            batch_size: Batch size for operations
        """
        total = len(vectors)

        for i in range(0, total, batch_size):
            end = min(i + batch_size, total)
            batch_vectors = vectors[i:end]
            batch_ids = ids[i:end]
            batch_contents = contents[i:end]
            batch_metadatas = metadatas[i:end]

            self._time_operation(
                "add",
                lambda emb=batch_vectors, idx=batch_ids, c=batch_contents, m=batch_metadatas: self.store.add(
                    ids=idx,
                    embeddings=emb,
                    contents=c,
                    metadatas=m,
                ),
            )

        self.result.metadata["add_total_vectors"] = total
        self.result.metadata["add_batch_size"] = batch_size

    def benchmark_search(
        self,
        queries: list[list[float]],
        limit: int = 10,
        iterations: int = 1,
    ) -> list[list[VectorSearchResult]]:
        """Benchmark vector search.

        Args:
            queries: Query vectors
            limit: Number of results per query
            iterations: Number of times to run each query

        Returns:
            Search results from last iteration
        """
        all_results = []

        for _ in range(iterations):
            for query in queries:
                results = self._time_operation(
                    "search",
                    lambda q=query, lim=limit: self.store.search(q, limit=lim),
                )
                all_results.append(results)

        self.result.metadata["search_limit"] = limit
        self.result.metadata["search_queries"] = len(queries)
        self.result.metadata["search_iterations"] = iterations

        return all_results

    def benchmark_delete(self, ids: list[str], batch_size: int = 100) -> None:
        """Benchmark vector deletion.

        Args:
            ids: IDs to delete
            batch_size: Batch size for operations
        """
        total = len(ids)

        for i in range(0, total, batch_size):
            end = min(i + batch_size, total)
            batch_ids = ids[i:end]

            self._time_operation(
                "delete",
                lambda idx=batch_ids: self.store.delete(idx),
            )

        self.result.metadata["delete_total"] = total
        self.result.metadata["delete_batch_size"] = batch_size

    def benchmark_health_check(self, iterations: int = 10) -> None:
        """Benchmark health check latency.

        Args:
            iterations: Number of health checks to run
        """
        for _ in range(iterations):
            self._time_operation(
                "health_check",
                self.store.health_check,
            )

        self.result.metadata["health_check_iterations"] = iterations

    def benchmark_get_stats(self, iterations: int = 10) -> None:
        """Benchmark get_stats latency.

        Args:
            iterations: Number of stats calls to run
        """
        for _ in range(iterations):
            self._time_operation(
                "get_stats",
                self.store.get_stats,
            )

        self.result.metadata["get_stats_iterations"] = iterations

    def get_results(self) -> BenchmarkResult:
        """Get benchmark results.

        Returns:
            BenchmarkResult with all recorded metrics
        """
        return self.result

    def print_summary(self) -> None:
        """Print a summary of benchmark results."""
        print(f"\n=== Benchmark Results: {self.backend_name} ===\n")

        for name, metric in self.result.metrics.items():
            print(f"{name}:")
            print(f"  Count: {metric.count}")
            print(f"  Mean: {metric.mean_ms:.2f}ms")
            print(f"  Median: {metric.median_ms:.2f}ms")
            print(f"  Min/Max: {metric.min_ms:.2f}ms / {metric.max_ms:.2f}ms")
            print(f"  Std Dev: {metric.std_ms:.2f}ms")
            print(f"  Throughput: {metric.ops_per_second:.1f} ops/sec")
            print()


def compare_backends(
    results: list[BenchmarkResult],
    operation: str = "search",
) -> dict[str, Any]:
    """Compare benchmark results across backends.

    Args:
        results: List of benchmark results
        operation: Operation to compare

    Returns:
        Comparison dictionary
    """
    comparison = {
        "operation": operation,
        "backends": {},
    }

    best_mean = float("inf")
    best_backend = None

    for result in results:
        metric = result.metrics.get(operation)
        if metric:
            comparison["backends"][result.backend] = {
                "mean_ms": metric.mean_ms,
                "median_ms": metric.median_ms,
                "ops_per_second": metric.ops_per_second,
            }
            if metric.mean_ms < best_mean:
                best_mean = metric.mean_ms
                best_backend = result.backend

    comparison["fastest"] = best_backend
    comparison["best_mean_ms"] = best_mean

    return comparison
