"""Core profiling components for ragd (F-123).

Provides ProfileSession for grouping related measurements and
OperationProfiler as a context manager for timing operations.
"""

from __future__ import annotations

import functools
import gc
import json
import logging
import os
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

import psutil

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

T = TypeVar("T")


def get_memory_mb() -> float:
    """Get current process memory usage in MB.

    Returns:
        Current RSS memory in megabytes
    """
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def get_peak_memory_mb() -> float:
    """Get peak memory usage in MB (platform-specific).

    Returns:
        Peak memory usage in megabytes.
        On macOS: ru_maxrss is in bytes
        On Linux: ru_maxrss is in kilobytes
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


@dataclass
class TimingResult:
    """Result of a timed operation."""

    operation: str
    duration_ms: float
    start_time: datetime
    end_time: datetime
    memory_start_mb: float | None = None
    memory_end_mb: float | None = None
    memory_delta_mb: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        """Duration in seconds."""
        return self.duration_ms / 1000

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation": self.operation,
            "duration_ms": self.duration_ms,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "memory_start_mb": self.memory_start_mb,
            "memory_end_mb": self.memory_end_mb,
            "memory_delta_mb": self.memory_delta_mb,
            "metadata": self.metadata,
        }


class ProfileSession:
    """Container for grouping related profiling measurements.

    ProfileSession collects timing results from multiple operations
    and provides export/import capabilities for comparison.

    Example:
        >>> session = ProfileSession("indexing_benchmark")
        >>> with OperationProfiler("parse", session):
        ...     parse_documents()
        >>> with OperationProfiler("embed", session):
        ...     embed_chunks()
        >>> session.export_json("profile.json")
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        track_memory: bool = True,
    ) -> None:
        """Initialise a profile session.

        Args:
            name: Session name for identification
            description: Optional description
            track_memory: Whether to track memory usage
        """
        self.name = name
        self.description = description
        self.track_memory = track_memory
        self.results: list[TimingResult] = []
        self.start_time = datetime.now()
        self.end_time: datetime | None = None
        self.metadata: dict[str, Any] = {}

        # Capture environment info
        self._capture_environment()

    def _capture_environment(self) -> None:
        """Capture environment information."""
        import platform
        import sys

        self.metadata["environment"] = {
            "python_version": sys.version,
            "platform": platform.platform(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
        }

    def add_result(self, result: TimingResult) -> None:
        """Add a timing result to the session.

        Args:
            result: TimingResult to add
        """
        self.results.append(result)

    def get_results_by_operation(self, operation: str) -> list[TimingResult]:
        """Get all results for a specific operation.

        Args:
            operation: Operation name

        Returns:
            List of matching TimingResults
        """
        return [r for r in self.results if r.operation == operation]

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics for all operations.

        Returns:
            Dictionary with summary statistics per operation
        """
        import statistics

        operations: dict[str, list[float]] = {}
        memory_deltas: dict[str, list[float]] = {}

        for result in self.results:
            if result.operation not in operations:
                operations[result.operation] = []
                memory_deltas[result.operation] = []

            operations[result.operation].append(result.duration_ms)
            if result.memory_delta_mb is not None:
                memory_deltas[result.operation].append(result.memory_delta_mb)

        summary: dict[str, Any] = {}
        for op, times in operations.items():
            op_summary = {
                "count": len(times),
                "total_ms": sum(times),
                "mean_ms": statistics.mean(times),
                "min_ms": min(times),
                "max_ms": max(times),
            }
            if len(times) > 1:
                op_summary["median_ms"] = statistics.median(times)
                op_summary["stdev_ms"] = statistics.stdev(times)
            else:
                op_summary["median_ms"] = times[0]
                op_summary["stdev_ms"] = 0.0

            # Memory stats if available
            mem_list = memory_deltas.get(op, [])
            if mem_list:
                op_summary["memory_delta_mean_mb"] = statistics.mean(mem_list)
                op_summary["memory_delta_max_mb"] = max(mem_list)

            summary[op] = op_summary

        return summary

    def finish(self) -> None:
        """Mark the session as finished."""
        self.end_time = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """Convert session to dictionary.

        Returns:
            Dictionary representation of the session
        """
        return {
            "name": self.name,
            "description": self.description,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": (
                (self.end_time - self.start_time).total_seconds() * 1000
                if self.end_time
                else None
            ),
            "metadata": self.metadata,
            "results": [r.to_dict() for r in self.results],
            "summary": self.get_summary(),
        }

    def export_json(self, path: str | Path) -> None:
        """Export session to JSON file.

        Args:
            path: Output file path
        """
        path = Path(path)
        path.write_text(json.dumps(self.to_dict(), indent=2))
        logger.info(f"Profile exported to {path}")

    @classmethod
    def import_json(cls, path: str | Path) -> ProfileSession:
        """Import session from JSON file.

        Args:
            path: Input file path

        Returns:
            ProfileSession reconstructed from JSON
        """
        path = Path(path)
        data = json.loads(path.read_text())

        session = cls(
            name=data["name"],
            description=data.get("description", ""),
            track_memory=True,
        )
        session.start_time = datetime.fromisoformat(data["start_time"])
        if data.get("end_time"):
            session.end_time = datetime.fromisoformat(data["end_time"])
        session.metadata = data.get("metadata", {})

        for result_data in data.get("results", []):
            result = TimingResult(
                operation=result_data["operation"],
                duration_ms=result_data["duration_ms"],
                start_time=datetime.fromisoformat(result_data["start_time"]),
                end_time=datetime.fromisoformat(result_data["end_time"]),
                memory_start_mb=result_data.get("memory_start_mb"),
                memory_end_mb=result_data.get("memory_end_mb"),
                memory_delta_mb=result_data.get("memory_delta_mb"),
                metadata=result_data.get("metadata", {}),
            )
            session.results.append(result)

        return session

    def __enter__(self) -> ProfileSession:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - finish the session."""
        self.finish()


class OperationProfiler:
    """Context manager for profiling individual operations.

    Automatically tracks timing and optionally memory usage.

    Example:
        >>> with ProfileSession("test") as session:
        ...     with OperationProfiler("parsing", session) as op:
        ...         result = parse_document(path)
        ...     print(f"Took {op.duration_ms:.2f}ms")
    """

    def __init__(
        self,
        operation: str,
        session: ProfileSession | None = None,
        track_memory: bool | None = None,
        gc_before: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Initialise operation profiler.

        Args:
            operation: Operation name
            session: ProfileSession to record to (optional)
            track_memory: Track memory usage (inherits from session if None)
            gc_before: Run garbage collection before timing
            metadata: Additional metadata to record
        """
        self.operation = operation
        self.session = session
        self.gc_before = gc_before
        self.metadata = metadata or {}

        # Determine memory tracking
        if track_memory is not None:
            self.track_memory = track_memory
        elif session is not None:
            self.track_memory = session.track_memory
        else:
            self.track_memory = True

        # Timing state
        self._start_time: datetime | None = None
        self._end_time: datetime | None = None
        self._start_perf: float = 0.0
        self._memory_start: float | None = None
        self._memory_end: float | None = None
        self._result: TimingResult | None = None

    @property
    def duration_ms(self) -> float:
        """Duration in milliseconds (available after exit)."""
        return self._result.duration_ms if self._result else 0.0

    @property
    def memory_delta_mb(self) -> float | None:
        """Memory delta in MB (available after exit if tracked)."""
        return self._result.memory_delta_mb if self._result else None

    @property
    def result(self) -> TimingResult | None:
        """The timing result (available after exit)."""
        return self._result

    def __enter__(self) -> OperationProfiler:
        """Start timing."""
        if self.gc_before:
            gc.collect()

        self._start_time = datetime.now()
        self._start_perf = time.perf_counter()

        if self.track_memory:
            self._memory_start = get_memory_mb()

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Stop timing and record result."""
        end_perf = time.perf_counter()
        self._end_time = datetime.now()

        duration_ms = (end_perf - self._start_perf) * 1000

        if self.track_memory:
            self._memory_end = get_memory_mb()

        # Create result
        self._result = TimingResult(
            operation=self.operation,
            duration_ms=duration_ms,
            start_time=self._start_time,  # type: ignore
            end_time=self._end_time,
            memory_start_mb=self._memory_start,
            memory_end_mb=self._memory_end,
            memory_delta_mb=(
                self._memory_end - self._memory_start
                if self._memory_start is not None and self._memory_end is not None
                else None
            ),
            metadata=self.metadata,
        )

        # Record to session if provided
        if self.session is not None:
            self.session.add_result(self._result)


@contextmanager
def track_memory(gc_before: bool = True) -> Generator[dict[str, float], None, None]:
    """Context manager for tracking memory delta during an operation.

    Args:
        gc_before: Run garbage collection before tracking

    Yields:
        Dictionary that will contain start_mb, end_mb, delta_mb after exit

    Example:
        >>> with track_memory() as mem:
        ...     process_large_file()
        >>> print(f"Memory used: {mem['delta_mb']:.1f}MB")
    """
    if gc_before:
        gc.collect()

    result: dict[str, float] = {"start_mb": get_memory_mb()}

    try:
        yield result
    finally:
        gc.collect()
        result["end_mb"] = get_memory_mb()
        result["delta_mb"] = result["end_mb"] - result["start_mb"]


def profile(
    operation: str | None = None,
    track_memory: bool = True,
    gc_before: bool = False,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for profiling function execution.

    Records timing (and optionally memory) for each function call.
    Results are logged at DEBUG level.

    Args:
        operation: Operation name (defaults to function name)
        track_memory: Whether to track memory usage
        gc_before: Run garbage collection before timing

    Returns:
        Decorated function

    Example:
        >>> @profile(operation="parse_document")
        ... def parse_document(path: Path) -> Document:
        ...     # parsing logic
        ...     return document
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        op_name = operation or func.__name__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            with OperationProfiler(
                operation=op_name,
                track_memory=track_memory,
                gc_before=gc_before,
            ) as profiler:
                result = func(*args, **kwargs)

            logger.debug(
                f"Profile {op_name}: {profiler.duration_ms:.2f}ms"
                + (
                    f", memory delta: {profiler.memory_delta_mb:.1f}MB"
                    if profiler.memory_delta_mb is not None
                    else ""
                )
            )
            return result

        return wrapper

    return decorator


def compare_profiles(
    baseline: ProfileSession,
    current: ProfileSession,
    operations: list[str] | None = None,
) -> dict[str, Any]:
    """Compare two profile sessions.

    Args:
        baseline: Baseline profile session
        current: Current profile session to compare
        operations: Specific operations to compare (all if None)

    Returns:
        Comparison dictionary with regression/improvement analysis
    """
    baseline_summary = baseline.get_summary()
    current_summary = current.get_summary()

    ops_to_compare = operations or list(
        set(baseline_summary.keys()) | set(current_summary.keys())
    )

    comparison: dict[str, Any] = {
        "baseline": baseline.name,
        "current": current.name,
        "operations": {},
    }

    for op in ops_to_compare:
        base = baseline_summary.get(op, {})
        curr = current_summary.get(op, {})

        if not base and not curr:
            continue

        op_comparison: dict[str, Any] = {}

        if base and curr:
            base_mean = base["mean_ms"]
            curr_mean = curr["mean_ms"]

            if base_mean > 0:
                change_pct = ((curr_mean - base_mean) / base_mean) * 100
                op_comparison["change_pct"] = change_pct
                op_comparison["status"] = (
                    "regression" if change_pct > 5 else "improvement" if change_pct < -5 else "stable"
                )
            else:
                op_comparison["change_pct"] = 0.0
                op_comparison["status"] = "new"

            op_comparison["baseline_mean_ms"] = base_mean
            op_comparison["current_mean_ms"] = curr_mean
            op_comparison["delta_ms"] = curr_mean - base_mean

        elif curr:
            op_comparison["status"] = "new"
            op_comparison["current_mean_ms"] = curr["mean_ms"]
        else:
            op_comparison["status"] = "removed"
            op_comparison["baseline_mean_ms"] = base["mean_ms"]

        comparison["operations"][op] = op_comparison

    return comparison
