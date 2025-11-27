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
    contextual: bool | None = None,
    late_chunking: bool | None = None,
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

    # Determine contextual retrieval setting
    use_contextual = contextual if contextual is not None else config.retrieval.contextual.enabled
    if use_contextual:
        con.print("[dim]Contextual retrieval enabled (requires Ollama)[/dim]")

    # Determine late chunking setting
    use_late_chunking = late_chunking if late_chunking is not None else config.embedding.late_chunking
    if use_late_chunking:
        con.print("[dim]Late chunking enabled for context-aware embeddings[/dim]")
        # Temporarily override config for this indexing session
        config.embedding.late_chunking = True

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
                contextual=use_contextual,
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
            contextual=use_contextual,
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
    mode: str = "hybrid",
    cite: str = "none",
    no_interactive: bool = False,
    output_format: OutputFormat = "rich",
    no_color: bool = False,
) -> None:
    """Search indexed documents with natural language.

    Returns the most relevant document chunks using hybrid search.
    """
    from ragd.config import load_config
    from ragd.search import hybrid_search, SearchMode
    from ragd.ui import format_search_results
    from ragd.ui.tui import run_search_navigator

    con = get_console(no_color)

    config = load_config()

    # Use config default if min_score not specified
    effective_min_score = (
        min_score if min_score is not None else config.retrieval.min_score
    )

    # Parse search mode
    try:
        search_mode = SearchMode(mode.lower())
    except ValueError:
        con.print(f"[red]Invalid search mode: {mode}[/red]")
        con.print("Valid modes: hybrid, semantic, keyword")
        raise typer.Exit(1)

    # Validate citation style
    valid_cite_styles = ["none", "inline", "apa", "mla", "chicago", "bibtex", "markdown"]
    if cite.lower() not in valid_cite_styles:
        con.print(f"[red]Invalid citation style: {cite}[/red]")
        con.print(f"Valid styles: {', '.join(valid_cite_styles)}")
        raise typer.Exit(1)
    cite_style = cite.lower()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=con,
        transient=True,
    ) as progress:
        if output_format == "rich":
            progress.add_task(f"Searching ({mode})...", total=None)
        hybrid_results = hybrid_search(
            query,
            limit=limit,
            mode=search_mode,
            min_score=effective_min_score,
            config=config,
        )

    # Convert HybridSearchResult to legacy SearchResult format for compatibility
    from ragd.search import SearchResult, SourceLocation

    results = [
        SearchResult(
            content=hr.content,
            score=hr.combined_score,
            document_id=hr.document_id,
            document_name=hr.document_name,
            chunk_index=hr.chunk_index,
            metadata=hr.metadata,
            location=SourceLocation(
                page_number=hr.location.page_number if hr.location else None,
                char_start=hr.location.char_start if hr.location else None,
                char_end=hr.location.char_end if hr.location else None,
            ) if hr.location else None,
        )
        for hr in hybrid_results
    ]

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
            citation_style=cite_style,  # type: ignore
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


def reindex_command(
    document_id: str | None = None,
    all_docs: bool = False,
    file_type: str | None = None,
    force: bool = False,
    verbose: bool = False,
    output_format: OutputFormat = "rich",
    no_color: bool = False,
) -> None:
    """Re-index documents with improved text extraction.

    Re-processes existing documents using the latest text extraction
    and normalisation pipeline (F-051 text quality improvements).
    """
    from ragd.config import load_config
    from ragd.storage import ChromaStore
    from ragd.ingestion import index_document
    from ragd.ingestion.extractor import extract_text
    from ragd.text.normalise import TextNormaliser, source_type_from_file_type

    con = get_console(no_color)

    config = load_config()
    store = ChromaStore(config.chroma_path)

    # Determine which documents to re-index
    if all_docs:
        docs = store.list_documents()
    elif file_type:
        docs = store.list_documents(file_type=file_type)
    elif document_id:
        doc = store.get_document(document_id)
        if doc is None:
            con.print(f"[red]Document not found: {document_id}[/red]")
            raise typer.Exit(1)
        docs = [doc]
    else:
        con.print("[red]Specify --all, --type, or a document ID[/red]")
        raise typer.Exit(1)

    if not docs:
        con.print("[yellow]No documents found matching criteria.[/yellow]")
        raise typer.Exit()

    doc_count = len(docs)

    if not force:
        if not typer.confirm(f"Re-index {doc_count} document{'s' if doc_count != 1 else ''}?"):
            con.print("[yellow]Cancelled.[/yellow]")
            raise typer.Exit()

    con.print(f"\n[bold]Re-indexing {doc_count} document{'s' if doc_count != 1 else ''}...[/bold]\n")

    success_count = 0
    error_count = 0
    normaliser = TextNormaliser()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        console=con,
        transient=False,
    ) as progress:
        task = progress.add_task("Re-indexing...", total=doc_count)

        for i, doc in enumerate(docs):
            try:
                source_path = Path(doc.get("source_path", ""))
                doc_id = doc.get("id", "")
                doc_name = doc.get("name", source_path.name if source_path else "unknown")

                if verbose:
                    progress.update(
                        task,
                        description=f"[dim]{doc_name[:40]}...[/dim]"
                        if len(doc_name) > 40
                        else f"[dim]{doc_name}[/dim]",
                    )

                # Delete old chunks for this document
                store.delete_chunks(doc_id)

                # Re-extract and re-index
                if source_path.exists():
                    # Re-index from source file
                    index_document(source_path, config=config, document_id=doc_id)
                    success_count += 1
                else:
                    # Source file no longer exists - log warning
                    if verbose:
                        con.print(f"[yellow]Source not found: {source_path}[/yellow]")
                    error_count += 1

            except Exception as e:
                if verbose:
                    con.print(f"[red]Error re-indexing {doc_name}: {e}[/red]")
                error_count += 1

            progress.update(task, completed=i + 1)

        progress.update(task, description="[green]Complete[/green]")

    # Summary
    con.print()
    if success_count > 0:
        con.print(f"[green]✓[/green] Re-indexed {success_count} document{'s' if success_count != 1 else ''}")
    if error_count > 0:
        con.print(f"[yellow]![/yellow] {error_count} document{'s' if error_count != 1 else ''} had errors")
