"""Core CLI commands for ragd.

This module contains fundamental commands for initialisation, indexing,
searching, and system status.
"""

from __future__ import annotations

import sys
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


def _show_config_diff(
    con: "Console",
    existing: "RagdConfig",
    recommendations: dict,
    llm_model: str,
) -> bool:
    """Display config differences in a table.

    Args:
        con: Rich console instance
        existing: Existing configuration
        recommendations: Recommended settings dict
        llm_model: Recommended LLM model

    Returns:
        True if there are differences, False otherwise
    """
    from rich.table import Table

    table = Table(show_header=True, header_style="bold")
    table.add_column("Setting")
    table.add_column("Current")
    table.add_column("Recommended")

    # Compare key settings
    if existing.embedding.model != recommendations["embedding_model"]:
        table.add_row(
            "Embedding model",
            existing.embedding.model,
            recommendations["embedding_model"],
        )
    if existing.llm.model != llm_model:
        table.add_row("LLM model", existing.llm.model, llm_model)
    if existing.chunking.chunk_size != recommendations["chunk_size"]:
        table.add_row(
            "Chunk size",
            str(existing.chunking.chunk_size),
            str(recommendations["chunk_size"]),
        )

    if table.row_count > 0:
        con.print("\n[bold]Current vs Recommended:[/bold]")
        con.print(table)
        return True
    else:
        con.print("\n[dim]Configuration matches recommended settings.[/dim]")
        return False


def init_command(
    no_color: bool = False,
) -> None:
    """Initialise ragd with guided setup.

    Detects hardware capabilities and creates optimal configuration.
    """
    from ragd.config import (
        config_exists,
        create_default_config,
        ensure_data_dir,
        save_config,
    )
    from ragd.hardware import (
        HardwareTier,
        detect_hardware,
        get_extreme_tier_model,
        get_recommendations,
    )

    con = get_console(no_color)

    # Print header
    from ragd.ui.styles import print_init_header

    con.print()
    print_init_header(con)

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

    # For EXTREME tier, check installed models for dynamic selection
    llm_model = recommendations["llm_model"]
    installed_names: list[str] = []
    if hw_info.tier == HardwareTier.EXTREME:
        try:
            from ragd.llm import ModelRegistry, OllamaClient

            client = OllamaClient()
            registry = ModelRegistry(client)
            installed = registry.list_available(refresh=True)
            installed_names = [m.name for m in installed] if installed else []
            llm_model = get_extreme_tier_model(installed_names)
            if installed_names and llm_model != recommendations["llm_model"]:
                con.print(f"[dim]Found installed extreme-tier model: {llm_model}[/dim]")
        except Exception:
            # Ollama not running or error - use default
            pass

    # Offer interactive model selection if multiple models available
    if len(installed_names) > 1:
        con.print(f"\n[dim]Found {len(installed_names)} installed models[/dim]")
        if typer.confirm("Would you like to select a different LLM model?", default=False):
            import questionary

            # Mark recommended model
            choices = []
            for name in sorted(installed_names):
                label = f"{name} (recommended)" if name == llm_model else name
                choices.append(questionary.Choice(label, value=name))

            from ragd.ui.styles import get_prompt_style

            selected = questionary.select(
                "Select LLM model:",
                choices=choices,
                default=llm_model,
                style=get_prompt_style(),
            ).ask()

            if selected:
                llm_model = selected

    con.print("\n[bold]Recommended settings:[/bold]")
    con.print(f"  • Embedding model: {recommendations['embedding_model']}")
    con.print(f"  • LLM model: {llm_model}")
    con.print(f"  • Chunk size: {recommendations['chunk_size']} tokens")

    # Check if config exists
    if config_exists():
        from ragd.config import load_config

        existing = load_config()
        _show_config_diff(con, existing, recommendations, llm_model)

        if not typer.confirm("\nOverwrite with recommended settings?"):
            con.print("[yellow]Keeping existing configuration.[/yellow]")
            raise typer.Exit()

    # Create and save configuration
    config = create_default_config()

    # Override LLM model with detected model (if different from default)
    if config.llm.model != llm_model:
        config.llm.model = llm_model

    # Detect and store context window from model card or Ollama
    context_detected = False
    try:
        from ragd.models import load_model_card

        card = load_model_card(llm_model, auto_discover=True, interactive=False)
        if card and card.context_length:
            config.chat.context_window = card.context_length
            con.print(f"[dim]Detected context window: {card.context_length:,} tokens[/dim]")
            context_detected = True
    except Exception:
        pass  # Model card not available

    # Fallback: query Ollama directly for context length
    if not context_detected:
        try:
            from ragd.llm import OllamaClient

            client = OllamaClient()
            ctx_length = client.get_context_length(llm_model)
            if ctx_length:
                config.chat.context_window = ctx_length
                con.print(f"[dim]Detected context window: {ctx_length:,} tokens (from Ollama)[/dim]")
        except Exception:
            pass  # Ollama not available, use default

    ensure_data_dir(config)
    save_config(config)

    con.print("\n[green]✓[/green] Configuration saved to ~/.ragd/config.yaml")
    con.print("[green]✓[/green] Data directory created at ~/.ragd/")

    # Download required models and data
    con.print("\n[bold]Downloading required models...[/bold]")

    # Download embedding model
    from ragd.embedding import download_model, is_model_cached

    embedding_model = recommendations["embedding_model"]
    if is_model_cached(embedding_model):
        con.print(f"[green]✓[/green] Embedding model already cached: {embedding_model}")
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=con,
        ) as progress:
            task = progress.add_task(
                f"Downloading embedding model ({embedding_model})...", total=None
            )
            download_model(embedding_model, device=hw_info.backend)
            progress.update(task, completed=True)
        con.print(f"[green]✓[/green] Downloaded embedding model: {embedding_model}")

    # Download NLTK data
    import nltk

    try:
        nltk.data.find("tokenizers/punkt")
        con.print("[green]✓[/green] NLTK tokeniser data already available")
    except LookupError:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=con,
        ) as progress:
            task = progress.add_task("Downloading NLTK tokeniser data...", total=None)
            nltk.download("punkt", quiet=True)
            nltk.download("punkt_tab", quiet=True)
            progress.update(task, completed=True)
        con.print("[green]✓[/green] Downloaded NLTK tokeniser data")

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
    from ragd.config import ensure_data_dir, load_config
    from ragd.ingestion import discover_files, index_path
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
            TextColumn("{task.fields[current_file]}"),
            console=con,
            transient=False,
        ) as progress:
            task = progress.add_task("Indexing...", total=total_files, current_file="")

            def progress_callback(completed: int, total: int, filename: str) -> None:
                # completed = number of files finished, filename = current file (empty when done)
                if filename:
                    truncated = filename[:35] + "..." if len(filename) > 35 else filename
                    file_display = f"[dim]({truncated})[/dim]"
                else:
                    file_display = "[green](done)[/green]"
                progress.update(task, completed=completed, current_file=file_display)

            results = index_path(
                path,
                config=config,
                recursive=recursive,
                skip_duplicates=skip_duplicates,
                progress_callback=progress_callback,
                contextual=use_contextual,
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
    tags: list[str] | None = None,
) -> None:
    """Search indexed documents with natural language.

    Returns the most relevant document chunks using hybrid search
    (semantic + keyword). Supports boolean operators in keyword mode.

    Boolean Operators (--mode keyword):

        AND    Both terms required       "python AND testing"

        OR     Either term matches       "ML OR machine learning"

        NOT    Exclude term              "web NOT Django"

        ()     Group expressions         "(A OR B) AND C"

        ""     Exact phrase              "machine learning"

        *      Prefix match              "mach*"

    Examples:

        ragd search "machine learning"

        ragd search "python AND testing" --mode keyword

        ragd search "(Python OR Java) AND web" --mode keyword
    """
    from ragd.config import load_config
    from ragd.search import SearchMode, hybrid_search
    from ragd.search.query import QueryParseError
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

    # Tag filtering: get allowed document IDs
    allowed_doc_ids: set[str] | None = None
    if tags:
        from ragd.metadata.tags import TagManager
        from ragd.storage.metadata import MetadataStore

        store = MetadataStore(config.data_dir / "metadata.db")
        tag_mgr = TagManager(store)
        matching_ids = tag_mgr.find_by_tags(tags, match_all=True)
        allowed_doc_ids = set(matching_ids)

        if not allowed_doc_ids:
            con.print(f"[yellow]No documents found with tags: {', '.join(tags)}[/yellow]")
            return

    try:
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
    except QueryParseError as e:
        con.print(f"[red]{e.user_message()}[/red]")
        raise typer.Exit(1)

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

    # Filter by tags if specified
    if allowed_doc_ids is not None:
        results = [r for r in results if r.document_id in allowed_doc_ids]

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


def info_command(
    detailed: bool = False,
    output_format: OutputFormat = "rich",
    no_color: bool = False,
) -> None:
    """Show ragd status and statistics.

    In brief mode (default): Quick status overview
    In detailed mode: Comprehensive index statistics
    """
    if detailed:
        stats_command(output_format=output_format, no_color=no_color)
    else:
        status_command(output_format=output_format, no_color=no_color)


def status_command(
    output_format: OutputFormat = "rich",
    no_color: bool = False,
) -> None:
    """Show ragd status and statistics (brief mode)."""
    from ragd.config import config_exists, load_config
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


def stats_command(
    output_format: OutputFormat = "rich",
    no_color: bool = False,
) -> None:
    """Show comprehensive index statistics.

    Displays detailed information about indexed content including
    document counts, file types, storage size, and retrieval health.
    """
    import json
    from collections import Counter
    from datetime import datetime

    from rich.panel import Panel

    from ragd.config import config_exists, load_config
    from ragd.metadata import MetadataStore
    from ragd.storage import ChromaStore

    con = get_console(no_color)

    if not config_exists():
        con.print("[yellow]ragd is not initialised.[/yellow]")
        con.print("Run [cyan]ragd init[/cyan] to set up.")
        raise typer.Exit()

    config = load_config()
    store = ChromaStore(config.chroma_path)
    metadata_store = MetadataStore(config.metadata_path)

    # Get basic stats
    stats = store.get_stats()
    doc_count = stats["document_count"]
    chunk_count = stats["chunk_count"]

    # Get file type breakdown from metadata
    file_types: Counter[str] = Counter()
    indexed_dates: list[datetime] = []

    try:
        all_metadata = metadata_store.query(limit=10000)
        for _, meta in all_metadata:
            # Extract file type from format or source path
            if meta.dc_format:
                file_type = meta.dc_format.split("/")[-1].upper()
            elif meta.ragd_source_path:
                ext = Path(meta.ragd_source_path).suffix.lower()
                file_type = ext[1:].upper() if ext else "UNKNOWN"
            else:
                file_type = "UNKNOWN"
            file_types[file_type] += 1

            if meta.ragd_ingestion_date:
                indexed_dates.append(meta.ragd_ingestion_date)
    except Exception:
        # Metadata store might not exist or be empty
        pass

    # Calculate averages
    avg_chunks = chunk_count / doc_count if doc_count > 0 else 0

    # Get storage size
    storage_mb = None
    index_size = stats.get("index_size_bytes") if isinstance(stats, dict) else getattr(stats, "index_size_bytes", None)
    if index_size:
        storage_mb = index_size / (1024 * 1024)

    # Get date range
    date_range = None
    if indexed_dates:
        min_date = min(indexed_dates)
        max_date = max(indexed_dates)
        date_range = (min_date, max_date)

    # Output
    if output_format == "json":
        data = {
            "documents": {
                "indexed": doc_count,
                "chunks": chunk_count,
                "avg_chunks_per_doc": round(avg_chunks, 1),
            },
            "file_types": dict(file_types.most_common()),
            "storage": {
                "backend": stats.get("backend", "chromadb") if isinstance(stats, dict) else (stats.backend.value if hasattr(stats, 'backend') and stats.backend else "chromadb"),
                "dimension": stats.get("dimension", 384) if isinstance(stats, dict) else getattr(stats, "dimension", 384),
                "size_mb": round(storage_mb, 1) if storage_mb else None,
            },
            "retrieval": {
                "embedding_model": config.embedding.model,
                "late_chunking": config.embedding.late_chunking,
            },
            "date_range": {
                "earliest": date_range[0].isoformat() if date_range else None,
                "latest": date_range[1].isoformat() if date_range else None,
            },
        }
        con.print(json.dumps(data, indent=2))
        return

    # Rich output
    con.print()
    con.print(Panel("[bold]Index Statistics[/bold]", expand=False))
    con.print()

    # Documents section
    con.print("[bold cyan]Documents[/bold cyan]")
    con.print(f"  Indexed: {doc_count:,}")
    con.print(f"  Chunks: {chunk_count:,} (avg {avg_chunks:.1f} per document)")
    if storage_mb:
        con.print(f"  Storage: {storage_mb:.1f} MB")
    con.print()

    # File types section
    if file_types:
        con.print("[bold cyan]Content Analysis[/bold cyan]")
        types_str = ", ".join(f"{t} ({c})" for t, c in file_types.most_common(5))
        con.print(f"  File types: {types_str}")
        if date_range:
            min_date, max_date = date_range
            con.print(f"  Date range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
        con.print()

    # Retrieval health section
    con.print("[bold cyan]Retrieval Health[/bold cyan]")
    con.print(f"  Embedding model: {config.embedding.model}")
    dimension = stats.get("dimension", 384) if isinstance(stats, dict) else getattr(stats, "dimension", 384)
    con.print(f"  Vector dimension: {dimension or 384}")
    con.print(f"  Late chunking: {'enabled' if config.embedding.late_chunking else 'disabled'}")
    last_modified = stats.get("last_modified") if isinstance(stats, dict) else getattr(stats, "last_modified", None)
    if last_modified:
        con.print(f"  Last indexed: {last_modified.strftime('%Y-%m-%d %H:%M')}")
    con.print()

    # Tips section
    if doc_count == 0:
        con.print("[dim]No documents indexed yet.[/dim]")
        con.print("[dim]Run 'ragd index <path>' to add documents.[/dim]")


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

    # Run checks silently, let the formatter display everything
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
    validate: bool = False,
    no_color: bool = False,
) -> None:
    """Manage ragd configuration."""
    import yaml

    from ragd.config import DEFAULT_CONFIG_PATH, config_exists, load_config

    con = get_console(no_color)

    if path:
        con.print(str(DEFAULT_CONFIG_PATH))
        return

    if validate:
        _config_validate(con)
        return

    if show or not (show or path or validate):
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


def _config_validate(con) -> None:
    """Run configuration validation checks."""
    from ragd.config import DEFAULT_CONFIG_PATH, config_exists, load_config
    from ragd.config_validator import (
        ValidationSeverity,
        validate_config,
    )

    if not config_exists():
        con.print("[yellow]No configuration file found.[/yellow]")
        con.print(f"Expected at: {DEFAULT_CONFIG_PATH}")
        con.print("\nRun [cyan]ragd init[/cyan] to create configuration.")
        raise typer.Exit(1)

    config_obj = load_config()
    report = validate_config(config_obj, DEFAULT_CONFIG_PATH)

    # Print banner
    width = 60
    con.print()
    con.print("+" + "-" * (width - 2) + "+")
    con.print("|  Configuration Validation" + " " * (width - 29) + "|")
    con.print("+" + "-" * (width - 2) + "+")
    con.print()

    # Print results
    for result in report.results:
        if result.passed:
            icon = "[green][OK][/green]"
        elif result.severity == ValidationSeverity.ERROR:
            icon = "[red][XX][/red]"
        elif result.severity == ValidationSeverity.WARNING:
            icon = "[yellow][!!][/yellow]"
        else:
            icon = "[dim][--][/dim]"

        con.print(f"  {icon} {result.name:<20} {result.message}")

        if not result.passed and result.suggestion:
            con.print(f"      [dim]-> {result.suggestion}[/dim]")

    # Print summary
    con.print()
    summary_parts = []
    if report.error_count:
        summary_parts.append(f"[red]{report.error_count} error{'s' if report.error_count != 1 else ''}[/red]")
    if report.warning_count:
        summary_parts.append(f"[yellow]{report.warning_count} warning{'s' if report.warning_count != 1 else ''}[/yellow]")
    if report.info_count:
        summary_parts.append(f"[dim]{report.info_count} info[/dim]")

    if not summary_parts:
        con.print("[green]All checks passed![/green]")
    else:
        con.print(" | ".join(summary_parts))

    if report.has_errors:
        raise typer.Exit(1)


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
    from ragd.ingestion import index_document
    from ragd.storage import ChromaStore

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


def list_documents_command(
    tag: str | None = None,
    project: str | None = None,
    limit: int | None = None,
    output_format: OutputFormat = "rich",
    no_color: bool = False,
) -> None:
    """List documents in the knowledge base."""
    from ragd.config import load_config
    from ragd.metadata import MetadataStore

    con = get_console(no_color)
    config = load_config()

    store = MetadataStore(config.metadata_path)

    # Build query params
    tags_filter = [tag] if tag else None
    results = store.query(
        project=project,
        tags=tags_filter,
        limit=limit,
    )

    if not results:
        con.print("[dim]No documents found.[/dim]")
        return

    if output_format == "json":
        import json
        data = [{"id": doc_id, "metadata": meta.to_dict()} for doc_id, meta in results]
        con.print(json.dumps(data, indent=2, default=str))
    else:
        from rich.table import Table

        table = Table(title=f"Documents ({len(results)})")
        table.add_column("#", justify="right", style="dim")
        table.add_column("Document")
        table.add_column("Title")
        table.add_column("Tags")
        table.add_column("Indexed")

        for i, (doc_id, meta) in enumerate(results, 1):
            title = meta.dc_title[:30] + "..." if len(meta.dc_title) > 30 else meta.dc_title or "-"
            tags_str = ", ".join(meta.ragd_tags[:3]) if meta.ragd_tags else "-"
            if len(meta.ragd_tags) > 3:
                tags_str += f" (+{len(meta.ragd_tags) - 3})"
            indexed = meta.ragd_ingestion_date.strftime("%Y-%m-%d") if meta.ragd_ingestion_date else "-"

            table.add_row(str(i), doc_id[:20], title, tags_str, indexed)

        con.print(table)


__all__ = [
    "init_command",
    "index_command",
    "search_command",
    "info_command",
    "status_command",
    "stats_command",
    "doctor_command",
    "config_command",
    "reindex_command",
    "list_documents_command",
]
