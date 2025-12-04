"""UI formatters for ragd CLI.

Provides Rich-based formatters for:
- Progress indicators (F-114)
- Error messages with hints (F-114)
- Operation summaries (F-114)
- Search results, status, health (legacy)
"""

# New F-114 formatters
from ragd.ui.formatters.progress import IndexingProgress, create_progress
from ragd.ui.formatters.errors import format_error, format_errors_summary
from ragd.ui.formatters.summaries import format_summary, format_batch_summary

# Legacy formatters (from original formatters.py, now in _legacy.py)
from ragd.ui.formatters._legacy import (
    OutputFormat,
    CitationStyleOption,
    format_search_results,
    format_status,
    format_index_results,
    format_health_results,
)

__all__ = [
    # New F-114 formatters
    "IndexingProgress",
    "create_progress",
    "format_error",
    "format_errors_summary",
    "format_summary",
    "format_batch_summary",
    # Legacy formatters
    "OutputFormat",
    "CitationStyleOption",
    "format_search_results",
    "format_status",
    "format_index_results",
    "format_health_results",
]
