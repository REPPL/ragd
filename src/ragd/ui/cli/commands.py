"""CLI command implementations for ragd.

This module contains the actual command logic extracted from the main CLI module.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    MofNCompleteColumn,
)

from ragd import __version__
from ragd.ui import OutputFormat


def get_console(no_color: bool = False) -> Console:
    """Get console with colour settings.

    Args:
        no_color: Whether to disable colour

    Returns:
        Console instance
    """
    # Check NO_COLOR environment variable
    if os.environ.get("NO_COLOR"):
        no_color = True
    return Console(no_color=no_color)


def init_command(
    no_color: bool = False,
) -> None:
    """Initialise ragd with guided setup.

    Detects hardware capabilities and creates optimal configuration.
    """
    from ragd.config import (
        create_default_config,
        ensure_data_dir,
        save_config,
        config_exists,
    )
    from ragd.hardware import detect_hardware, get_recommendations

    con = get_console(no_color)

    con.print("\n[bold]Welcome to ragd![/bold]")
    con.print("Setting up your local RAG system...\n")

    # Detect hardware
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=con,
    ) as progress:
        task = progress.add_task("Detecting hardware...", total=None)
        hw_info = detect_hardware()
        progress.update(task, completed=True)

    con.print(f"[green]✓[/green] Detected {hw_info.backend.upper()} backend")
    con.print(f"[green]✓[/green] Memory: {hw_info.memory_gb:.1f} GB")
    con.print(f"[green]✓[/green] CPU cores: {hw_info.cpu_cores}")
    con.print(f"[green]✓[/green] Hardware tier: {hw_info.tier.value.upper()}")

    if hw_info.gpu_name:
        con.print(f"[green]✓[/green] GPU: {hw_info.gpu_name}")

    # Get recommendations
    recommendations = get_recommendations(hw_info.tier)
    con.print(f"\n[bold]Recommended settings:[/bold]")
    con.print(f"  • Embedding model: {recommendations['embedding_model']}")
    con.print(f"  • LLM model: {recommendations['llm_model']}")
    con.print(f"  • Chunk size: {recommendations['chunk_size']} tokens")

    # Check if config exists
    if config_exists():
        if not typer.confirm("\nConfiguration already exists. Overwrite?"):
            con.print("[yellow]Keeping existing configuration.[/yellow]")
            raise typer.Exit()

    # Create and save configuration
    config = create_default_config()
    ensure_data_dir(config)
    save_config(config)

    con.print(f"\n[green]✓[/green] Configuration saved to ~/.ragd/config.yaml")
    con.print(f"[green]✓[/green] Data directory created at ~/.ragd/")
    con.print("\n[bold green]ragd is ready![/bold green]")
    con.print("\nNext steps:")
    con.print("  • Index documents: [cyan]ragd index <path>[/cyan]")
    con.print("  • Search: [cyan]ragd search \"your query\"[/cyan]")
    con.print("  • Check health: [cyan]ragd doctor[/cyan]")


def index_command(
    path: Path,
    recursive: bool = True,
    skip_duplicates: bool = True,
    verbose: bool = False,
    output_format: OutputFormat = "rich",
    no_color: bool = False,
) -> None:
    """Index documents from a file or directory.

    Supported formats: PDF, TXT, MD, HTML
    """
    from ragd.config import load_config, ensure_data_dir
    from ragd.ingestion import index_path, discover_files
    from ragd.ui import format_index_results

    con = get_console(no_color)

    if not path.exists():
        con.print(f"[red]Error:[/red] Path not found: {path}")
        raise typer.Exit(1)

    # Load config and ensure directories
    config = load_config()
    ensure_data_dir(config)

    # Discover files first to get total count
    files = discover_files(path, recursive=recursive)
    total_files = len(files)

    if total_files == 0:
        con.print("[yellow]No supported files found to index.[/yellow]")
        raise typer.Exit()

    if output_format == "rich" and not verbose:
        # Progress bar mode (default)
        con.print(
            f"\n[bold]Indexing {total_files} document{'s' if total_files != 1 else ''}...[/bold]\n"
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            console=con,
            transient=False,
        ) as progress:
            task = progress.add_task("Indexing...", total=total_files)

            def progress_callback(current: int, total: int, filename: str) -> None:
                progress.update(
                    task,
                    completed=current,
                    description=f"[dim]{filename[:40]}...[/dim]"
                    if len(filename) > 40
                    else f"[dim]{filename}[/dim]",
                )

            results = index_path(
                path,
                config=config,
                recursive=recursive,
                skip_duplicates=skip_duplicates,
                progress_callback=progress_callback,
            )
            progress.update(
                task, completed=total_files, description="[green]Complete[/green]"
            )
    else:
        # Verbose mode (old behaviour) or non-rich output
        con.print(f"\n[bold]Indexing:[/bold] {path}\n")

        def verbose_callback(current: int, total: int, filename: str) -> None:
            con.print(f"[dim][{current}/{total}][/dim] {filename}")

        results = index_path(
            path,
            config=config,
            recursive=recursive,
            skip_duplicates=skip_duplicates,
            progress_callback=verbose_callback if output_format == "rich" else None,
        )

    # Format output
    output = format_index_results(
        results,
        output_format=output_format,
        console=con,
    )
    if output:
        con.print(output)


def search_command(
    query: str,
    limit: int = 10,
    min_score: float | None = None,
    no_interactive: bool = False,
    output_format: OutputFormat = "rich",
    no_color: bool = False,
) -> None:
    """Search indexed documents with natural language.

    Returns the most relevant document chunks based on semantic similarity.
    """
    from ragd.config import load_config
    from ragd.search import search as do_search
    from ragd.ui import format_search_results
    from ragd.ui.tui import run_search_navigator

    con = get_console(no_color)

    config = load_config()

    # Use config default if min_score not specified
    effective_min_score = (
        min_score if min_score is not None else config.retrieval.min_score
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=con,
        transient=True,
    ) as progress:
        if output_format == "rich":
            progress.add_task("Searching...", total=None)
        results = do_search(
            query,
            limit=limit,
            min_score=effective_min_score,
            config=config,
        )

    # Determine if we should use interactive mode
    # Interactive mode requires: TTY, rich format, not disabled, and results exist
    use_interactive = (
        sys.stdout.isatty()
        and output_format == "rich"
        and not no_interactive
        and results
    )

    if use_interactive:
        run_search_navigator(results, query)
    else:
        output = format_search_results(
            results,
            query=query,
            output_format=output_format,
            console=con,
        )
        if output:
            con.print(output)


def status_command(
    output_format: OutputFormat = "rich",
    no_color: bool = False,
) -> None:
    """Show ragd status and statistics."""
    from ragd.config import load_config, config_exists
    from ragd.storage import ChromaStore
    from ragd.ui import format_status

    con = get_console(no_color)

    if not config_exists():
        con.print("[yellow]ragd is not initialised.[/yellow]")
        con.print("Run [cyan]ragd init[/cyan] to set up.")
        raise typer.Exit()

    config = load_config()
    store = ChromaStore(config.chroma_path)
    stats = store.get_stats()

    config_summary = {
        "embedding_model": config.embedding.model,
        "tier": config.hardware.tier.value,
        "data_dir": str(config.storage.data_dir),
    }

    output = format_status(
        stats,
        config_summary,
        output_format=output_format,
        console=con,
    )
    if output:
        con.print(output)


def doctor_command(
    output_format: OutputFormat = "rich",
    no_color: bool = False,
) -> None:
    """Run health checks on ragd components.

    Validates configuration, storage, embedding model, and dependencies.
    """
    from ragd.config import load_config
    from ragd.health import run_health_checks
    from ragd.ui import format_health_results

    con = get_console(no_color)

    con.print("\n[bold]Running health checks...[/bold]\n")

    config = load_config()
    results = run_health_checks(config)

    output = format_health_results(
        results,
        output_format=output_format,
        console=con,
    )
    if output:
        con.print(output)

    # Exit with error if any check failed
    if any(r.status == "unhealthy" for r in results):
        raise typer.Exit(1)


def config_command(
    show: bool = False,
    path: bool = False,
    no_color: bool = False,
) -> None:
    """Manage ragd configuration."""
    import yaml
    from ragd.config import DEFAULT_CONFIG_PATH, load_config, config_exists

    con = get_console(no_color)

    if path:
        con.print(str(DEFAULT_CONFIG_PATH))
        return

    if show or not (show or path):
        if not config_exists():
            con.print("[yellow]No configuration file found.[/yellow]")
            con.print(f"Expected at: {DEFAULT_CONFIG_PATH}")
            con.print("\nRun [cyan]ragd init[/cyan] to create configuration.")
            raise typer.Exit()

        config_obj = load_config()
        config_dict = config_obj.model_dump()
        # Convert Path objects to strings
        if "storage" in config_dict:
            config_dict["storage"]["data_dir"] = str(config_dict["storage"]["data_dir"])
        # Convert HardwareTier enum to string
        if "hardware" in config_dict and "tier" in config_dict["hardware"]:
            tier = config_dict["hardware"]["tier"]
            if hasattr(tier, "value"):
                config_dict["hardware"]["tier"] = tier.value

        con.print(yaml.safe_dump(config_dict, default_flow_style=False))
