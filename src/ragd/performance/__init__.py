"""Performance profiling framework for ragd (F-123).

This module provides comprehensive profiling capabilities for all ragd operations:
- Timing with millisecond precision
- Memory tracking via psutil
- Profile sessions for grouping related measurements
- JSON export/import for comparison
- Rich terminal reports

Example:
    >>> from ragd.performance import OperationProfiler, ProfileSession
    >>> with ProfileSession("indexing_benchmark") as session:
    ...     with OperationProfiler("document_parsing", session):
    ...         parse_document(path)
    ...     with OperationProfiler("embedding_generation", session):
    ...         generate_embeddings(chunks)
    >>> session.export_json("profile.json")
"""

from __future__ import annotations

from ragd.performance.memory import (
    MemoryBudget,
    MemoryDelta,
    MemoryMonitor,
    MemorySnapshot,
    estimate_memory_for_embeddings,
    force_gc,
    gc_after_operation,
    get_current_memory_mb,
    get_peak_memory_mb,
    get_system_memory_info,
    suggest_batch_size,
    track_memory,
)
from ragd.performance.metrics import (
    ChatProfile,
    IndexingProfile,
    ProfileMetric,
    SearchProfile,
)
from ragd.performance.profiler import (
    OperationProfiler,
    ProfileSession,
    profile,
)
from ragd.performance.reports import (
    format_profile_report,
    print_profile_report,
)

__all__ = [
    # Core profiling
    "ProfileSession",
    "OperationProfiler",
    "profile",
    # Metrics
    "ProfileMetric",
    "IndexingProfile",
    "SearchProfile",
    "ChatProfile",
    # Reporting
    "format_profile_report",
    "print_profile_report",
    # Memory (F-124)
    "get_current_memory_mb",
    "get_peak_memory_mb",
    "get_system_memory_info",
    "track_memory",
    "MemoryBudget",
    "MemoryMonitor",
    "MemorySnapshot",
    "MemoryDelta",
    "force_gc",
    "gc_after_operation",
    "estimate_memory_for_embeddings",
    "suggest_batch_size",
]
