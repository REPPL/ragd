"""Memory tracking utilities for ragd (F-124).

Provides comprehensive memory monitoring and optimisation tools:
- Real-time memory usage tracking
- Peak memory detection
- Memory budget enforcement
- Streaming utilities for memory-efficient processing
"""

from __future__ import annotations

import gc
import logging
import os
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, TypeVar

import psutil

logger = logging.getLogger(__name__)

T = TypeVar("T")


def get_current_memory_mb() -> float:
    """Get current process memory usage in MB.

    Returns:
        Current RSS (Resident Set Size) memory in megabytes
    """
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def get_peak_memory_mb() -> float:
    """Get peak memory usage in MB.

    Note: Platform-specific behaviour:
    - macOS: ru_maxrss is in bytes
    - Linux: ru_maxrss is in kilobytes

    Returns:
        Peak memory usage in megabytes
    """
    import platform
    import resource

    rusage = resource.getrusage(resource.RUSAGE_SELF)
    if platform.system() == "Darwin":
        # macOS returns bytes
        return rusage.ru_maxrss / (1024 * 1024)
    else:
        # Linux returns kilobytes
        return rusage.ru_maxrss / 1024


def get_system_memory_info() -> dict[str, float]:
    """Get system memory information.

    Returns:
        Dictionary with total, available, used, percent
    """
    mem = psutil.virtual_memory()
    return {
        "total_gb": mem.total / (1024**3),
        "available_gb": mem.available / (1024**3),
        "used_gb": mem.used / (1024**3),
        "percent": mem.percent,
    }


@dataclass
class MemorySnapshot:
    """Snapshot of memory state at a point in time."""

    current_mb: float
    peak_mb: float
    timestamp: float = field(default_factory=lambda: __import__("time").time())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "current_mb": self.current_mb,
            "peak_mb": self.peak_mb,
            "timestamp": self.timestamp,
        }


@dataclass
class MemoryDelta:
    """Memory change during an operation."""

    start_mb: float
    end_mb: float
    delta_mb: float
    peak_mb: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start_mb": self.start_mb,
            "end_mb": self.end_mb,
            "delta_mb": self.delta_mb,
            "peak_mb": self.peak_mb,
        }


@contextmanager
def track_memory(
    gc_before: bool = True,
    gc_after: bool = True,
) -> Generator[dict[str, float], None, None]:
    """Context manager for tracking memory delta during an operation.

    Args:
        gc_before: Run garbage collection before tracking
        gc_after: Run garbage collection after tracking

    Yields:
        Dictionary that will contain start_mb, end_mb, delta_mb after exit

    Example:
        >>> with track_memory() as mem:
        ...     process_large_file()
        >>> print(f"Memory used: {mem['delta_mb']:.1f}MB")
    """
    if gc_before:
        gc.collect()

    start = get_current_memory_mb()
    result: dict[str, float] = {"start_mb": start}

    try:
        yield result
    finally:
        if gc_after:
            gc.collect()
        result["end_mb"] = get_current_memory_mb()
        result["delta_mb"] = result["end_mb"] - result["start_mb"]


class MemoryBudget:
    """Memory budget enforcement for operations.

    Tracks memory usage and warns/aborts when budget is exceeded.

    Example:
        >>> budget = MemoryBudget(max_mb=1024, warn_mb=768)
        >>> budget.check()  # Logs warning if usage exceeds warn_mb
        >>> with budget.enforce():
        ...     process_documents()  # Raises if budget exceeded
    """

    def __init__(
        self,
        max_mb: float = 2048,
        warn_mb: float | None = None,
        on_exceed: str = "warn",  # "warn", "abort", "ignore"
    ) -> None:
        """Initialise memory budget.

        Args:
            max_mb: Maximum allowed memory in MB
            warn_mb: Warning threshold in MB (defaults to 75% of max)
            on_exceed: Action when exceeded ("warn", "abort", "ignore")
        """
        self.max_mb = max_mb
        self.warn_mb = warn_mb or (max_mb * 0.75)
        self.on_exceed = on_exceed
        self._baseline: float | None = None

    def check(self) -> tuple[bool, float]:
        """Check current memory against budget.

        Returns:
            Tuple of (within_budget, current_mb)
        """
        current = get_current_memory_mb()

        if current > self.max_mb:
            if self.on_exceed == "abort":
                raise MemoryError(
                    f"Memory budget exceeded: {current:.0f}MB > {self.max_mb:.0f}MB"
                )
            elif self.on_exceed == "warn":
                logger.warning(
                    f"Memory budget exceeded: {current:.0f}MB > {self.max_mb:.0f}MB"
                )
            return False, current

        if current > self.warn_mb:
            logger.warning(
                f"Memory usage high: {current:.0f}MB (warning at {self.warn_mb:.0f}MB)"
            )

        return True, current

    def reset_baseline(self) -> None:
        """Reset baseline memory measurement."""
        gc.collect()
        self._baseline = get_current_memory_mb()

    def get_delta(self) -> float:
        """Get memory delta since baseline.

        Returns:
            Memory delta in MB (0 if no baseline set)
        """
        if self._baseline is None:
            return 0.0
        return get_current_memory_mb() - self._baseline

    @contextmanager
    def enforce(self) -> Generator[None, None, None]:
        """Context manager that enforces memory budget.

        Raises:
            MemoryError: If budget exceeded and on_exceed="abort"
        """
        self.reset_baseline()
        try:
            yield
        finally:
            self.check()


class MemoryMonitor:
    """Continuous memory monitoring for long operations.

    Samples memory usage periodically and tracks statistics.

    Example:
        >>> monitor = MemoryMonitor(sample_interval_ms=100)
        >>> with monitor:
        ...     process_many_documents()
        >>> print(f"Peak: {monitor.peak_mb:.0f}MB")
    """

    def __init__(
        self,
        sample_interval_ms: float = 100,
        max_samples: int = 1000,
    ) -> None:
        """Initialise memory monitor.

        Args:
            sample_interval_ms: Sampling interval in milliseconds
            max_samples: Maximum samples to keep
        """
        self.sample_interval_ms = sample_interval_ms
        self.max_samples = max_samples
        self.samples: list[float] = []
        self._thread: Any = None
        self._stop_event: Any = None

    @property
    def peak_mb(self) -> float:
        """Peak memory observed."""
        return max(self.samples) if self.samples else 0.0

    @property
    def mean_mb(self) -> float:
        """Mean memory observed."""
        if not self.samples:
            return 0.0
        return sum(self.samples) / len(self.samples)

    @property
    def min_mb(self) -> float:
        """Minimum memory observed."""
        return min(self.samples) if self.samples else 0.0

    def sample(self) -> float:
        """Take a memory sample.

        Returns:
            Current memory in MB
        """
        current = get_current_memory_mb()
        if len(self.samples) < self.max_samples:
            self.samples.append(current)
        else:
            # Rolling window
            self.samples.pop(0)
            self.samples.append(current)
        return current

    def start_background_sampling(self) -> None:
        """Start background sampling thread."""
        import threading
        import time

        self._stop_event = threading.Event()

        def sample_loop() -> None:
            while not self._stop_event.is_set():
                self.sample()
                time.sleep(self.sample_interval_ms / 1000)

        self._thread = threading.Thread(target=sample_loop, daemon=True)
        self._thread.start()

    def stop_background_sampling(self) -> None:
        """Stop background sampling thread."""
        if self._stop_event:
            self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)

    def __enter__(self) -> MemoryMonitor:
        """Start monitoring."""
        self.samples = []
        self.sample()  # Initial sample
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop monitoring."""
        self.sample()  # Final sample

    def get_summary(self) -> dict[str, float]:
        """Get monitoring summary.

        Returns:
            Dictionary with peak, mean, min, sample_count
        """
        return {
            "peak_mb": self.peak_mb,
            "mean_mb": self.mean_mb,
            "min_mb": self.min_mb,
            "sample_count": len(self.samples),
        }


def force_gc() -> float:
    """Force garbage collection and return freed memory.

    Returns:
        Memory freed in MB (negative if more memory used)
    """
    before = get_current_memory_mb()
    gc.collect()
    after = get_current_memory_mb()
    return before - after


def gc_after_operation(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator that runs gc.collect() after function execution.

    Args:
        func: Function to wrap

    Returns:
        Wrapped function
    """
    import functools

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return func(*args, **kwargs)
        finally:
            gc.collect()

    return wrapper


def estimate_memory_for_embeddings(
    text_count: int,
    avg_text_length: int = 500,
    embedding_dim: int = 384,
) -> float:
    """Estimate memory required for embedding operation.

    Args:
        text_count: Number of texts to embed
        avg_text_length: Average text length in characters
        embedding_dim: Embedding dimension

    Returns:
        Estimated memory in MB
    """
    # Rough estimates:
    # - Text storage: ~1 byte per character
    # - Embedding: 4 bytes per float * dimension
    # - Overhead: ~2x for intermediate processing

    text_memory = text_count * avg_text_length / (1024 * 1024)
    embedding_memory = text_count * embedding_dim * 4 / (1024 * 1024)
    overhead_factor = 2.0

    return (text_memory + embedding_memory) * overhead_factor


def suggest_batch_size(
    total_items: int,
    available_memory_mb: float | None = None,
    item_memory_mb: float = 0.5,
    target_utilisation: float = 0.5,
) -> int:
    """Suggest batch size based on available memory.

    Args:
        total_items: Total items to process
        available_memory_mb: Available memory (auto-detected if None)
        item_memory_mb: Estimated memory per item
        target_utilisation: Target memory utilisation (0-1)

    Returns:
        Suggested batch size
    """
    if available_memory_mb is None:
        mem_info = get_system_memory_info()
        available_memory_mb = mem_info["available_gb"] * 1024 * target_utilisation

    max_items = int(available_memory_mb / item_memory_mb)
    batch_size = max(1, min(max_items, total_items))

    # Round to nice number
    if batch_size > 100:
        batch_size = (batch_size // 10) * 10
    elif batch_size > 10:
        batch_size = (batch_size // 5) * 5

    return batch_size
