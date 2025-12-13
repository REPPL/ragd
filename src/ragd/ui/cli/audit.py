"""CLI commands for operation audit trail (F-112).

Provides commands for viewing and managing the audit log.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ragd.operations.audit import AuditEntry, get_audit_log


def _parse_date(date_str: str) -> datetime:
    """Parse date string in various formats.

    Args:
        date_str: Date string to parse

    Returns:
        Parsed datetime

    Raises:
        ValueError: If date cannot be parsed
    """
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {date_str}")


def _format_entry_row(entry: AuditEntry) -> tuple[str, str, str, str, str]:
    """Format an audit entry for table display.

    Args:
        entry: Audit entry to format

    Returns:
        Tuple of formatted values
    """
    # Format timestamp
    ts = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    # Format result with colour
    result_styles = {
        "success": "green",
        "partial": "yellow",
        "failed": "red",
    }
    result_style = result_styles.get(entry.result, "white")
    result = f"[{result_style}]{entry.result}[/{result_style}]"

    # Format duration
    if entry.duration_ms < 1000:
        duration = f"{entry.duration_ms}ms"
    elif entry.duration_ms < 60000:
        duration = f"{entry.duration_ms / 1000:.1f}s"
    else:
        duration = f"{entry.duration_ms / 60000:.1f}m"

    # Truncate target
    target = str(entry.target) if entry.target else "-"
    if len(target) > 40:
        target = "..." + target[-37:]

    return entry.id[:8], ts, entry.operation, result, target


def audit_list_command(
    console: Console,
    operation: Annotated[
        str | None,
        typer.Option(
            "--operation", "-o",
            help="Filter by operation type (index, delete, search, etc.)",
        ),
    ] = None,
    result: Annotated[
        str | None,
        typer.Option(
            "--result", "-r",
            help="Filter by result (success, partial, failed)",
        ),
    ] = None,
    since: Annotated[
        str | None,
        typer.Option(
            "--since",
            help="Show entries since date (YYYY-MM-DD)",
        ),
    ] = None,
    until: Annotated[
        str | None,
        typer.Option(
            "--until",
            help="Show entries until date (YYYY-MM-DD)",
        ),
    ] = None,
    limit: Annotated[
        int,
        typer.Option(
            "--limit", "-n",
            help="Maximum entries to show",
        ),
    ] = 20,
    output_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Output as JSON",
        ),
    ] = False,
) -> None:
    """List recent operations from the audit log.

    Shows a table of recent operations with their results.
    """
    audit_log = get_audit_log()

    # Parse dates
    since_dt = _parse_date(since) if since else None
    until_dt = _parse_date(until) if until else None

    # Get entries
    entries = audit_log.list(
        operation=operation,
        result=result,
        since=since_dt,
        until=until_dt,
        limit=limit,
    )

    if output_json:
        data = [e.to_dict() for e in entries]
        console.print_json(json.dumps(data, default=str))
        return

    if not entries:
        console.print("[dim]No audit entries found.[/dim]")
        return

    # Create table
    table = Table(title="Operation Audit Log")
    table.add_column("ID", style="dim")
    table.add_column("Timestamp")
    table.add_column("Operation")
    table.add_column("Result")
    table.add_column("Target")

    for entry in entries:
        row = _format_entry_row(entry)
        table.add_row(*row)

    console.print(table)

    # Show total count
    total = audit_log.count(operation=operation, result=result)
    if total > limit:
        console.print(f"\n[dim]Showing {limit} of {total} entries. Use --limit to see more.[/dim]")


def audit_show_command(
    console: Console,
    entry_id: Annotated[
        str,
        typer.Argument(
            help="ID of the audit entry to show (or prefix)",
        ),
    ],
    output_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Output as JSON",
        ),
    ] = False,
) -> None:
    """Show details of a specific audit entry.

    Displays full details including operation-specific metadata.
    """
    audit_log = get_audit_log()

    # Try to find by exact ID or prefix
    entry = audit_log.get(entry_id)
    if not entry:
        # Try prefix match
        entries = audit_log.list(limit=100)
        matches = [e for e in entries if e.id.startswith(entry_id)]
        if len(matches) == 1:
            entry = matches[0]
        elif len(matches) > 1:
            console.print(f"[yellow]Multiple entries match prefix '{entry_id}':[/yellow]")
            for e in matches[:5]:
                console.print(f"  {e.id[:12]} - {e.operation}")
            return
        else:
            console.print(f"[red]Audit entry not found: {entry_id}[/red]")
            raise typer.Exit(1)

    if output_json:
        console.print_json(json.dumps(entry.to_dict(), default=str))
        return

    # Display entry details
    result_styles = {
        "success": "green",
        "partial": "yellow",
        "failed": "red",
    }
    result_style = result_styles.get(entry.result, "white")

    content = Table(show_header=False, box=None, padding=(0, 2))
    content.add_column("Field", style="dim")
    content.add_column("Value")

    content.add_row("ID:", entry.id)
    content.add_row("Timestamp:", entry.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
    content.add_row("Operation:", entry.operation)
    content.add_row("Result:", f"[{result_style}]{entry.result}[/{result_style}]")
    content.add_row("Target:", str(entry.target) if entry.target else "-")
    content.add_row("Duration:", f"{entry.duration_ms}ms")

    # Add details
    if entry.details:
        content.add_row("", "")
        content.add_row("[bold]Details:[/bold]", "")
        for key, value in entry.details.items():
            content.add_row(f"  {key}:", str(value))

    panel = Panel(
        content,
        title="[bold]Audit Entry[/bold]",
        border_style="blue",
    )
    console.print(panel)


def audit_clear_command(
    console: Console,
    before: Annotated[
        str | None,
        typer.Option(
            "--before",
            help="Clear entries before date (YYYY-MM-DD)",
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(
            "--force", "-f",
            help="Skip confirmation prompt",
        ),
    ] = False,
) -> None:
    """Clear audit log entries.

    Removes old entries from the audit log.
    """
    audit_log = get_audit_log()

    before_dt = _parse_date(before) if before else None
    count = audit_log.count()

    if count == 0:
        console.print("[dim]Audit log is empty.[/dim]")
        return

    # Confirm
    if not force:
        if before_dt:
            msg = f"Clear {count} entries before {before}?"
        else:
            msg = f"Clear all {count} audit entries?"

        if not typer.confirm(msg):
            console.print("[dim]Cancelled.[/dim]")
            return

    # Clear
    removed = audit_log.clear(before=before_dt)
    console.print(f"[green]Cleared {removed} audit entries.[/green]")


def audit_stats_command(
    console: Console,
    output_json: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Output as JSON",
        ),
    ] = False,
) -> None:
    """Show audit log statistics.

    Displays summary of operations in the audit log.
    """
    audit_log = get_audit_log()

    total = audit_log.count()

    if total == 0:
        console.print("[dim]Audit log is empty.[/dim]")
        return

    # Count by operation and result
    operations = ["index", "delete", "search", "doctor", "reindex"]
    results = ["success", "partial", "failed"]

    stats = {
        "total": total,
        "by_operation": {},
        "by_result": {},
    }

    for op in operations:
        count = audit_log.count(operation=op)
        if count > 0:
            stats["by_operation"][op] = count

    for res in results:
        count = audit_log.count(result=res)
        if count > 0:
            stats["by_result"][res] = count

    if output_json:
        console.print_json(json.dumps(stats))
        return

    # Display stats
    table = Table(title="Audit Log Statistics")
    table.add_column("Metric", style="dim")
    table.add_column("Value")

    table.add_row("Total entries:", str(total))
    table.add_row("", "")

    if stats["by_operation"]:
        table.add_row("[bold]By Operation:[/bold]", "")
        for op, count in stats["by_operation"].items():
            table.add_row(f"  {op}", str(count))

    if stats["by_result"]:
        table.add_row("", "")
        table.add_row("[bold]By Result:[/bold]", "")
        result_styles = {
            "success": "green",
            "partial": "yellow",
            "failed": "red",
        }
        for res, count in stats["by_result"].items():
            style = result_styles.get(res, "white")
            table.add_row(f"  [{style}]{res}[/{style}]", str(count))

    console.print(table)
