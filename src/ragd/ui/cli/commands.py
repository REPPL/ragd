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
    from ragd.search import hybrid_search, SearchMode
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


def meta_show_command(
    document_id: str,
    output_format: OutputFormat = "rich",
    no_color: bool = False,
) -> None:
    """Show metadata for a document."""
    from ragd.config import load_config
    from ragd.metadata import MetadataStore

    con = get_console(no_color)
    config = load_config()

    store = MetadataStore(config.metadata_path)
    metadata = store.get(document_id)

    if metadata is None:
        con.print(f"[red]Document not found: {document_id}[/red]")
        raise typer.Exit(1)

    if output_format == "json":
        import json
        con.print(json.dumps(metadata.to_dict(), indent=2, default=str))
    else:
        from rich.table import Table

        table = Table(title=f"Metadata: {document_id}", show_header=True)
        table.add_column("Field", style="cyan")
        table.add_column("Value")

        # Dublin Core fields
        if metadata.dc_title:
            table.add_row("Title", metadata.dc_title)
        if metadata.dc_creator:
            table.add_row("Creator", ", ".join(metadata.dc_creator))
        if metadata.dc_subject:
            table.add_row("Subject", ", ".join(metadata.dc_subject))
        if metadata.dc_description:
            table.add_row("Description", metadata.dc_description[:100] + "..." if len(metadata.dc_description) > 100 else metadata.dc_description)
        if metadata.dc_date:
            table.add_row("Date", metadata.dc_date.strftime("%Y-%m-%d"))
        if metadata.dc_type:
            table.add_row("Type", metadata.dc_type)
        if metadata.dc_format:
            table.add_row("Format", metadata.dc_format)
        if metadata.dc_language:
            table.add_row("Language", metadata.dc_language)

        # RAG fields
        table.add_row("", "")  # Separator
        if metadata.ragd_source_path:
            table.add_row("Source", metadata.ragd_source_path)
        if metadata.ragd_chunk_count:
            table.add_row("Chunks", str(metadata.ragd_chunk_count))
        if metadata.ragd_ingestion_date:
            table.add_row("Indexed", metadata.ragd_ingestion_date.strftime("%Y-%m-%d %H:%M"))
        if metadata.ragd_tags:
            table.add_row("Tags", ", ".join(metadata.ragd_tags))
        if metadata.ragd_project:
            table.add_row("Project", metadata.ragd_project)

        con.print(table)


def meta_edit_command(
    document_id: str,
    title: str | None = None,
    creator: str | None = None,
    description: str | None = None,
    doc_type: str | None = None,
    project: str | None = None,
    no_color: bool = False,
) -> None:
    """Edit metadata for a document."""
    from ragd.config import load_config
    from ragd.metadata import MetadataStore

    con = get_console(no_color)
    config = load_config()

    store = MetadataStore(config.metadata_path)
    metadata = store.get(document_id)

    if metadata is None:
        con.print(f"[red]Document not found: {document_id}[/red]")
        raise typer.Exit(1)

    # Track changes
    changes = []

    if title is not None:
        old_val = metadata.dc_title
        store.update(document_id, dc_title=title)
        changes.append(f"Title: '{old_val}' → '{title}'")

    if creator is not None:
        # Split on semicolon for multiple creators
        creators = [c.strip() for c in creator.split(";") if c.strip()]
        old_val = ", ".join(metadata.dc_creator)
        store.update(document_id, dc_creator=creators)
        changes.append(f"Creator: '{old_val}' → '{creator}'")

    if description is not None:
        old_val = metadata.dc_description[:50] + "..." if len(metadata.dc_description) > 50 else metadata.dc_description
        store.update(document_id, dc_description=description)
        changes.append(f"Description: updated")

    if doc_type is not None:
        old_val = metadata.dc_type
        store.update(document_id, dc_type=doc_type)
        changes.append(f"Type: '{old_val}' → '{doc_type}'")

    if project is not None:
        old_val = metadata.ragd_project
        store.update(document_id, ragd_project=project)
        changes.append(f"Project: '{old_val}' → '{project}'")

    if changes:
        con.print(f"[green]✓[/green] Updated metadata for: {document_id}")
        for change in changes:
            con.print(f"  {change}")
    else:
        con.print("[yellow]No changes specified.[/yellow]")


def tag_add_command(
    document_id: str,
    tags: list[str],
    no_color: bool = False,
) -> None:
    """Add tags to a document."""
    from ragd.config import load_config
    from ragd.metadata import MetadataStore, TagManager

    con = get_console(no_color)
    config = load_config()

    store = MetadataStore(config.metadata_path)
    tag_mgr = TagManager(store)

    if not store.exists(document_id):
        con.print(f"[red]Document not found: {document_id}[/red]")
        raise typer.Exit(1)

    if tag_mgr.add(document_id, tags):
        con.print(f"[green]✓[/green] Added tags to: {document_id}")
        for tag in tags:
            con.print(f"  + {tag}")
    else:
        con.print("[red]Failed to add tags.[/red]")
        raise typer.Exit(1)


def tag_remove_command(
    document_id: str,
    tags: list[str],
    no_color: bool = False,
) -> None:
    """Remove tags from a document."""
    from ragd.config import load_config
    from ragd.metadata import MetadataStore, TagManager

    con = get_console(no_color)
    config = load_config()

    store = MetadataStore(config.metadata_path)
    tag_mgr = TagManager(store)

    if not store.exists(document_id):
        con.print(f"[red]Document not found: {document_id}[/red]")
        raise typer.Exit(1)

    if tag_mgr.remove(document_id, tags):
        con.print(f"[green]✓[/green] Removed tags from: {document_id}")
        for tag in tags:
            con.print(f"  - {tag}")
    else:
        con.print("[red]Failed to remove tags.[/red]")
        raise typer.Exit(1)


def tag_list_command(
    document_id: str | None = None,
    show_counts: bool = False,
    output_format: OutputFormat = "rich",
    no_color: bool = False,
) -> None:
    """List tags for a document or all tags in knowledge base."""
    from ragd.config import load_config
    from ragd.metadata import MetadataStore, TagManager

    con = get_console(no_color)
    config = load_config()

    store = MetadataStore(config.metadata_path)
    tag_mgr = TagManager(store)

    if document_id:
        # Show tags for specific document
        tags = tag_mgr.get(document_id)
        if not tags:
            con.print(f"[dim]No tags for: {document_id}[/dim]")
        else:
            con.print(f"Tags for {document_id}:")
            for tag in tags:
                con.print(f"  {tag}")
    else:
        # Show all tags
        if show_counts:
            counts = tag_mgr.tag_counts()
            if not counts:
                con.print("[dim]No tags in knowledge base.[/dim]")
            else:
                from rich.table import Table
                table = Table(title="Tags in Knowledge Base")
                table.add_column("Tag", style="cyan")
                table.add_column("Documents", justify="right")

                for tag, count in sorted(counts.items()):
                    table.add_row(tag, str(count))

                con.print(table)
        else:
            all_tags = tag_mgr.list_all_tags()
            if not all_tags:
                con.print("[dim]No tags in knowledge base.[/dim]")
            else:
                con.print("Tags in knowledge base:")
                for tag in all_tags:
                    con.print(f"  {tag}")


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
    from ragd.config import load_config
    from ragd.storage import ChromaStore
    from ragd.metadata import MetadataStore
    from ragd.archive import ExportEngine, ExportOptions, ArchiveFilters

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
    from ragd.config import load_config
    from ragd.storage import ChromaStore
    from ragd.metadata import MetadataStore
    from ragd.archive import ImportEngine, ImportOptions, ConflictResolution

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
    con.print(f"[green]✓[/green] Import complete")
    con.print(f"  Documents imported: {result.documents_imported}")
    con.print(f"  Chunks imported: {result.chunks_imported}")
    if result.documents_skipped > 0:
        con.print(f"  Documents skipped: {result.documents_skipped}")


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
