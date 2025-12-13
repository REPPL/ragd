"""Tests for F-124: Memory Optimisation.

Tests the memory tracking and optimisation utilities.
"""

from __future__ import annotations

import pytest

from ragd.performance.memory import (
    get_current_memory_mb,
    get_peak_memory_mb,
    get_system_memory_info,
    track_memory,
    MemoryBudget,
    MemoryMonitor,
    MemorySnapshot,
    MemoryDelta,
    force_gc,
    gc_after_operation,
    estimate_memory_for_embeddings,
    suggest_batch_size,
)


class TestGetMemory:
    """Test basic memory tracking functions."""

    def test_get_current_memory_mb_positive(self) -> None:
        """Current memory should be positive."""
        memory = get_current_memory_mb()
        assert memory > 0
        assert isinstance(memory, float)

    def test_get_current_memory_mb_reasonable(self) -> None:
        """Memory should be in reasonable range for test process."""
        memory = get_current_memory_mb()
        # Between 1MB and 16GB
        assert 1 < memory < 16384

    def test_get_peak_memory_mb_positive(self) -> None:
        """Peak memory should be positive."""
        peak = get_peak_memory_mb()
        assert peak > 0
        assert isinstance(peak, float)

    def test_get_peak_memory_at_least_current(self) -> None:
        """Peak memory should be >= current memory."""
        current = get_current_memory_mb()
        peak = get_peak_memory_mb()
        # Peak should be at least current (with some tolerance for timing)
        assert peak >= current * 0.9


class TestSystemMemoryInfo:
    """Test system memory information."""

    def test_get_system_memory_info_structure(self) -> None:
        """System memory info should have expected keys."""
        info = get_system_memory_info()

        assert "total_gb" in info
        assert "available_gb" in info
        assert "used_gb" in info
        assert "percent" in info

    def test_get_system_memory_info_values(self) -> None:
        """System memory values should be sensible."""
        info = get_system_memory_info()

        assert info["total_gb"] > 0
        assert info["available_gb"] > 0
        assert info["used_gb"] > 0
        assert 0 < info["percent"] <= 100


class TestTrackMemory:
    """Test track_memory context manager."""

    def test_track_memory_basic(self) -> None:
        """track_memory should record start/end/delta."""
        with track_memory() as mem:
            data = [0] * 10000

        assert "start_mb" in mem
        assert "end_mb" in mem
        assert "delta_mb" in mem

    def test_track_memory_delta_type(self) -> None:
        """Memory delta should be a float."""
        with track_memory() as mem:
            pass

        assert isinstance(mem["delta_mb"], float)

    def test_track_memory_with_gc(self) -> None:
        """track_memory should work with gc options."""
        with track_memory(gc_before=True, gc_after=True) as mem:
            pass

        assert "start_mb" in mem


class TestMemorySnapshot:
    """Test MemorySnapshot dataclass."""

    def test_memory_snapshot_creation(self) -> None:
        """MemorySnapshot should be created correctly."""
        snapshot = MemorySnapshot(current_mb=100.0, peak_mb=150.0)
        assert snapshot.current_mb == 100.0
        assert snapshot.peak_mb == 150.0

    def test_memory_snapshot_to_dict(self) -> None:
        """MemorySnapshot should convert to dict."""
        snapshot = MemorySnapshot(current_mb=100.0, peak_mb=150.0)
        data = snapshot.to_dict()

        assert data["current_mb"] == 100.0
        assert data["peak_mb"] == 150.0
        assert "timestamp" in data


class TestMemoryDelta:
    """Test MemoryDelta dataclass."""

    def test_memory_delta_creation(self) -> None:
        """MemoryDelta should be created correctly."""
        delta = MemoryDelta(start_mb=100.0, end_mb=150.0, delta_mb=50.0)
        assert delta.delta_mb == 50.0

    def test_memory_delta_to_dict(self) -> None:
        """MemoryDelta should convert to dict."""
        delta = MemoryDelta(start_mb=100.0, end_mb=150.0, delta_mb=50.0, peak_mb=175.0)
        data = delta.to_dict()

        assert data["delta_mb"] == 50.0
        assert data["peak_mb"] == 175.0


class TestMemoryBudget:
    """Test MemoryBudget class."""

    def test_memory_budget_creation(self) -> None:
        """MemoryBudget should be created with defaults."""
        budget = MemoryBudget()
        assert budget.max_mb == 2048
        assert budget.warn_mb == 1536  # 75% of 2048

    def test_memory_budget_custom(self) -> None:
        """MemoryBudget should accept custom values."""
        budget = MemoryBudget(max_mb=1024, warn_mb=512)
        assert budget.max_mb == 1024
        assert budget.warn_mb == 512

    def test_memory_budget_check(self) -> None:
        """MemoryBudget.check() should return status."""
        budget = MemoryBudget(max_mb=999999)  # Large budget
        within_budget, current = budget.check()

        assert within_budget is True
        assert current > 0

    def test_memory_budget_exceed_warn(self) -> None:
        """MemoryBudget should handle exceed with warn action."""
        budget = MemoryBudget(max_mb=1, on_exceed="warn")
        within_budget, _ = budget.check()
        assert within_budget is False

    def test_memory_budget_exceed_ignore(self) -> None:
        """MemoryBudget should handle exceed with ignore action."""
        budget = MemoryBudget(max_mb=1, on_exceed="ignore")
        within_budget, _ = budget.check()
        assert within_budget is False

    def test_memory_budget_reset_baseline(self) -> None:
        """MemoryBudget should reset baseline."""
        budget = MemoryBudget()
        budget.reset_baseline()
        assert budget._baseline is not None

    def test_memory_budget_get_delta(self) -> None:
        """MemoryBudget should calculate delta from baseline."""
        budget = MemoryBudget()
        delta_before = budget.get_delta()
        assert delta_before == 0.0  # No baseline

        budget.reset_baseline()
        delta_after = budget.get_delta()
        assert isinstance(delta_after, float)

    def test_memory_budget_context_manager(self) -> None:
        """MemoryBudget.enforce() should work as context manager."""
        budget = MemoryBudget(max_mb=999999)

        with budget.enforce():
            pass  # Should not raise


class TestMemoryMonitor:
    """Test MemoryMonitor class."""

    def test_memory_monitor_creation(self) -> None:
        """MemoryMonitor should be created correctly."""
        monitor = MemoryMonitor(sample_interval_ms=100)
        assert monitor.sample_interval_ms == 100
        assert len(monitor.samples) == 0

    def test_memory_monitor_sample(self) -> None:
        """MemoryMonitor.sample() should record samples."""
        monitor = MemoryMonitor()
        sample = monitor.sample()

        assert sample > 0
        assert len(monitor.samples) == 1
        assert monitor.samples[0] == sample

    def test_memory_monitor_context_manager(self) -> None:
        """MemoryMonitor should work as context manager."""
        with MemoryMonitor() as monitor:
            pass  # Do some work

        assert len(monitor.samples) >= 2  # Initial and final samples

    def test_memory_monitor_statistics(self) -> None:
        """MemoryMonitor should calculate statistics."""
        monitor = MemoryMonitor()
        for _ in range(5):
            monitor.sample()

        assert monitor.peak_mb > 0
        assert monitor.mean_mb > 0
        assert monitor.min_mb > 0

    def test_memory_monitor_summary(self) -> None:
        """MemoryMonitor.get_summary() should return dict."""
        with MemoryMonitor() as monitor:
            pass

        summary = monitor.get_summary()
        assert "peak_mb" in summary
        assert "mean_mb" in summary
        assert "min_mb" in summary
        assert "sample_count" in summary

    def test_memory_monitor_max_samples(self) -> None:
        """MemoryMonitor should respect max_samples."""
        monitor = MemoryMonitor(max_samples=3)

        for _ in range(10):
            monitor.sample()

        assert len(monitor.samples) == 3


class TestForceGc:
    """Test force_gc function."""

    def test_force_gc_returns_float(self) -> None:
        """force_gc should return memory freed."""
        freed = force_gc()
        assert isinstance(freed, float)


class TestGcAfterOperation:
    """Test gc_after_operation decorator."""

    def test_gc_after_operation_runs_function(self) -> None:
        """gc_after_operation should run the function."""
        call_count = [0]

        @gc_after_operation
        def test_func() -> int:
            call_count[0] += 1
            return 42

        result = test_func()
        assert result == 42
        assert call_count[0] == 1


class TestEstimateMemory:
    """Test memory estimation functions."""

    def test_estimate_memory_for_embeddings(self) -> None:
        """estimate_memory_for_embeddings should return positive value."""
        estimate = estimate_memory_for_embeddings(
            text_count=1000,
            avg_text_length=500,
            embedding_dim=384,
        )

        assert estimate > 0
        assert isinstance(estimate, float)

    def test_estimate_memory_scales_with_count(self) -> None:
        """Estimate should scale with text count."""
        est_100 = estimate_memory_for_embeddings(100)
        est_1000 = estimate_memory_for_embeddings(1000)

        assert est_1000 > est_100


class TestSuggestBatchSize:
    """Test suggest_batch_size function."""

    def test_suggest_batch_size_positive(self) -> None:
        """Suggested batch size should be positive."""
        batch_size = suggest_batch_size(total_items=1000)
        assert batch_size > 0

    def test_suggest_batch_size_respects_total(self) -> None:
        """Batch size should not exceed total items."""
        batch_size = suggest_batch_size(total_items=5)
        assert batch_size <= 5

    def test_suggest_batch_size_custom_memory(self) -> None:
        """Batch size should respect available memory."""
        batch_size_low = suggest_batch_size(
            total_items=1000,
            available_memory_mb=10,
            item_memory_mb=1.0,
        )
        batch_size_high = suggest_batch_size(
            total_items=1000,
            available_memory_mb=1000,
            item_memory_mb=1.0,
        )

        assert batch_size_high > batch_size_low


class TestMemoryConfigIntegration:
    """Test MemoryConfig integration with RagdConfig."""

    def test_memory_config_in_ragd_config(self) -> None:
        """RagdConfig should include MemoryConfig."""
        from ragd.config import RagdConfig

        config = RagdConfig()
        assert hasattr(config, "memory")
        assert config.memory.max_peak_mb == 2048
        assert config.memory.embedding_batch_size == 32

    def test_memory_config_defaults(self) -> None:
        """MemoryConfig should have sensible defaults."""
        from ragd.config import MemoryConfig

        config = MemoryConfig()
        assert config.max_peak_mb == 2048
        assert config.streaming_threshold_mb == 100
        assert config.embedding_batch_size == 32
        assert config.gc_frequency == "per_document"
