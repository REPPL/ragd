"""Tests for F-127: Performance Benchmarks.

Tests the benchmark module components.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from ragd.benchmark.runner import (
    BenchmarkResult,
    BenchmarkRunner,
    BenchmarkSuite,
    IndexingBenchmark,
    SearchBenchmark,
    StartupBenchmark,
)


class TestBenchmarkResult:
    """Test BenchmarkResult dataclass."""

    def test_result_creation(self) -> None:
        """BenchmarkResult should be created correctly."""
        result = BenchmarkResult(
            name="test",
            iterations=3,
            times_ms=[100.0, 110.0, 105.0],
        )

        assert result.name == "test"
        assert result.iterations == 3
        assert len(result.times_ms) == 3

    def test_result_mean(self) -> None:
        """BenchmarkResult.mean_ms should calculate correctly."""
        result = BenchmarkResult(
            name="test",
            iterations=3,
            times_ms=[100.0, 110.0, 105.0],
        )

        assert result.mean_ms == pytest.approx(105.0, rel=0.01)

    def test_result_median(self) -> None:
        """BenchmarkResult.median_ms should calculate correctly."""
        result = BenchmarkResult(
            name="test",
            iterations=3,
            times_ms=[100.0, 110.0, 105.0],
        )

        assert result.median_ms == 105.0

    def test_result_min_max(self) -> None:
        """BenchmarkResult should calculate min/max."""
        result = BenchmarkResult(
            name="test",
            iterations=3,
            times_ms=[100.0, 110.0, 105.0],
        )

        assert result.min_ms == 100.0
        assert result.max_ms == 110.0

    def test_result_percentiles(self) -> None:
        """BenchmarkResult should calculate percentiles."""
        # Create results with known distribution
        times = list(range(1, 101))  # 1-100
        result = BenchmarkResult(
            name="test",
            iterations=1,
            times_ms=[float(t) for t in times],
        )

        assert result.p50_ms == pytest.approx(50.5, rel=0.1)
        assert result.p95_ms == pytest.approx(95.0, rel=0.1)
        assert result.p99_ms == pytest.approx(99.0, rel=0.1)

    def test_result_empty_times(self) -> None:
        """BenchmarkResult should handle empty times."""
        result = BenchmarkResult(
            name="test",
            iterations=0,
            times_ms=[],
        )

        assert result.mean_ms == 0.0
        assert result.median_ms == 0.0
        assert result.p50_ms == 0.0

    def test_result_to_dict(self) -> None:
        """BenchmarkResult should convert to dict."""
        result = BenchmarkResult(
            name="test",
            iterations=3,
            times_ms=[100.0, 110.0, 105.0],
            memory_mb=50.5,
            metadata={"key": "value"},
        )

        data = result.to_dict()
        assert data["name"] == "test"
        assert data["iterations"] == 3
        assert data["mean_ms"] == pytest.approx(105.0, rel=0.01)
        assert data["memory_mb"] == 50.5
        assert data["metadata"]["key"] == "value"


class TestBenchmarkSuite:
    """Test BenchmarkSuite dataclass."""

    def test_suite_creation(self) -> None:
        """BenchmarkSuite should be created correctly."""
        suite = BenchmarkSuite()

        assert suite.name == "ragd"
        assert len(suite.results) == 0
        assert suite.timestamp != ""
        assert "ragd_version" in suite.environment

    def test_suite_add_result(self) -> None:
        """BenchmarkSuite should add results."""
        suite = BenchmarkSuite()
        result = BenchmarkResult(
            name="test",
            iterations=1,
            times_ms=[100.0],
        )

        suite.add_result(result)
        assert len(suite.results) == 1

    def test_suite_to_dict(self) -> None:
        """BenchmarkSuite should convert to dict."""
        suite = BenchmarkSuite()
        suite.add_result(
            BenchmarkResult(name="test", iterations=1, times_ms=[100.0])
        )

        data = suite.to_dict()
        assert data["name"] == "ragd"
        assert len(data["results"]) == 1
        assert "environment" in data

    def test_suite_save_load(self) -> None:
        """BenchmarkSuite should save and load."""
        suite = BenchmarkSuite()
        suite.add_result(
            BenchmarkResult(
                name="test",
                iterations=3,
                times_ms=[100.0, 110.0, 105.0],
            )
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "results.json"
            suite.save(path)

            assert path.exists()

            loaded = BenchmarkSuite.load(path)
            assert loaded.name == suite.name
            assert len(loaded.results) == 1
            assert loaded.results[0].name == "test"


class TestStartupBenchmark:
    """Test StartupBenchmark."""

    def test_startup_benchmark_creation(self) -> None:
        """StartupBenchmark should be created correctly."""
        bench = StartupBenchmark(iterations=5)

        assert bench.name == "startup"
        assert bench.iterations == 5

    def test_startup_benchmark_run(self) -> None:
        """StartupBenchmark should run and return results."""
        bench = StartupBenchmark(iterations=2)
        result = bench.run()

        assert result.name == "startup"
        assert result.iterations == 2
        assert len(result.times_ms) == 4  # 2 iterations x 2 commands
        assert "version_mean_ms" in result.metadata
        assert "help_mean_ms" in result.metadata
        assert "meets_target" in result.metadata


class TestIndexingBenchmark:
    """Test IndexingBenchmark."""

    def test_indexing_benchmark_creation(self) -> None:
        """IndexingBenchmark should be created correctly."""
        bench = IndexingBenchmark(doc_count=50, iterations=2)

        assert bench.name == "indexing"
        assert bench.doc_count == 50
        assert bench.iterations == 2

    def test_indexing_benchmark_run(self) -> None:
        """IndexingBenchmark should run and return results."""
        bench = IndexingBenchmark(doc_count=10, iterations=1)
        result = bench.run()

        assert result.name == "indexing"
        assert len(result.times_ms) == 1
        assert "doc_count" in result.metadata
        assert "docs_per_sec" in result.metadata


class TestSearchBenchmark:
    """Test SearchBenchmark."""

    def test_search_benchmark_creation(self) -> None:
        """SearchBenchmark should be created correctly."""
        bench = SearchBenchmark(query_count=50)

        assert bench.name == "search"
        assert bench.query_count == 50

    def test_search_benchmark_run_empty_store(self) -> None:
        """SearchBenchmark should handle empty store gracefully."""
        bench = SearchBenchmark(query_count=5, iterations=1)
        result = bench.run()

        # Should return result even if store is empty
        assert result.name == "search"


class TestBenchmarkRunner:
    """Test BenchmarkRunner."""

    def test_runner_creation(self) -> None:
        """BenchmarkRunner should be created correctly."""
        runner = BenchmarkRunner(verbose=True)

        assert runner.verbose is True
        assert runner.suite is not None

    def test_runner_run_startup(self) -> None:
        """BenchmarkRunner should run startup benchmark."""
        runner = BenchmarkRunner()
        result = runner.run_startup(iterations=2)

        assert result.name == "startup"
        assert len(runner.suite.results) == 1

    def test_runner_run_indexing(self) -> None:
        """BenchmarkRunner should run indexing benchmark."""
        runner = BenchmarkRunner()
        result = runner.run_indexing(doc_count=5, iterations=1)

        assert result.name == "indexing"
        assert len(runner.suite.results) == 1

    def test_runner_generate_report(self) -> None:
        """BenchmarkRunner should generate markdown report."""
        runner = BenchmarkRunner()
        runner.suite.add_result(
            BenchmarkResult(
                name="test",
                iterations=1,
                times_ms=[100.0, 110.0],
            )
        )

        report = runner.generate_report()
        assert "# ragd Performance Benchmarks" in report
        assert "## Environment" in report
        assert "## Results" in report
        assert "test" in report
