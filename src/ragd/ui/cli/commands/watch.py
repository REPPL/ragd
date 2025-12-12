"""Watch CLI commands for ragd.

This module contains commands for watching directories for automatic indexing.
"""

from __future__ import annotations

from pathlib import Path

import typer

from ragd.ui import OutputFormat
from ragd.ui.cli.utils import get_console


def watch_start_command(
    directories: list[Path],
    patterns: list[str] | None = None,
    recursive: bool = True,
    no_color: bool = False,
) -> None:
    """Start watching directories for changes."""
    from ragd.config import load_config
    from ragd.ingestion import index_path
    from ragd.web.watcher import FolderWatcher, WatchConfig, WATCHDOG_AVAILABLE

    con = get_console(no_color)

    if not WATCHDOG_AVAILABLE:
        con.print("[red]Error: watchdog library not installed[/red]")
        con.print("Install with: [cyan]pip install watchdog[/cyan]")
        raise typer.Exit(1)

    # Check if already running
    if FolderWatcher.is_running():
        con.print("[yellow]Watch daemon already running.[/yellow]")
        con.print("Use [cyan]ragd watch stop[/cyan] to stop it first.")
        raise typer.Exit(1)

    # Validate directories
    valid_dirs = []
    for directory in directories:
        if not directory.exists():
            con.print(f"[yellow]Warning: Directory not found: {directory}[/yellow]")
        elif not directory.is_dir():
            con.print(f"[yellow]Warning: Not a directory: {directory}[/yellow]")
        else:
            valid_dirs.append(directory)

    if not valid_dirs:
        con.print("[red]No valid directories specified.[/red]")
        raise typer.Exit(1)

    config = load_config()

    watch_config = WatchConfig(
        directories=valid_dirs,
        patterns=patterns if patterns else None,
        recursive=recursive,
    )

    # Define index callback
    def index_callback(path: Path) -> bool:
        try:
            index_path(path, config=config)
            return True
        except Exception as e:
            con.print(f"[red]Error indexing {path}: {e}[/red]")
            return False

    watcher = FolderWatcher(watch_config, index_callback)

    con.print(f"\n[bold]Starting watch on {len(valid_dirs)} directories...[/bold]\n")
    for directory in valid_dirs:
        con.print(f"  [green]✓[/green] {directory}")

    con.print("\n[dim]Press Ctrl+C to stop[/dim]\n")

    try:
        watcher.start()
        watcher.run()
    except KeyboardInterrupt:
        con.print("\n[yellow]Stopping...[/yellow]")
    finally:
        watcher.stop()
        con.print("[green]✓[/green] Watch stopped")


def watch_stop_command(
    no_color: bool = False,
) -> None:
    """Stop the watch daemon."""
    from ragd.web.watcher import FolderWatcher

    con = get_console(no_color)

    if not FolderWatcher.is_running():
        con.print("[yellow]Watch daemon is not running.[/yellow]")
        return

    if FolderWatcher.stop_daemon():
        con.print("[green]✓[/green] Watch daemon stopped")
    else:
        con.print("[red]Failed to stop watch daemon.[/red]")
        raise typer.Exit(1)


def watch_status_command(
    output_format: OutputFormat = "rich",
    no_color: bool = False,
) -> None:
    """Show watch daemon status."""
    from ragd.web.watcher import FolderWatcher

    con = get_console(no_color)

    if not FolderWatcher.is_running():
        con.print("[dim]Watch daemon is not running.[/dim]")
        return

    status = FolderWatcher.read_status()
    if status is None:
        con.print("[yellow]Status information not available.[/yellow]")
        return

    if output_format == "json":
        import json
        data = {
            "running": status.running,
            "pid": status.pid,
            "uptime_seconds": status.uptime_seconds,
            "directories": status.directories,
            "files_indexed": status.files_indexed,
            "queue_size": status.queue_size,
        }
        con.print(json.dumps(data, indent=2))
    else:
        from rich.table import Table

        table = Table(title="Watch Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value")

        table.add_row("Running", "[green]Yes[/green]" if status.running else "[red]No[/red]")
        table.add_row("PID", str(status.pid) if status.pid else "-")

        hours = int(status.uptime_seconds // 3600)
        minutes = int((status.uptime_seconds % 3600) // 60)
        table.add_row("Uptime", f"{hours}h {minutes}m" if hours else f"{minutes}m")

        table.add_row("Directories", ", ".join(status.directories) or "-")
        table.add_row("Files Indexed", str(status.files_indexed))
        table.add_row("Queue Size", str(status.queue_size))

        con.print(table)

        # Show recent events
        if status.recent_events:
            con.print("\n[bold]Recent Events:[/bold]")
            for event in status.recent_events[-5:]:
                icon = "📄" if event.event_type == "indexed" else "⏭️"
                con.print(f"  {icon} {event.event_type}: {Path(event.path).name}")


__all__ = [
    "watch_start_command",
    "watch_stop_command",
    "watch_status_command",
]
