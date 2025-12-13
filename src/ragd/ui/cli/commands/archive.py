"""Archive CLI commands for ragd.

This module contains export and import commands for knowledge base archives.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
)

from ragd.ui import OutputFormat
from ragd.ui.cli.utils import get_console


def export_command(
    output_path: Path,
    no_embeddings: bool = False,
    tag: str | None = None,
    project: str | None = None,
    verbose: bool = False,
    output_format: OutputFormat = "rich",
    no_color: bool = False,
) -> None:
    """Export knowledge base to an archive.

    Creates a portable tar.gz archive containing documents, chunks,
    embeddings, and metadata.
    """
    from ragd.archive import ArchiveFilters, ExportEngine, ExportOptions
    from ragd.config import load_config
    from ragd.metadata import MetadataStore
    from ragd.storage import ChromaStore

    con = get_console(no_color)
    config = load_config()

    store = ChromaStore(config.chroma_path)
    metadata = MetadataStore(config.metadata_path)

    # Build filters
    filters = None
    if tag or project:
        filters = ArchiveFilters(
            tags=[tag] if tag else None,
            project=project,
        )

    options = ExportOptions(
        include_embeddings=not no_embeddings,
        filters=filters,
    )

    engine = ExportEngine(store, metadata)

    con.print(f"\n[bold]Exporting to: {output_path}[/bold]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        console=con,
        transient=False,
    ) as progress:
        task = progress.add_task("Exporting...", total=100)

        def progress_callback(current: int, total: int, stage: str) -> None:
            pct = int((current / total) * 100) if total > 0 else 0
            progress.update(task, completed=pct, description=f"[dim]{stage}[/dim]")

        result = engine.export(output_path, options, progress_callback=progress_callback)
        progress.update(task, completed=100, description="[green]Complete[/green]")

    # Summary
    con.print()
    con.print(f"[green]✓[/green] Export complete: {output_path}")
    con.print(f"  Documents: {result.document_count}")
    con.print(f"  Chunks: {result.chunk_count}")
    if result.archive_size_bytes:
        size_mb = result.archive_size_bytes / (1024 * 1024)
        con.print(f"  Size: {size_mb:.1f} MB")


def import_command(
    archive_path: Path,
    skip_conflicts: bool = False,
    overwrite: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
    output_format: OutputFormat = "rich",
    no_color: bool = False,
) -> None:
    """Import knowledge base from an archive.

    Restores documents, chunks, embeddings, and metadata from
    a portable tar.gz archive.
    """
    from ragd.archive import ConflictResolution, ImportEngine, ImportOptions
    from ragd.config import load_config
    from ragd.metadata import MetadataStore
    from ragd.storage import ChromaStore

    con = get_console(no_color)
    config = load_config()

    if not archive_path.exists():
        con.print(f"[red]Archive not found: {archive_path}[/red]")
        raise typer.Exit(1)

    store = ChromaStore(config.chroma_path)
    metadata = MetadataStore(config.metadata_path)

    # Determine conflict resolution
    if skip_conflicts:
        resolution = ConflictResolution.SKIP
    elif overwrite:
        resolution = ConflictResolution.OVERWRITE
    else:
        resolution = ConflictResolution.SKIP  # Default

    options = ImportOptions(
        conflict_resolution=resolution,
        dry_run=dry_run,
    )

    engine = ImportEngine(store, metadata)

    # Validate first
    con.print(f"\n[bold]Validating archive: {archive_path}[/bold]\n")

    validation = engine.validate(archive_path)
    if not validation.is_valid:
        con.print(f"[red]Invalid archive: {validation.error}[/red]")
        raise typer.Exit(1)

    con.print(f"[green]✓[/green] Archive valid (v{validation.version})")
    con.print(f"  Documents: {validation.document_count}")
    con.print(f"  Chunks: {validation.chunk_count}")

    if validation.conflicts:
        con.print(f"  [yellow]Conflicts: {len(validation.conflicts)}[/yellow]")
        if skip_conflicts:
            con.print("  [dim]Using --skip-conflicts[/dim]")
        elif overwrite:
            con.print("  [dim]Using --overwrite[/dim]")

    if dry_run:
        con.print("\n[yellow]Dry run - no changes made.[/yellow]")
        return

    # Import
    con.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        console=con,
        transient=False,
    ) as progress:
        task = progress.add_task("Importing...", total=100)

        def progress_callback(current: int, total: int, stage: str) -> None:
            pct = int((current / total) * 100) if total > 0 else 0
            progress.update(task, completed=pct, description=f"[dim]{stage}[/dim]")

        result = engine.import_archive(archive_path, options, progress_callback=progress_callback)
        progress.update(task, completed=100, description="[green]Complete[/green]")

    # Summary
    con.print()
    con.print("[green]✓[/green] Import complete")
    con.print(f"  Documents imported: {result.documents_imported}")
    con.print(f"  Chunks imported: {result.chunks_imported}")
    if result.documents_skipped > 0:
        con.print(f"  Documents skipped: {result.documents_skipped}")


__all__ = [
    "export_command",
    "import_command",
]
