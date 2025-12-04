"""Output formatting utilities for ragd (F-090).

Provides consistent output formatting across all CLI commands.
"""

from __future__ import annotations

import csv
import io
import json
import os
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, TypeVar

from rich.console import Console
from rich.table import Table


class OutputFormat(str, Enum):
    """Output format options."""

    RICH = "rich"
    PLAIN = "plain"
    JSON = "json"
    CSV = "csv"


def get_output_format(format_arg: str | None = None) -> OutputFormat:
    """Get output format from argument or environment.

    Args:
        format_arg: Format argument from CLI

    Returns:
        OutputFormat enum value
    """
    # CLI argument takes precedence
    if format_arg:
        try:
            return OutputFormat(format_arg.lower())
        except ValueError:
            pass

    # Check environment variable
    env_format = os.environ.get("RAGD_OUTPUT_FORMAT", "").lower()
    if env_format:
        try:
            return OutputFormat(env_format)
        except ValueError:
            pass

    return OutputFormat.RICH


def format_output(
    data: Any,
    format: OutputFormat,
    console: Console | None = None,
    table_title: str | None = None,
    table_columns: list[str] | None = None,
) -> str | None:
    """Format data according to output format.

    Args:
        data: Data to format (dict, list, or dataclass)
        format: Output format
        console: Rich console (required for RICH format)
        table_title: Title for table output
        table_columns: Column headers for table/CSV output

    Returns:
        Formatted string for JSON/PLAIN/CSV, None for RICH (prints directly)
    """
    if format == OutputFormat.JSON:
        return _format_json(data)
    elif format == OutputFormat.CSV:
        return _format_csv(data, table_columns)
    elif format == OutputFormat.PLAIN:
        return _format_plain(data)
    else:  # RICH
        if console:
            _format_rich(data, console, table_title, table_columns)
        return None


def _format_json(data: Any) -> str:
    """Format data as JSON."""
    return json.dumps(_serialise(data), indent=2, ensure_ascii=False)


def _format_csv(data: Any, columns: list[str] | None = None) -> str:
    """Format data as CSV."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Ensure data is a list
    if not isinstance(data, list):
        data = [data]

    if not data:
        return ""

    # Get columns from first item if not provided
    if not columns:
        first = data[0]
        if isinstance(first, dict):
            columns = list(first.keys())
        elif is_dataclass(first):
            columns = list(asdict(first).keys())
        else:
            columns = ["value"]

    # Write header
    writer.writerow(columns)

    # Write rows
    for item in data:
        if isinstance(item, dict):
            row = [str(item.get(col, "")) for col in columns]
        elif is_dataclass(item):
            item_dict = asdict(item)
            row = [str(item_dict.get(col, "")) for col in columns]
        else:
            row = [str(item)]
        writer.writerow(row)

    return output.getvalue()


def _format_plain(data: Any) -> str:
    """Format data as plain text."""
    if isinstance(data, str):
        return data
    elif isinstance(data, dict):
        lines = []
        for key, value in data.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)
    elif isinstance(data, list):
        return "\n".join(str(item) for item in data)
    elif is_dataclass(data):
        return _format_plain(asdict(data))
    else:
        return str(data)


def _format_rich(
    data: Any,
    console: Console,
    title: str | None = None,
    columns: list[str] | None = None,
) -> None:
    """Format data using Rich."""
    if isinstance(data, list) and data:
        # Table output
        first = data[0]
        if isinstance(first, dict):
            cols = columns or list(first.keys())
        elif is_dataclass(first):
            cols = columns or list(asdict(first).keys())
        else:
            cols = columns or ["value"]

        table = Table(title=title)
        for col in cols:
            table.add_column(col.replace("_", " ").title())

        for item in data:
            if isinstance(item, dict):
                row = [str(item.get(col, "")) for col in cols]
            elif is_dataclass(item):
                item_dict = asdict(item)
                row = [str(item_dict.get(col, "")) for col in cols]
            else:
                row = [str(item)]
            table.add_row(*row)

        console.print(table)

    elif isinstance(data, dict):
        if title:
            console.print(f"\n[bold]{title}[/bold]\n")
        for key, value in data.items():
            console.print(f"[cyan]{key}[/cyan]: {value}")

    else:
        console.print(data)


def _serialise(obj: Any) -> Any:
    """Serialise object for JSON output."""
    if is_dataclass(obj):
        return asdict(obj)
    elif isinstance(obj, dict):
        return {k: _serialise(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialise(v) for v in obj]
    elif isinstance(obj, Path):
        return str(obj)
    elif isinstance(obj, Enum):
        return obj.value
    elif hasattr(obj, "__dict__"):
        return {k: _serialise(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    else:
        return obj


class OutputWriter:
    """Utility class for consistent output across commands."""

    def __init__(
        self,
        format: OutputFormat | str = OutputFormat.RICH,
        no_color: bool = False,
    ):
        """Initialise output writer.

        Args:
            format: Output format
            no_color: Disable colours
        """
        if isinstance(format, str):
            format = get_output_format(format)

        self.format = format
        self.console = Console(no_color=no_color or format != OutputFormat.RICH)

    def print(self, data: Any, title: str | None = None, columns: list[str] | None = None) -> None:
        """Print data in configured format.

        Args:
            data: Data to print
            title: Optional title
            columns: Optional column headers
        """
        result = format_output(
            data,
            self.format,
            self.console,
            table_title=title,
            table_columns=columns,
        )

        if result is not None:
            # JSON/CSV/PLAIN output
            print(result)

    def success(self, message: str) -> None:
        """Print success message."""
        if self.format == OutputFormat.JSON:
            print(json.dumps({"status": "success", "message": message}))
        elif self.format == OutputFormat.RICH:
            self.console.print(f"[green]✓[/green] {message}")
        else:
            print(f"OK: {message}")

    def error(self, message: str) -> None:
        """Print error message."""
        if self.format == OutputFormat.JSON:
            print(json.dumps({"status": "error", "message": message}))
        elif self.format == OutputFormat.RICH:
            self.console.print(f"[red]✗[/red] {message}")
        else:
            print(f"ERROR: {message}")

    def warning(self, message: str) -> None:
        """Print warning message."""
        if self.format == OutputFormat.JSON:
            print(json.dumps({"status": "warning", "message": message}))
        elif self.format == OutputFormat.RICH:
            self.console.print(f"[yellow]![/yellow] {message}")
        else:
            print(f"WARNING: {message}")

    def info(self, message: str) -> None:
        """Print info message."""
        if self.format == OutputFormat.JSON:
            pass  # Skip info in JSON mode
        elif self.format == OutputFormat.RICH:
            self.console.print(f"[dim]{message}[/dim]")
        else:
            print(message)
