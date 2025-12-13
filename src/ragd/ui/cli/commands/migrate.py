"""Migrate CLI command for ragd (F-075).

This module contains the backend migration command.
"""

from __future__ import annotations

from typing import Annotated

import typer
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

from ragd.ui.cli.utils import get_console


def migrate_command(
    source: Annotated[str, typer.Option("--from", help="Source backend (chromadb, faiss)")],
    target: Annotated[str, typer.Option("--to", help="Target backend (chromadb, faiss)")],
    batch_size: Annotated[int, typer.Option("--batch-size", "-b", help="Chunks per batch")] = 500,
    validate: Annotated[bool, typer.Option("--validate/--no-validate", help="Run validation after migration")] = True,
    keep_source: Annotated[bool, typer.Option("--keep-source/--delete-source", help="Keep source data")] = True,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Only show what would be migrated")] = False,
    resume: Annotated[bool, typer.Option("--resume", help="Resume interrupted migration")] = False,
    no_color: Annotated[bool, typer.Option("--no-color", help="Disable colour output")] = False,
) -> None:
    """Migrate data between vector store backends.

    Migrate your indexed documents from one backend to another without
    re-indexing. Supports ChromaDB and FAISS backends.

    Examples:

        ragd migrate --from chromadb --to faiss

        ragd migrate --from chromadb --to faiss --dry-run

        ragd migrate --from faiss --to chromadb --no-validate

        ragd migrate --resume
    """
    from ragd.storage.migration import MigrationEngine

    con = get_console(no_color)

    engine = MigrationEngine()

    # Resume mode
    if resume:
        if not engine.has_checkpoint():
            con.print("[red]Error: No migration checkpoint found to resume[/red]")
            raise typer.Exit(1)

        checkpoint = engine.get_checkpoint_info()
        con.print("[bold]Resuming migration from checkpoint[/bold]")
        con.print(f"Source: {checkpoint.manifest.source_backend}")
        con.print(f"Target: {checkpoint.manifest.target_backend}")
        con.print(f"Progress: {checkpoint.chunks_migrated}/{checkpoint.manifest.total_chunks}")
        con.print()

        # Use checkpoint backends
        source = checkpoint.manifest.source_backend
        target = checkpoint.manifest.target_backend

    # Validate backends
    valid_backends = {"chromadb", "faiss"}
    if source not in valid_backends:
        con.print(f"[red]Error: Invalid source backend: {source}[/red]")
        con.print(f"Valid backends: {', '.join(valid_backends)}")
        raise typer.Exit(1)
    if target not in valid_backends:
        con.print(f"[red]Error: Invalid target backend: {target}[/red]")
        con.print(f"Valid backends: {', '.join(valid_backends)}")
        raise typer.Exit(1)
    if source == target:
        con.print("[red]Error: Source and target backends must be different[/red]")
        raise typer.Exit(1)

    # Header
    con.print("[bold]Backend Migration[/bold]")
    con.print(f"Source: {source}")
    con.print(f"Target: {target}")
    con.print(f"Batch size: {batch_size}")
    con.print(f"Validate: {validate}")
    con.print(f"Keep source: {keep_source}")
    if dry_run:
        con.print("[yellow]DRY RUN - No changes will be made[/yellow]")
    con.print()

    # Progress tracking
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=con,
        disable=dry_run,
    ) as progress:
        task = progress.add_task("Migrating...", total=100)

        def progress_callback(migrated: int, total: int, message: str) -> None:
            if total > 0:
                percent = (migrated / total) * 100
                progress.update(task, completed=percent, description=message)

        try:
            result = engine.migrate(
                source_backend=source,
                target_backend=target,
                batch_size=batch_size,
                validate=validate,
                keep_source=keep_source,
                dry_run=dry_run,
                progress_callback=progress_callback,
            )
        except Exception as e:
            con.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)

    # Results
    con.print()
    if result.success:
        con.print("[green]Migration complete![/green]")
    else:
        con.print("[red]Migration failed[/red]")

    con.print(f"Chunks migrated: {result.chunks_migrated}")
    con.print(f"Documents migrated: {result.documents_migrated}")
    con.print(f"Duration: {result.duration_seconds:.1f}s")

    if result.errors:
        con.print()
        con.print("[red]Errors:[/red]")
        for error in result.errors[:10]:  # Limit output
            con.print(f"  • {error}")
        if len(result.errors) > 10:
            con.print(f"  ... and {len(result.errors) - 10} more")

    if validate and not dry_run:
        con.print()
        if result.validation_passed:
            con.print("[green]Validation passed[/green]")
        else:
            con.print("[red]Validation failed[/red]")
            for error in result.validation_errors:
                con.print(f"  • {error}")

    if not result.success:
        raise typer.Exit(1)


def migrate_status_command(
    no_color: Annotated[bool, typer.Option("--no-color", help="Disable colour output")] = False,
) -> None:
    """Show migration checkpoint status if one exists."""
    from ragd.storage.migration import MigrationEngine

    con = get_console(no_color)
    engine = MigrationEngine()

    if not engine.has_checkpoint():
        con.print("No migration checkpoint found.")
        return

    checkpoint = engine.get_checkpoint_info()
    if checkpoint is None:
        con.print("No migration checkpoint found.")
        return

    con.print("[bold]Migration Checkpoint[/bold]")
    con.print()
    con.print(f"Source: {checkpoint.manifest.source_backend}")
    con.print(f"Target: {checkpoint.manifest.target_backend}")
    con.print(f"Progress: {checkpoint.chunks_migrated}/{checkpoint.manifest.total_chunks} ({checkpoint.progress_percent:.1f}%)")
    con.print(f"Started: {checkpoint.started_at}")
    con.print(f"Updated: {checkpoint.updated_at}")

    if checkpoint.errors:
        con.print()
        con.print(f"[yellow]Errors: {len(checkpoint.errors)}[/yellow]")
        for error in checkpoint.errors[:5]:
            con.print(f"  • {error}")

    con.print()
    con.print("[dim]Use 'ragd migrate --resume' to continue[/dim]")


__all__ = [
    "migrate_command",
    "migrate_status_command",
]
