"""Tests for F-123: Performance Profiling.

Tests the performance profiling framework components.
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from ragd.performance import (
    ProfileSession,
    OperationProfiler,
    ProfileMetric,
    profile,
    format_profile_report,
    print_profile_report,
)
from ragd.performance.profiler import (
    TimingResult,
    get_memory_mb,
    track_memory,
    compare_profiles,
)
from ragd.performance.metrics import (
    IndexingProfile,
    SearchProfile,
    ChatProfile,
    calculate_percentiles,
)


class TestGetMemory:
    """Test memory tracking utilities."""

    def test_get_memory_mb_returns_positive(self) -> None:
        """get_memory_mb should return positive value."""
        memory = get_memory_mb()
        assert memory > 0

    def test_get_memory_mb_reasonable_range(self) -> None:
        """Memory usage should be in reasonable range."""
        memory = get_memory_mb()
        # Should be between 1MB and 16GB
        assert 1 < memory < 16384


class TestTrackMemory:
    """Test track_memory context manager."""

    def test_track_memory_records_delta(self) -> None:
        """track_memory should record memory delta."""
        with track_memory() as mem:
            # Allocate some memory
            data = [0] * 100000

        assert "start_mb" in mem
        assert "end_mb" in mem
        assert "delta_mb" in mem
        assert isinstance(mem["delta_mb"], float)

    def test_track_memory_gc_before(self) -> None:
        """track_memory should run gc when gc_before=True."""
        with track_memory(gc_before=True) as mem:
            pass

        assert "start_mb" in mem


class TestTimingResult:
    """Test TimingResult dataclass."""

    def test_timing_result_creation(self) -> None:
        """TimingResult should be created correctly."""
        now = datetime.now()
        result = TimingResult(
            operation="test",
            duration_ms=100.0,
            start_time=now,
            end_time=now,
        )
        assert result.operation == "test"
        assert result.duration_ms == 100.0
        assert result.duration_seconds == 0.1

    def test_timing_result_with_memory(self) -> None:
        """TimingResult should include memory tracking."""
        now = datetime.now()
        result = TimingResult(
            operation="test",
            duration_ms=100.0,
            start_time=now,
            end_time=now,
            memory_start_mb=100.0,
            memory_end_mb=150.0,
            memory_delta_mb=50.0,
        )
        assert result.memory_delta_mb == 50.0

    def test_timing_result_to_dict(self) -> None:
        """TimingResult should convert to dict."""
        now = datetime.now()
        result = TimingResult(
            operation="test",
            duration_ms=100.0,
            start_time=now,
            end_time=now,
        )
        data = result.to_dict()
        assert data["operation"] == "test"
        assert data["duration_ms"] == 100.0


class TestOperationProfiler:
    """Test OperationProfiler context manager."""

    def test_operation_profiler_times_operation(self) -> None:
        """OperationProfiler should time operations."""
        with OperationProfiler("test") as op:
            # Do something
            sum(range(1000))

        assert op.duration_ms > 0
        assert op.result is not None
        assert op.result.operation == "test"

    def test_operation_profiler_tracks_memory(self) -> None:
        """OperationProfiler should track memory when enabled."""
        with OperationProfiler("test", track_memory=True) as op:
            data = [0] * 10000

        assert op.memory_delta_mb is not None

    def test_operation_profiler_with_session(self) -> None:
        """OperationProfiler should record to session."""
        session = ProfileSession("test_session")

        with OperationProfiler("op1", session):
            pass
        with OperationProfiler("op2", session):
            pass

        assert len(session.results) == 2
        assert session.results[0].operation == "op1"
        assert session.results[1].operation == "op2"

    def test_operation_profiler_metadata(self) -> None:
        """OperationProfiler should include metadata."""
        with OperationProfiler("test", metadata={"key": "value"}) as op:
            pass

        assert op.result.metadata["key"] == "value"


class TestProfileSession:
    """Test ProfileSession class."""

    def test_profile_session_creation(self) -> None:
        """ProfileSession should be created correctly."""
        session = ProfileSession("test_session", description="Test")
        assert session.name == "test_session"
        assert session.description == "Test"
        assert session.track_memory is True

    def test_profile_session_context_manager(self) -> None:
        """ProfileSession should work as context manager."""
        with ProfileSession("test") as session:
            assert session.end_time is None

        assert session.end_time is not None

    def test_profile_session_add_result(self) -> None:
        """ProfileSession should accept results."""
        session = ProfileSession("test")
        result = TimingResult(
            operation="op1",
            duration_ms=100.0,
            start_time=datetime.now(),
            end_time=datetime.now(),
        )
        session.add_result(result)
        assert len(session.results) == 1

    def test_profile_session_get_summary(self) -> None:
        """ProfileSession should compute summary statistics."""
        session = ProfileSession("test")

        for i in range(5):
            result = TimingResult(
                operation="op1",
                duration_ms=100.0 + i,
                start_time=datetime.now(),
                end_time=datetime.now(),
            )
            session.add_result(result)

        summary = session.get_summary()
        assert "op1" in summary
        assert summary["op1"]["count"] == 5
        assert summary["op1"]["mean_ms"] == 102.0  # (100+101+102+103+104)/5

    def test_profile_session_export_import_json(self) -> None:
        """ProfileSession should export and import JSON."""
        with ProfileSession("test") as session:
            with OperationProfiler("op1", session):
                pass

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = Path(f.name)

        try:
            session.export_json(path)
            assert path.exists()

            imported = ProfileSession.import_json(path)
            assert imported.name == "test"
            assert len(imported.results) == 1
        finally:
            path.unlink()

    def test_profile_session_captures_environment(self) -> None:
        """ProfileSession should capture environment info."""
        session = ProfileSession("test")
        env = session.metadata.get("environment", {})

        assert "python_version" in env
        assert "platform" in env
        assert "cpu_count" in env
        assert "memory_total_gb" in env


class TestProfileDecorator:
    """Test @profile decorator."""

    def test_profile_decorator_times_function(self) -> None:
        """@profile should time function execution."""
        call_count = [0]

        @profile(operation="test_func")
        def test_function() -> int:
            call_count[0] += 1
            return sum(range(1000))

        result = test_function()
        assert result == sum(range(1000))
        assert call_count[0] == 1

    def test_profile_decorator_uses_function_name(self) -> None:
        """@profile should use function name if operation not specified."""
        @profile()
        def my_function() -> None:
            pass

        my_function()
        # No exception means success


class TestProfileMetric:
    """Test ProfileMetric class."""

    def test_profile_metric_creation(self) -> None:
        """ProfileMetric should be created correctly."""
        metric = ProfileMetric(name="test", operation="index")
        assert metric.name == "test"
        assert metric.count == 0

    def test_profile_metric_record(self) -> None:
        """ProfileMetric should record measurements."""
        metric = ProfileMetric(name="test", operation="index")
        metric.record(100.0, memory_delta_mb=10.0)
        metric.record(150.0, memory_delta_mb=15.0)

        assert metric.count == 2
        assert metric.total_ms == 250.0
        assert metric.mean_ms == 125.0

    def test_profile_metric_percentiles(self) -> None:
        """ProfileMetric should calculate percentiles."""
        metric = ProfileMetric(name="test", operation="search")
        for i in range(100):
            metric.record(float(i))

        assert metric.p50_ms == 49.5  # median of 0-99
        assert metric.p95_ms >= 94
        assert metric.p99_ms >= 98

    def test_profile_metric_to_dict(self) -> None:
        """ProfileMetric should convert to dict."""
        metric = ProfileMetric(name="test", operation="index")
        metric.record(100.0)

        data = metric.to_dict()
        assert data["name"] == "test"
        assert data["count"] == 1


class TestCalculatePercentiles:
    """Test calculate_percentiles function."""

    def test_percentiles_empty_list(self) -> None:
        """Percentiles of empty list should be zeros."""
        result = calculate_percentiles([])
        assert result["p50"] == 0.0
        assert result["p95"] == 0.0

    def test_percentiles_single_value(self) -> None:
        """Percentiles of single value should be that value."""
        result = calculate_percentiles([100.0])
        assert result["p50"] == 100.0
        assert result["mean"] == 100.0

    def test_percentiles_distribution(self) -> None:
        """Percentiles should be calculated correctly."""
        values = list(range(100))
        result = calculate_percentiles(values)

        assert result["p50"] == 50
        assert result["min"] == 0
        assert result["max"] == 99


class TestCompareProfiles:
    """Test profile comparison functionality."""

    def test_compare_profiles_regression(self) -> None:
        """compare_profiles should detect regressions."""
        # Baseline - fast
        baseline = ProfileSession("baseline")
        baseline.add_result(TimingResult(
            operation="search",
            duration_ms=100.0,
            start_time=datetime.now(),
            end_time=datetime.now(),
        ))

        # Current - slower (regression)
        current = ProfileSession("current")
        current.add_result(TimingResult(
            operation="search",
            duration_ms=200.0,
            start_time=datetime.now(),
            end_time=datetime.now(),
        ))

        comparison = compare_profiles(baseline, current)

        assert "search" in comparison["operations"]
        assert comparison["operations"]["search"]["status"] == "regression"
        assert comparison["operations"]["search"]["change_pct"] > 0

    def test_compare_profiles_improvement(self) -> None:
        """compare_profiles should detect improvements."""
        # Baseline - slow
        baseline = ProfileSession("baseline")
        baseline.add_result(TimingResult(
            operation="search",
            duration_ms=200.0,
            start_time=datetime.now(),
            end_time=datetime.now(),
        ))

        # Current - faster (improvement)
        current = ProfileSession("current")
        current.add_result(TimingResult(
            operation="search",
            duration_ms=100.0,
            start_time=datetime.now(),
            end_time=datetime.now(),
        ))

        comparison = compare_profiles(baseline, current)

        assert comparison["operations"]["search"]["status"] == "improvement"
        assert comparison["operations"]["search"]["change_pct"] < 0


class TestIndexingProfile:
    """Test IndexingProfile dataclass."""

    def test_indexing_profile_throughput(self) -> None:
        """IndexingProfile should calculate throughput."""
        profile = IndexingProfile()
        profile.document_count = 100
        profile.chunk_count = 1000
        profile.total.record(10000.0)  # 10 seconds

        assert profile.docs_per_second == 10.0
        assert profile.chunks_per_second == 100.0


class TestSearchProfile:
    """Test SearchProfile dataclass."""

    def test_search_profile_qps(self) -> None:
        """SearchProfile should calculate QPS."""
        profile = SearchProfile()
        profile.query_count = 100

        for _ in range(100):
            profile.latency.record(10.0)  # 10ms per query

        assert profile.qps == 100.0  # 1000ms / 10ms = 100 QPS


class TestChatProfile:
    """Test ChatProfile dataclass."""

    def test_chat_profile_tokens_per_second(self) -> None:
        """ChatProfile should calculate tokens per second."""
        profile = ChatProfile()
        profile.total_tokens_in = 1000
        profile.total_tokens_out = 500
        profile.llm_response.record(1000.0)  # 1 second

        assert profile.tokens_per_second_in == 1000.0
        assert profile.tokens_per_second_out == 500.0
