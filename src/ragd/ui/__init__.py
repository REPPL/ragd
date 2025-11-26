"""User interface components for ragd.

This module provides UI implementations for different interfaces:
- cli: Command-line interface (Typer)
- tui: Terminal user interface (Textual)
- web: Web interface (future)
"""

from ragd.ui.formatters import (
    OutputFormat,
    format_search_results,
    format_status,
    format_index_results,
    format_health_results,
)

__all__ = [
    "OutputFormat",
    "format_search_results",
    "format_status",
    "format_index_results",
    "format_health_results",
]
