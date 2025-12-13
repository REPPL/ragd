"""Profile metrics dataclasses for ragd (F-123).

Provides structured metrics for different operation types:
- ProfileMetric: Base metric class
- IndexingProfile: Document indexing metrics
- SearchProfile: Search operation metrics
- ChatProfile: Chat/LLM response metrics
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProfileMetric:
    """Base class for profile metrics.

    Tracks timing and memory for a named operation with
    support for multiple measurements and statistical analysis.
    """

    name: str
    operation: str
    times_ms: list[float] = field(default_factory=list)
    memory_deltas_mb: list[float] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def record(
        self,
        duration_ms: float,
        memory_delta_mb: float | None = None,
    ) -> None:
        """Record a measurement.

        Args:
            duration_ms: Duration in milliseconds
            memory_delta_mb: Memory delta in megabytes (optional)
        """
        self.times_ms.append(duration_ms)
        if memory_delta_mb is not None:
            self.memory_deltas_mb.append(memory_delta_mb)

    @property
    def count(self) -> int:
        """Number of measurements recorded."""
        return len(self.times_ms)

    @property
    def total_ms(self) -> float:
        """Total time in milliseconds."""
        return sum(self.times_ms)

    @property
    def mean_ms(self) -> float:
        """Mean time in milliseconds."""
        return statistics.mean(self.times_ms) if self.times_ms else 0.0

    @property
    def median_ms(self) -> float:
        """Median time in milliseconds."""
        return statistics.median(self.times_ms) if self.times_ms else 0.0

    @property
    def min_ms(self) -> float:
        """Minimum time in milliseconds."""
        return min(self.times_ms) if self.times_ms else 0.0

    @property
    def max_ms(self) -> float:
        """Maximum time in milliseconds."""
        return max(self.times_ms) if self.times_ms else 0.0

    @property
    def stdev_ms(self) -> float:
        """Standard deviation in milliseconds."""
        if len(self.times_ms) < 2:
            return 0.0
        return statistics.stdev(self.times_ms)

    @property
    def p50_ms(self) -> float:
        """50th percentile (median) in milliseconds."""
        return self.median_ms

    @property
    def p95_ms(self) -> float:
        """95th percentile in milliseconds."""
        if not self.times_ms:
            return 0.0
        sorted_times = sorted(self.times_ms)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[min(idx, len(sorted_times) - 1)]

    @property
    def p99_ms(self) -> float:
        """99th percentile in milliseconds."""
        if not self.times_ms:
            return 0.0
        sorted_times = sorted(self.times_ms)
        idx = int(len(sorted_times) * 0.99)
        return sorted_times[min(idx, len(sorted_times) - 1)]

    @property
    def memory_mean_mb(self) -> float | None:
        """Mean memory delta in megabytes."""
        if not self.memory_deltas_mb:
            return None
        return statistics.mean(self.memory_deltas_mb)

    @property
    def memory_max_mb(self) -> float | None:
        """Maximum memory delta in megabytes."""
        if not self.memory_deltas_mb:
            return None
        return max(self.memory_deltas_mb)

    @property
    def ops_per_second(self) -> float:
        """Operations per second throughput."""
        if self.total_ms == 0:
            return 0.0
        return (self.count / self.total_ms) * 1000

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "name": self.name,
            "operation": self.operation,
            "count": self.count,
            "total_ms": self.total_ms,
            "mean_ms": self.mean_ms,
            "median_ms": self.median_ms,
            "min_ms": self.min_ms,
            "max_ms": self.max_ms,
            "stdev_ms": self.stdev_ms,
            "p50_ms": self.p50_ms,
            "p95_ms": self.p95_ms,
            "p99_ms": self.p99_ms,
            "ops_per_second": self.ops_per_second,
            "metadata": self.metadata,
        }
        if self.memory_deltas_mb:
            result["memory_mean_mb"] = self.memory_mean_mb
            result["memory_max_mb"] = self.memory_max_mb
        return result


@dataclass
class IndexingProfile:
    """Metrics for document indexing operations.

    Tracks timing and throughput for the indexing pipeline:
    - Document parsing
    - Chunking
    - Embedding generation
    - Vector storage
    """

    document_count: int = 0
    chunk_count: int = 0
    total_bytes: int = 0
    parsing: ProfileMetric = field(
        default_factory=lambda: ProfileMetric("parsing", "index")
    )
    chunking: ProfileMetric = field(
        default_factory=lambda: ProfileMetric("chunking", "index")
    )
    embedding: ProfileMetric = field(
        default_factory=lambda: ProfileMetric("embedding", "index")
    )
    storage: ProfileMetric = field(
        default_factory=lambda: ProfileMetric("storage", "index")
    )
    total: ProfileMetric = field(
        default_factory=lambda: ProfileMetric("total", "index")
    )

    @property
    def docs_per_second(self) -> float:
        """Documents processed per second."""
        if self.total.total_ms == 0:
            return 0.0
        return (self.document_count / self.total.total_ms) * 1000

    @property
    def chunks_per_second(self) -> float:
        """Chunks processed per second."""
        if self.total.total_ms == 0:
            return 0.0
        return (self.chunk_count / self.total.total_ms) * 1000

    @property
    def bytes_per_second(self) -> float:
        """Bytes processed per second."""
        if self.total.total_ms == 0:
            return 0.0
        return (self.total_bytes / self.total.total_ms) * 1000

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "document_count": self.document_count,
            "chunk_count": self.chunk_count,
            "total_bytes": self.total_bytes,
            "docs_per_second": self.docs_per_second,
            "chunks_per_second": self.chunks_per_second,
            "bytes_per_second": self.bytes_per_second,
            "phases": {
                "parsing": self.parsing.to_dict(),
                "chunking": self.chunking.to_dict(),
                "embedding": self.embedding.to_dict(),
                "storage": self.storage.to_dict(),
                "total": self.total.to_dict(),
            },
        }


@dataclass
class SearchProfile:
    """Metrics for search operations.

    Tracks latency distribution and throughput for searches.
    """

    query_count: int = 0
    total_results: int = 0
    latency: ProfileMetric = field(
        default_factory=lambda: ProfileMetric("latency", "search")
    )
    embedding_time: ProfileMetric = field(
        default_factory=lambda: ProfileMetric("embedding_time", "search")
    )
    vector_search_time: ProfileMetric = field(
        default_factory=lambda: ProfileMetric("vector_search_time", "search")
    )
    rerank_time: ProfileMetric = field(
        default_factory=lambda: ProfileMetric("rerank_time", "search")
    )

    @property
    def qps(self) -> float:
        """Queries per second throughput."""
        return self.latency.ops_per_second

    @property
    def avg_results_per_query(self) -> float:
        """Average number of results per query."""
        if self.query_count == 0:
            return 0.0
        return self.total_results / self.query_count

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "query_count": self.query_count,
            "total_results": self.total_results,
            "qps": self.qps,
            "avg_results_per_query": self.avg_results_per_query,
            "latency": self.latency.to_dict(),
            "phases": {
                "embedding_time": self.embedding_time.to_dict(),
                "vector_search_time": self.vector_search_time.to_dict(),
                "rerank_time": self.rerank_time.to_dict(),
            },
        }


@dataclass
class ChatProfile:
    """Metrics for chat/LLM operations.

    Tracks response times for chat interactions.
    """

    message_count: int = 0
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    context_retrieval: ProfileMetric = field(
        default_factory=lambda: ProfileMetric("context_retrieval", "chat")
    )
    llm_response: ProfileMetric = field(
        default_factory=lambda: ProfileMetric("llm_response", "chat")
    )
    total: ProfileMetric = field(
        default_factory=lambda: ProfileMetric("total", "chat")
    )

    @property
    def tokens_per_second_in(self) -> float:
        """Input tokens per second."""
        if self.llm_response.total_ms == 0:
            return 0.0
        return (self.total_tokens_in / self.llm_response.total_ms) * 1000

    @property
    def tokens_per_second_out(self) -> float:
        """Output tokens per second."""
        if self.llm_response.total_ms == 0:
            return 0.0
        return (self.total_tokens_out / self.llm_response.total_ms) * 1000

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "message_count": self.message_count,
            "total_tokens_in": self.total_tokens_in,
            "total_tokens_out": self.total_tokens_out,
            "tokens_per_second_in": self.tokens_per_second_in,
            "tokens_per_second_out": self.tokens_per_second_out,
            "phases": {
                "context_retrieval": self.context_retrieval.to_dict(),
                "llm_response": self.llm_response.to_dict(),
                "total": self.total.to_dict(),
            },
        }


@dataclass
class StartupProfile:
    """Metrics for CLI startup time.

    Tracks cold and warm startup performance.
    """

    cold_start: ProfileMetric = field(
        default_factory=lambda: ProfileMetric("cold_start", "startup")
    )
    warm_start: ProfileMetric = field(
        default_factory=lambda: ProfileMetric("warm_start", "startup")
    )
    import_time: ProfileMetric = field(
        default_factory=lambda: ProfileMetric("import_time", "startup")
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "cold_start": self.cold_start.to_dict(),
            "warm_start": self.warm_start.to_dict(),
            "import_time": self.import_time.to_dict(),
        }


def calculate_percentiles(values: list[float]) -> dict[str, float]:
    """Calculate percentiles for a list of values.

    Args:
        values: List of numeric values

    Returns:
        Dictionary with p50, p95, p99, mean, min, max
    """
    if not values:
        return {
            "p50": 0.0,
            "p95": 0.0,
            "p99": 0.0,
            "mean": 0.0,
            "min": 0.0,
            "max": 0.0,
        }

    sorted_vals = sorted(values)
    n = len(sorted_vals)

    return {
        "p50": sorted_vals[int(n * 0.50)],
        "p95": sorted_vals[min(int(n * 0.95), n - 1)],
        "p99": sorted_vals[min(int(n * 0.99), n - 1)],
        "mean": statistics.mean(sorted_vals),
        "min": min(sorted_vals),
        "max": max(sorted_vals),
    }
