"""Operation summary formatters for ragd CLI.

Provides Rich-based summary display for:
- Indexing operations
- Batch operations
- Statistics
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ragd.operations.errors import BatchResult


def format_summary(
    succeeded: int,
    failed: int,
    skipped: int,
    chunks: int,
    duration_seconds: float,
    images: int = 0,
) -> Panel:
    """Format an operation summary as a Rich Panel.

    Args:
        succeeded: Number of successful documents
        failed: Number of failed documents
        skipped: Number of skipped documents
        chunks: Total chunks created
        duration_seconds: Operation duration
        images: Total images extracted

    Returns:
        Rich Panel with summary
    """
    # Build summary table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Metric", style="dim")
    table.add_column("Value", style="bold")

    # Documents row with color-coded status
    docs_text = Text()
    docs_text.append(f"{succeeded}", style="green")
    docs_text.append(" indexed")
    if skipped > 0:
        docs_text.append(f", {skipped}", style="yellow")
        docs_text.append(" skipped")
    if failed > 0:
        docs_text.append(f", {failed}", style="red")
        docs_text.append(" failed")
    table.add_row("Documents:", docs_text)

    # Chunks
    table.add_row("Chunks:", f"{chunks:,}")

    # Images (if any)
    if images > 0:
        table.add_row("Images:", f"{images:,}")

    # Duration
    duration_str = _format_duration(duration_seconds)
    table.add_row("Duration:", duration_str)

    # Determine panel style based on success/failure
    if failed > 0:
        title = "[bold yellow]Indexing Complete (with errors)[/bold yellow]"
        border_style = "yellow"
    elif succeeded == 0 and skipped > 0:
        title = "[bold]Indexing Complete (all skipped)[/bold]"
        border_style = "dim"
    else:
        title = "[bold green]Indexing Complete[/bold green]"
        border_style = "green"

    return Panel(
        table,
        title=title,
        border_style=border_style,
        padding=(0, 1),
    )


def format_batch_summary(
    batch: BatchResult,
    console: Console | None = None,
) -> None:
    """Display a batch operation summary.

    Args:
        batch: Batch result to summarise
        console: Rich console for output
    """
    if console is None:
        console = Console()

    panel = format_summary(
        succeeded=batch.succeeded,
        failed=batch.failed,
        skipped=batch.skipped,
        chunks=batch.total_chunks,
        duration_seconds=batch.duration_seconds,
        images=batch.total_images,
    )

    console.print()
    console.print(panel)

    # Suggest next action
    if batch.failed == 0 and batch.succeeded > 0:
        console.print("\n[dim]Run 'ragd search <query>' to search your documents.[/dim]")
    elif batch.failed > 0:
        console.print("\n[dim]Run 'ragd doctor' to diagnose indexing issues.[/dim]")


def format_status_summary(
    total_documents: int,
    total_chunks: int,
    total_images: int = 0,
    storage_mb: float = 0.0,
    console: Console | None = None,
) -> None:
    """Display index status summary.

    Args:
        total_documents: Number of indexed documents
        total_chunks: Total chunks in index
        total_images: Total images in index
        storage_mb: Storage size in MB
        console: Rich console for output
    """
    if console is None:
        console = Console()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Metric", style="dim")
    table.add_column("Value", style="bold")

    table.add_row("Documents:", f"{total_documents:,}")
    table.add_row("Chunks:", f"{total_chunks:,}")

    if total_images > 0:
        table.add_row("Images:", f"{total_images:,}")

    if storage_mb > 0:
        table.add_row("Storage:", f"{storage_mb:.1f} MB")

    panel = Panel(
        table,
        title="[bold]Index Status[/bold]",
        border_style="blue",
        padding=(0, 1),
    )

    console.print(panel)


def format_dry_run_summary(
    would_index: int,
    would_skip: int,
    would_fail: int = 0,
    console: Console | None = None,
) -> None:
    """Display dry-run summary.

    Args:
        would_index: Documents that would be indexed
        would_skip: Documents that would be skipped
        would_fail: Documents that would fail (predicted)
        console: Rich console for output
    """
    if console is None:
        console = Console()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Action", style="dim")
    table.add_column("Count", style="bold")

    table.add_row("Would index:", f"{would_index}")
    table.add_row("Would skip:", f"{would_skip}")
    if would_fail > 0:
        table.add_row("Would fail:", Text(str(would_fail), style="red"))

    panel = Panel(
        table,
        title="[bold yellow][DRY RUN] Preview[/bold yellow]",
        border_style="yellow",
        padding=(0, 1),
    )

    console.print()
    console.print(panel)
    console.print("\n[dim]No changes made. Remove --dry-run to proceed.[/dim]")


def _format_duration(seconds: float) -> str:
    """Format duration in human-readable form.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def format_simple_summary(
    succeeded: int,
    failed: int,
    skipped: int,
    chunks: int,
    duration_seconds: float,
) -> str:
    """Format a simple text summary (for non-Rich output).

    Args:
        succeeded: Number of successful documents
        failed: Number of failed documents
        skipped: Number of skipped documents
        chunks: Total chunks created
        duration_seconds: Operation duration

    Returns:
        Simple text summary
    """
    lines = [
        "Indexing Complete",
        f"  Documents: {succeeded} indexed, {skipped} skipped, {failed} failed",
        f"  Chunks: {chunks:,}",
        f"  Duration: {_format_duration(duration_seconds)}",
    ]
    return "\n".join(lines)
