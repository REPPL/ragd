"""Benchmark runner for ragd (F-127).

Provides benchmark execution and reporting for performance testing.
"""

from __future__ import annotations

import gc
import json
import logging
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result from a benchmark run."""

    name: str
    iterations: int
    times_ms: list[float]
    memory_mb: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def mean_ms(self) -> float:
        """Mean execution time."""
        return statistics.mean(self.times_ms) if self.times_ms else 0.0

    @property
    def median_ms(self) -> float:
        """Median execution time."""
        return statistics.median(self.times_ms) if self.times_ms else 0.0

    @property
    def min_ms(self) -> float:
        """Minimum execution time."""
        return min(self.times_ms) if self.times_ms else 0.0

    @property
    def max_ms(self) -> float:
        """Maximum execution time."""
        return max(self.times_ms) if self.times_ms else 0.0

    @property
    def p50_ms(self) -> float:
        """50th percentile (median)."""
        return self._percentile(50)

    @property
    def p95_ms(self) -> float:
        """95th percentile."""
        return self._percentile(95)

    @property
    def p99_ms(self) -> float:
        """99th percentile."""
        return self._percentile(99)

    def _percentile(self, p: int) -> float:
        """Calculate percentile."""
        if not self.times_ms:
            return 0.0
        sorted_times = sorted(self.times_ms)
        k = (len(sorted_times) - 1) * p / 100
        f = int(k)
        c = f + 1 if f + 1 < len(sorted_times) else f
        return sorted_times[f] + (k - f) * (sorted_times[c] - sorted_times[f])

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "mean_ms": self.mean_ms,
            "median_ms": self.median_ms,
            "min_ms": self.min_ms,
            "max_ms": self.max_ms,
            "p50_ms": self.p50_ms,
            "p95_ms": self.p95_ms,
            "p99_ms": self.p99_ms,
            "memory_mb": self.memory_mb,
            "metadata": self.metadata,
        }


@dataclass
class IndexingBenchmark:
    """Indexing performance benchmark."""

    name: str = "indexing"
    doc_count: int = 100
    iterations: int = 3

    def run(self) -> BenchmarkResult:
        """Run indexing benchmark."""
        from ragd.config import load_config
        from ragd.embedding import get_embedder
        from ragd.ingestion import chunk_text
        from ragd.performance.memory import get_current_memory_mb

        config = load_config()
        embedder = get_embedder(config.embedding.model)

        # Generate test documents
        test_docs = [
            f"This is test document {i}. It contains some sample text for benchmarking. "
            f"The purpose is to measure indexing throughput and memory usage. "
            f"Document number {i} has unique content to ensure varied embedding."
            for i in range(self.doc_count)
        ]

        times_ms: list[float] = []
        memory_start = get_current_memory_mb()

        for _ in range(self.iterations):
            gc.collect()
            start = time.perf_counter()

            for doc in test_docs:
                chunks = chunk_text(doc, 200, 50)
                texts = [c.content for c in chunks]
                _embeddings = embedder.embed(texts)  # noqa: F841

            elapsed_ms = (time.perf_counter() - start) * 1000
            times_ms.append(elapsed_ms)

        memory_end = get_current_memory_mb()

        docs_per_sec = self.doc_count / (statistics.mean(times_ms) / 1000)

        return BenchmarkResult(
            name=self.name,
            iterations=self.iterations,
            times_ms=times_ms,
            memory_mb=memory_end - memory_start,
            metadata={
                "doc_count": self.doc_count,
                "docs_per_sec": docs_per_sec,
            },
        )


@dataclass
class SearchBenchmark:
    """Search performance benchmark."""

    name: str = "search"
    query_count: int = 100
    iterations: int = 1

    def run(self) -> BenchmarkResult:
        """Run search benchmark."""
        from ragd.config import load_config
        from ragd.embedding import get_embedder
        from ragd.storage.chromadb import ChromaStore

        config = load_config()

        try:
            store = ChromaStore(config.chroma_path)
            embedder = get_embedder(config.embedding.model)
        except Exception as e:
            logger.warning("Cannot run search benchmark: %s", e)
            return BenchmarkResult(
                name=self.name,
                iterations=0,
                times_ms=[],
                metadata={"error": str(e)},
            )

        # Check if store has data
        stats = store.get_stats()
        if stats.get("total_chunks", 0) == 0:
            return BenchmarkResult(
                name=self.name,
                iterations=0,
                times_ms=[],
                metadata={"error": "No indexed data"},
            )

        # Generate test queries
        queries = [
            f"test query {i} about documents"
            for i in range(self.query_count)
        ]

        times_ms: list[float] = []

        for _ in range(self.iterations):
            for query in queries:
                gc.collect()
                start = time.perf_counter()

                query_vec = embedder.embed([query])[0]
                _results = store.search(query_vec, limit=5)  # noqa: F841

                elapsed_ms = (time.perf_counter() - start) * 1000
                times_ms.append(elapsed_ms)

        qps = len(times_ms) / (sum(times_ms) / 1000) if times_ms else 0

        return BenchmarkResult(
            name=self.name,
            iterations=self.iterations,
            times_ms=times_ms,
            metadata={
                "query_count": self.query_count,
                "qps": qps,
            },
        )


@dataclass
class StartupBenchmark:
    """CLI startup time benchmark."""

    name: str = "startup"
    iterations: int = 10

    def run(self) -> BenchmarkResult:
        """Run startup benchmark."""
        times_version: list[float] = []
        times_help: list[float] = []

        for _ in range(self.iterations):
            # Measure --version startup
            start = time.perf_counter()
            subprocess.run(
                [sys.executable, "-m", "ragd", "--version"],
                capture_output=True,
                check=True,
            )
            elapsed_ms = (time.perf_counter() - start) * 1000
            times_version.append(elapsed_ms)

            # Measure --help startup
            start = time.perf_counter()
            subprocess.run(
                [sys.executable, "-m", "ragd", "--help"],
                capture_output=True,
                check=True,
            )
            elapsed_ms = (time.perf_counter() - start) * 1000
            times_help.append(elapsed_ms)

        all_times = times_version + times_help

        return BenchmarkResult(
            name=self.name,
            iterations=self.iterations,
            times_ms=all_times,
            metadata={
                "version_mean_ms": statistics.mean(times_version),
                "help_mean_ms": statistics.mean(times_help),
                "target_ms": 500,
                "meets_target": statistics.mean(all_times) < 500,
            },
        )


@dataclass
class BenchmarkSuite:
    """Complete benchmark suite."""

    name: str = "ragd"
    results: list[BenchmarkResult] = field(default_factory=list)
    environment: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(UTC).isoformat()
        if not self.environment:
            self.environment = self._get_environment()

    def _get_environment(self) -> dict[str, Any]:
        """Get environment information."""
        import ragd

        return {
            "ragd_version": ragd.__version__,
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "processor": platform.processor(),
            "machine": platform.machine(),
        }

    def add_result(self, result: BenchmarkResult) -> None:
        """Add a benchmark result."""
        self.results.append(result)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "timestamp": self.timestamp,
            "environment": self.environment,
            "results": [r.to_dict() for r in self.results],
        }

    def save(self, path: Path) -> None:
        """Save results to JSON file."""
        path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: Path) -> BenchmarkSuite:
        """Load results from JSON file."""
        data = json.loads(path.read_text())
        suite = cls(
            name=data.get("name", "ragd"),
            timestamp=data.get("timestamp", ""),
            environment=data.get("environment", {}),
        )
        for r in data.get("results", []):
            suite.results.append(
                BenchmarkResult(
                    name=r["name"],
                    iterations=r["iterations"],
                    times_ms=[],  # Raw times not stored
                    memory_mb=r.get("memory_mb"),
                    metadata=r.get("metadata", {}),
                )
            )
        return suite


class BenchmarkRunner:
    """Run benchmark suite."""

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self.suite = BenchmarkSuite()

    def run_all(self) -> BenchmarkSuite:
        """Run all benchmarks."""
        benchmarks = [
            StartupBenchmark(),
            IndexingBenchmark(),
            SearchBenchmark(),
        ]

        for bench in benchmarks:
            if self.verbose:
                print(f"Running {bench.name} benchmark...")
            result = bench.run()
            self.suite.add_result(result)
            if self.verbose:
                print(f"  Mean: {result.mean_ms:.1f}ms, P95: {result.p95_ms:.1f}ms")

        return self.suite

    def run_startup(self, iterations: int = 10) -> BenchmarkResult:
        """Run startup benchmark only."""
        bench = StartupBenchmark(iterations=iterations)
        result = bench.run()
        self.suite.add_result(result)
        return result

    def run_indexing(self, doc_count: int = 100, iterations: int = 3) -> BenchmarkResult:
        """Run indexing benchmark only."""
        bench = IndexingBenchmark(doc_count=doc_count, iterations=iterations)
        result = bench.run()
        self.suite.add_result(result)
        return result

    def run_search(self, query_count: int = 100) -> BenchmarkResult:
        """Run search benchmark only."""
        bench = SearchBenchmark(query_count=query_count)
        result = bench.run()
        self.suite.add_result(result)
        return result

    def generate_report(self) -> str:
        """Generate markdown report."""
        lines = [
            f"# ragd Performance Benchmarks",
            "",
            f"## Environment",
            f"- **ragd version**: {self.suite.environment.get('ragd_version', 'N/A')}",
            f"- **Python**: {self.suite.environment.get('python_version', 'N/A')}",
            f"- **Platform**: {self.suite.environment.get('platform', 'N/A')}",
            f"- **Processor**: {self.suite.environment.get('processor', 'N/A')}",
            "",
            f"## Results",
            "",
            "| Benchmark | Mean | P50 | P95 | P99 |",
            "|-----------|------|-----|-----|-----|",
        ]

        for result in self.suite.results:
            lines.append(
                f"| {result.name} | {result.mean_ms:.1f}ms | "
                f"{result.p50_ms:.1f}ms | {result.p95_ms:.1f}ms | {result.p99_ms:.1f}ms |"
            )

        lines.extend([
            "",
            "## Detailed Results",
            "",
        ])

        for result in self.suite.results:
            lines.append(f"### {result.name}")
            lines.append("")
            lines.append(f"- **Iterations**: {result.iterations}")
            lines.append(f"- **Mean**: {result.mean_ms:.1f}ms")
            lines.append(f"- **Min**: {result.min_ms:.1f}ms")
            lines.append(f"- **Max**: {result.max_ms:.1f}ms")
            if result.memory_mb:
                lines.append(f"- **Memory delta**: {result.memory_mb:.1f}MB")
            for key, value in result.metadata.items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")

        return "\n".join(lines)
