"""Error message formatters for ragd CLI.

Provides Rich-based error display with:
- Clear error titles
- File paths
- Categorised reasons
- Actionable hints
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ragd.operations.errors import (
    REMEDIATION_HINTS,
    BatchResult,
    DocumentResult,
    IndexingErrorCategory,
)


def format_error(
    result: DocumentResult,
    show_hint: bool = True,
) -> Panel:
    """Format a single error result as a Rich Panel.

    Args:
        result: The failed document result
        show_hint: Whether to include remediation hint

    Returns:
        Rich Panel with error details
    """
    # Build error content
    lines: list[Text] = []

    # Path
    path_text = Text()
    path_text.append("  Path: ", style="dim")
    path_text.append(str(result.path), style="cyan")
    lines.append(path_text)

    # Category
    if result.category:
        cat_text = Text()
        cat_text.append("  Type: ", style="dim")
        cat_text.append(result.category.value.replace("_", " ").title(), style="yellow")
        lines.append(cat_text)

    # Error message
    if result.message:
        msg_text = Text()
        msg_text.append("Reason: ", style="dim")
        # Truncate long messages
        msg = result.message
        if len(msg) > 100:
            msg = msg[:97] + "..."
        msg_text.append(msg, style="white")
        lines.append(msg_text)

    # Hint
    if show_hint and result.hint:
        hint_text = Text()
        hint_text.append("\n  Hint: ", style="dim")
        hint_text.append(result.hint, style="green")
        lines.append(hint_text)

    # Combine lines
    content = Text("\n").join(lines)

    return Panel(
        content,
        title="[bold red]Error[/bold red]",
        border_style="red",
        padding=(0, 1),
    )


def format_errors_summary(
    batch: BatchResult,
    console: Console | None = None,
    max_errors: int = 5,
    show_all: bool = False,
) -> None:
    """Display a summary of errors from a batch operation.

    Args:
        batch: Batch result containing errors
        console: Rich console for output
        max_errors: Maximum individual errors to show
        show_all: If True, show all errors (ignore max_errors)
    """
    if console is None:
        console = Console()

    failed = batch.get_failed()
    if not failed:
        return

    # Header
    console.print()
    console.print(f"[bold red]Failed: {len(failed)} document(s)[/bold red]")
    console.print()

    # Errors by category
    by_category = batch.failures_by_category
    if len(by_category) > 1:
        # Show category breakdown
        cat_table = Table(show_header=False, box=None, padding=(0, 2))
        cat_table.add_column("Category", style="yellow")
        cat_table.add_column("Count", style="white")

        for category, count in sorted(
            by_category.items(), key=lambda x: x[1], reverse=True
        ):
            cat_table.add_row(
                category.value.replace("_", " ").title(),
                str(count),
            )

        console.print(cat_table)
        console.print()

    # Show individual errors
    errors_to_show = failed if show_all else failed[:max_errors]
    for result in errors_to_show:
        console.print(format_error(result))

    # Show truncation notice
    remaining = len(failed) - len(errors_to_show)
    if remaining > 0:
        console.print(
            f"\n[dim]... and {remaining} more error(s). "
            f"Use --verbose to see all.[/dim]"
        )

    # Show remediation summary
    console.print()
    _show_remediation_summary(by_category, console)


def _show_remediation_summary(
    by_category: dict[IndexingErrorCategory, int],
    console: Console,
) -> None:
    """Show summary of remediation steps for each error category.

    Args:
        by_category: Count of errors by category
        console: Rich console
    """
    if not by_category:
        return

    console.print("[bold]Suggested actions:[/bold]")
    console.print()

    for category in sorted(by_category.keys(), key=lambda c: by_category[c], reverse=True):
        hint = REMEDIATION_HINTS.get(category, "Check error details above.")
        # Shorten hint for summary
        if len(hint) > 80:
            hint = hint[:77] + "..."

        text = Text()
        text.append("  • ", style="dim")
        text.append(f"{category.value.replace('_', ' ').title()}: ", style="yellow")
        text.append(hint, style="white")
        console.print(text)


def format_error_simple(
    path: str,
    error: str,
    hint: str | None = None,
) -> str:
    """Format an error as a simple string (for non-Rich output).

    Args:
        path: File path
        error: Error message
        hint: Optional hint

    Returns:
        Formatted error string
    """
    lines = [
        f"Error: {error}",
        f"  Path: {path}",
    ]
    if hint:
        lines.append(f"  Hint: {hint}")

    return "\n".join(lines)
