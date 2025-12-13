"""User interface components for ragd.

This module provides UI implementations for different interfaces:
- cli: Command-line interface (Typer)
- tui: Terminal user interface (Textual)
- web: Web interface (future)
"""

from ragd.ui.formatters import (
    CitationStyleOption,
    OutputFormat,
    format_health_results,
    format_index_results,
    format_search_results,
    format_status,
)

__all__ = [
    "CitationStyleOption",
    "OutputFormat",
    "format_search_results",
    "format_status",
    "format_index_results",
    "format_health_results",
]
