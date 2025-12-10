"""CLI interface for ragd using Typer.

This module provides the command-line interface for ragd, including commands
for initialisation, indexing, searching, and system status.

Command implementations are in ragd.ui.cli.commands.
"""

from __future__ import annotations

import difflib
import os
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from ragd import __version__


def is_admin_mode() -> bool:
    """Check if admin mode is requested via flag or environment.

    Admin mode shows additional commands for advanced users.
    Can be enabled via:
    - --admin flag: ragd --admin --help
    - RAGD_ADMIN environment variable: RAGD_ADMIN=1 ragd --help
    """
    if os.environ.get("RAGD_ADMIN", "").lower() in ("1", "true", "yes"):
        return True
    return "--admin" in sys.argv


ADMIN_MODE = is_admin_mode()
from ragd.ui.cli import (
    get_console,
    init_command,
    index_command,
    search_command,
    info_command,
    doctor_command,
    config_command,
    reindex_command,
    meta_show_command,
    meta_edit_command,
    tag_add_command,
    tag_remove_command,
    tag_list_command,
    list_documents_command,
    export_command,
    import_command,
    watch_start_command,
    watch_stop_command,
    watch_status_command,
    ask_command,
    chat_command,
    models_list_command,
    models_recommend_command,
    models_show_command,
    models_set_command,
    evaluate_command,
    quality_command,
    # Backend commands
    backend_show_command,
    backend_list_command,
    backend_health_command,
    backend_set_command,
    backend_benchmark_command,
    # Security commands
    unlock_command,
    lock_command,
    password_change_command,
    password_reset_command,
    session_status_command,
    # Deletion commands
    delete_command,
    delete_audit_command,
    # Tier commands
    tier_set_command,
    tier_show_command,
    tier_list_command,
    tier_summary_command,
    tier_promote_command,
    tier_demote_command,
    # Collection commands
    collection_create_command,
    collection_list_command,
    collection_show_command,
    collection_update_command,
    collection_delete_command,
    collection_export_command,
    # Suggestion commands
    suggestions_show_command,
    suggestions_pending_command,
    suggestions_confirm_command,
    suggestions_reject_command,
    suggestions_stats_command,
    # Library commands
    library_show_command,
    library_create_command,
    library_add_command,
    library_remove_command,
    library_rename_command,
    library_delete_command,
    library_hide_command,
    library_validate_command,
    library_promote_command,
    library_pending_command,
    library_stats_command,
    # Config wizard
    run_config_wizard,
    # Config debugging
    show_effective_config,
    show_config_diff,
    show_config_source,
    validate_config,
    # Config migration
    migrate_config,
    rollback_config,
    needs_migration,
    # Help system
    show_extended_help,
    show_examples,
    list_help_topics,
    # Audit commands
    audit_list_command,
    audit_show_command,
    audit_clear_command,
    audit_stats_command,
)

app = typer.Typer(
    name="ragd",
    help="Your Private Intelligent Document Assistant.",
    no_args_is_help=True,
)
console = Console()

# Subcommand groups
# User groups (always visible)
meta_app = typer.Typer(help="Manage document metadata.")
tag_app = typer.Typer(help="Manage document tags.")
collection_app = typer.Typer(help="Manage smart collections.")

# Admin groups (hidden unless ADMIN_MODE)
tier_app = typer.Typer(help="Manage data sensitivity tiers.")
library_app = typer.Typer(help="Manage tag library.")
watch_app = typer.Typer(help="Watch folders for automatic indexing.")
models_app = typer.Typer(help="Manage LLM models.")
backend_app = typer.Typer(help="Manage vector store backends.")
password_app = typer.Typer(help="Manage encryption password.")
session_app = typer.Typer(help="Manage encryption session.")
audit_app = typer.Typer(help="View operation audit log.")

# Register user subcommand groups (always visible)
app.add_typer(collection_app, name="collection", rich_help_panel="Organisation")
app.add_typer(meta_app, name="meta", rich_help_panel="Organisation")
app.add_typer(tag_app, name="tag", rich_help_panel="Organisation")

# Register admin subcommand groups (hidden unless ADMIN_MODE)
app.add_typer(
    library_app, name="library",
    hidden=not ADMIN_MODE,
    rich_help_panel="Administration" if ADMIN_MODE else None,
)
app.add_typer(
    tier_app, name="tier",
    hidden=not ADMIN_MODE,
    rich_help_panel="Administration" if ADMIN_MODE else None,
)
app.add_typer(
    backend_app, name="backend",
    hidden=not ADMIN_MODE,
    rich_help_panel="Infrastructure" if ADMIN_MODE else None,
)
app.add_typer(
    models_app, name="models",
    hidden=not ADMIN_MODE,
    rich_help_panel="Infrastructure" if ADMIN_MODE else None,
)
app.add_typer(
    password_app, name="password",
    hidden=not ADMIN_MODE,
    rich_help_panel="Security" if ADMIN_MODE else None,
)
app.add_typer(
    session_app, name="session",
    hidden=not ADMIN_MODE,
    rich_help_panel="Security" if ADMIN_MODE else None,
)
app.add_typer(
    watch_app, name="watch",
    hidden=not ADMIN_MODE,
    rich_help_panel="Automation" if ADMIN_MODE else None,
)
app.add_typer(
    audit_app, name="audit",
    hidden=not ADMIN_MODE,
    rich_help_panel="Maintenance" if ADMIN_MODE else None,
)


# Output format option
FormatOption = Annotated[
    str,
    typer.Option(
        "--format",
        "-f",
        help="Output format: rich, plain, or json.",
    ),
]


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"ragd version {__version__}")
        raise typer.Exit()


# All available commands for fuzzy matching
ALL_COMMANDS = [
    # Top-level commands
    "init", "index", "search", "info", "doctor", "config", "reindex",
    "list", "export", "import", "ask", "chat", "evaluate", "quality",
    "unlock", "lock", "help", "delete",
    # Subcommand groups
    "meta", "tag", "tier", "collection", "library", "watch", "models",
    "backend", "password", "session", "audit",
]


def suggest_command(unknown: str) -> list[str]:
    """Find similar commands using fuzzy matching."""
    return difflib.get_close_matches(unknown, ALL_COMMANDS, n=3, cutoff=0.6)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
    admin: bool = typer.Option(
        False,
        "--admin",
        help="Show administration commands.",
        is_eager=True,
        hidden=True,  # Don't clutter basic help
    ),
) -> None:
    """Your Private Intelligent Document Assistant.

    Use --admin to see administration commands.
    """
    # Handle unknown commands with fuzzy suggestions
    if ctx.invoked_subcommand is None and len(sys.argv) > 1:
        arg = sys.argv[1]
        # Skip if it's a flag
        if not arg.startswith("-"):
            suggestions = suggest_command(arg)
            if suggestions:
                if len(suggestions) == 1:
                    console.print(f"[red]Unknown command: '{arg}'. Did you mean '{suggestions[0]}'?[/red]")
                else:
                    options = ", ".join(f"'{s}'" for s in suggestions)
                    console.print(f"[red]Unknown command: '{arg}'. Did you mean one of: {options}?[/red]")
            else:
                console.print(f"[red]Unknown command: '{arg}'[/red]")
            console.print("\nRun [cyan]ragd --help[/cyan] for available commands.")
            raise typer.Exit(1)


@app.command(rich_help_panel="Setup & Help")
def init(
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Initialise ragd with guided setup.

    Detects hardware capabilities and creates optimal configuration.
    """
    init_command(no_color=no_color)


@app.command(rich_help_panel="Document Management")
def index(
    path: Annotated[Path, typer.Argument(help="File or directory to index.")],
    recursive: bool = typer.Option(
        True, "--recursive/--no-recursive", "-r", help="Search directories recursively."
    ),
    skip_duplicates: bool = typer.Option(
        True, "--skip-duplicates/--no-skip-duplicates", help="Skip already-indexed documents."
    ),
    contextual: bool = typer.Option(
        None, "--contextual/--no-contextual", "-c",
        help="Enable contextual retrieval (requires Ollama). Uses config if not specified."
    ),
    late_chunking: bool = typer.Option(
        None, "--late-chunking/--no-late-chunking", "-l",
        help="Enable late chunking for context-aware embeddings. Uses config if not specified."
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-V", help="Show per-file progress instead of progress bar."
    ),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Index documents from a file or directory.

    Supported formats: PDF, TXT, MD, HTML

    Contextual retrieval generates AI-powered context for each chunk,
    improving search accuracy. Requires Ollama to be running locally.

    Late chunking embeds chunks with full document context, improving
    embedding quality for retrieval.
    """
    index_command(
        path=path,
        recursive=recursive,
        skip_duplicates=skip_duplicates,
        contextual=contextual,
        late_chunking=late_chunking,
        verbose=verbose,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


SearchModeOption = Annotated[
    str,
    typer.Option(
        "--mode",
        "-m",
        help="Search mode: hybrid (default), semantic, or keyword.",
    ),
]

CitationOption = Annotated[
    str,
    typer.Option(
        "--cite",
        help="Citation style: none, inline, apa, mla, chicago, bibtex, markdown.",
    ),
]


@app.command(rich_help_panel="Core Commands")
def search(
    query: Annotated[str, typer.Argument(help="Search query.")],
    limit: int = typer.Option(10, "--limit", "-n", help="Maximum number of results."),
    min_score: float = typer.Option(
        None, "--min-score", help="Minimum similarity score (0-1). Default: 0.3"
    ),
    mode: SearchModeOption = "hybrid",
    cite: CitationOption = "none",
    no_interactive: bool = typer.Option(
        False, "--no-interactive", help="Disable interactive navigator, print results directly."
    ),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
    tag: list[str] = typer.Option(
        [], "--tag", "-t", help="Filter by tag. Can be repeated for multiple tags."
    ),
) -> None:
    """Search indexed documents with natural language.

    Returns the most relevant document chunks using hybrid search (semantic + keyword).
    By default, opens an interactive navigator to browse results (use j/k or arrows to navigate, q to quit).

    Search modes:
      - hybrid: Combines semantic and keyword search (default)
      - semantic: Pure vector similarity search
      - keyword: Pure BM25 keyword search

    Citation styles:
      - none: No citations (default)
      - inline: Simple (filename, p. X) format
      - apa: APA 7th edition
      - mla: MLA 9th edition
      - chicago: Chicago notes-bibliography
      - bibtex: BibTeX for LaTeX
      - markdown: Markdown link format

    Tag filtering:
      Use --tag to filter results to documents with specific tags.
      Multiple --tag options require ALL tags to match.
    """
    search_command(
        query=query,
        limit=limit,
        min_score=min_score,
        mode=mode,
        cite=cite,
        no_interactive=no_interactive,
        output_format=output_format,  # type: ignore
        no_color=no_color,
        tags=tag if tag else None,
    )


@app.command(rich_help_panel="Setup & Help")
def info(
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show comprehensive statistics."),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Show ragd status and statistics.

    By default shows a quick status overview. Use --detailed for
    comprehensive index statistics.

    Examples:
        ragd info             # Quick status
        ragd info --detailed  # Full statistics
        ragd info -d          # Short form
    """
    info_command(
        detailed=detailed,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@app.command(
    hidden=not ADMIN_MODE,
    rich_help_panel="Administration" if ADMIN_MODE else None,
)
def doctor(
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Run health checks on ragd components.

    Validates configuration, storage, embedding model, and dependencies.
    """
    doctor_command(
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@app.command(
    hidden=not ADMIN_MODE,
    rich_help_panel="Administration" if ADMIN_MODE else None,
)
def config(
    show: bool = typer.Option(False, "--show", "-s", help="Show current configuration."),
    path: bool = typer.Option(False, "--path", "-p", help="Show configuration file path."),
    validate: bool = typer.Option(
        False, "--validate", "-v", help="Validate configuration and detect issues."
    ),
    effective: bool = typer.Option(False, "--effective", "-e", help="Show effective config with defaults."),
    diff: bool = typer.Option(False, "--diff", "-d", help="Show only non-default values."),
    source: bool = typer.Option(False, "--source", help="Show config value sources."),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive configuration wizard."),
    migrate: bool = typer.Option(False, "--migrate", help="Migrate config to current version."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show migration changes without applying."),
    rollback: bool = typer.Option(False, "--rollback", help="Rollback to previous config backup."),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Manage ragd configuration.

    Configuration options:
        --show           Show current configuration
        --effective      Show config with all defaults
        --diff           Show only changed values
        --source         Show where values come from
        --interactive    Launch configuration wizard
        --migrate        Migrate to current schema version
        --rollback       Restore from backup

    Examples:
        ragd config --show                 # Show config
        ragd config --effective            # Show with defaults
        ragd config --diff                 # Show customisations
        ragd config --interactive          # Wizard mode
        ragd config --migrate --dry-run    # Preview migration
    """
    con = get_console(no_color)

    if interactive:
        run_config_wizard(con)
    elif effective:
        show_effective_config(con, format=output_format)
    elif diff:
        show_config_diff(con, format=output_format)
    elif source:
        show_config_source(con)
    elif migrate:
        migrate_config(dry_run=dry_run, console=con)
    elif rollback:
        rollback_config(console=con)
    elif validate:
        validate_config(con)
    else:
        config_command(
            show=show,
            path=path,
            validate=validate,
            no_color=no_color,
        )


@app.command(rich_help_panel="Document Management")
def reindex(
    document_id: Annotated[
        str | None, typer.Argument(help="Specific document ID to re-index.")
    ] = None,
    all_docs: bool = typer.Option(False, "--all", "-a", help="Re-index all documents."),
    file_type: str = typer.Option(None, "--type", "-t", help="Re-index by file type (pdf, html)."),
    force: bool = typer.Option(False, "--force", "-F", help="Skip confirmation prompt."),
    verbose: bool = typer.Option(False, "--verbose", "-V", help="Show per-file progress."),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Re-index documents with improved text extraction.

    Use this command after upgrading ragd to apply the latest text
    quality improvements to existing documents.

    Examples:
        ragd reindex --all              # Re-index all documents
        ragd reindex --type pdf         # Re-index only PDFs
        ragd reindex doc-123            # Re-index specific document
        ragd reindex --all --force      # Re-index without confirmation
    """
    reindex_command(
        document_id=document_id,
        all_docs=all_docs,
        file_type=file_type,
        force=force,
        verbose=verbose,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


# --- Metadata subcommands ---

@meta_app.command("show")
def meta_show(
    document_id: Annotated[str, typer.Argument(help="Document ID to show metadata for.")],
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Show metadata for a document.

    Displays Dublin Core metadata and RAG-specific fields.
    """
    meta_show_command(
        document_id=document_id,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@meta_app.command("edit")
def meta_edit(
    document_id: Annotated[str, typer.Argument(help="Document ID to edit.")],
    title: str = typer.Option(None, "--title", help="Set document title."),
    creator: str = typer.Option(None, "--creator", help="Set creator(s), semicolon-separated."),
    description: str = typer.Option(None, "--description", help="Set description."),
    doc_type: str = typer.Option(None, "--type", help="Set document type."),
    project: str = typer.Option(None, "--project", help="Set project name."),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Edit metadata for a document.

    Update specific metadata fields. Use semicolons to separate multiple creators.

    Examples:
        ragd meta edit doc-123 --title "My Document"
        ragd meta edit doc-123 --creator "Smith, J.; Doe, J."
        ragd meta edit doc-123 --project "Research"
    """
    meta_edit_command(
        document_id=document_id,
        title=title,
        creator=creator,
        description=description,
        doc_type=doc_type,
        project=project,
        no_color=no_color,
    )


# --- Tag subcommands ---

@tag_app.command("add")
def tag_add(
    document_id: Annotated[str, typer.Argument(help="Document ID to tag.")],
    tags: Annotated[list[str], typer.Argument(help="Tags to add.")],
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Add tags to a document.

    Examples:
        ragd tag add doc-123 important
        ragd tag add doc-123 "topic:ml" "status:reading"
    """
    tag_add_command(
        document_id=document_id,
        tags=tags,
        no_color=no_color,
    )


@tag_app.command("remove")
def tag_remove(
    document_id: Annotated[str, typer.Argument(help="Document ID to untag.")],
    tags: Annotated[list[str], typer.Argument(help="Tags to remove.")],
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Remove tags from a document.

    Examples:
        ragd tag remove doc-123 draft
    """
    tag_remove_command(
        document_id=document_id,
        tags=tags,
        no_color=no_color,
    )


@tag_app.command("list")
def tag_list(
    document_id: Annotated[str | None, typer.Argument(help="Document ID (optional).")] = None,
    show_counts: bool = typer.Option(False, "--counts", "-c", help="Show document counts per tag."),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """List tags.

    Without a document ID, lists all tags in the knowledge base.
    With a document ID, lists tags for that document.

    Examples:
        ragd tag list              # All tags
        ragd tag list --counts     # Tags with document counts
        ragd tag list doc-123      # Tags for specific document
    """
    tag_list_command(
        document_id=document_id,
        show_counts=show_counts,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


# --- Tier subcommands ---

@tier_app.command("set")
def tier_set(
    document_id: Annotated[str, typer.Argument(help="Document ID to update.")],
    tier: Annotated[str, typer.Argument(help="Tier: public, personal, sensitive, critical.")],
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Set the sensitivity tier for a document.

    Tiers control access requirements:
      - public: Always accessible
      - personal: Default, requires basic auth
      - sensitive: Requires active session
      - critical: Requires session + confirmation

    Examples:
        ragd tier set doc-123 sensitive
        ragd tier set doc-456 critical
    """
    tier_set_command(
        document_id=document_id,
        tier=tier,
        no_color=no_color,
    )


@tier_app.command("show")
def tier_show(
    document_id: Annotated[str, typer.Argument(help="Document ID to query.")],
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Show the sensitivity tier for a document.

    Examples:
        ragd tier show doc-123
    """
    tier_show_command(
        document_id=document_id,
        no_color=no_color,
    )


@tier_app.command("list")
def tier_list(
    tier: Annotated[str | None, typer.Argument(help="Filter by tier (optional).")] = None,
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """List documents by tier.

    Without a tier argument, shows counts for all tiers.
    With a tier argument, lists documents in that tier.

    Examples:
        ragd tier list              # Show tier counts
        ragd tier list sensitive    # List sensitive documents
    """
    tier_list_command(
        tier=tier,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@tier_app.command("summary")
def tier_summary(
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Show tier distribution summary.

    Displays a visual breakdown of document counts per tier.

    Examples:
        ragd tier summary
        ragd tier summary --format json
    """
    tier_summary_command(
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@tier_app.command("promote")
def tier_promote(
    document_id: Annotated[str, typer.Argument(help="Document ID to promote.")],
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Increase document sensitivity by one level.

    Examples:
        ragd tier promote doc-123  # personal -> sensitive
    """
    tier_promote_command(
        document_id=document_id,
        no_color=no_color,
    )


@tier_app.command("demote")
def tier_demote(
    document_id: Annotated[str, typer.Argument(help="Document ID to demote.")],
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Decrease document sensitivity by one level.

    Examples:
        ragd tier demote doc-123  # sensitive -> personal
    """
    tier_demote_command(
        document_id=document_id,
        no_color=no_color,
    )


# --- List command ---

@app.command("list", rich_help_panel="Document Management")
def list_docs(
    tag: str = typer.Option(None, "--tag", "-t", help="Filter by tag."),
    project: str = typer.Option(None, "--project", "-p", help="Filter by project."),
    limit: int = typer.Option(None, "--limit", "-n", help="Maximum results."),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """List documents in the knowledge base.

    Filter documents by tag, project, or other criteria.

    Examples:
        ragd list                     # All documents
        ragd list --tag important     # Documents with tag
        ragd list --project Research  # Documents in project
        ragd list -n 10               # First 10 documents
    """
    list_documents_command(
        tag=tag,
        project=project,
        limit=limit,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


# --- Export/Import commands ---

@app.command("export", rich_help_panel="Knowledge Base")
def export_archive(
    output_path: Annotated[Path, typer.Argument(help="Path for output archive (.tar.gz).")],
    no_embeddings: bool = typer.Option(False, "--no-embeddings", help="Exclude embeddings (smaller archive)."),
    tag: str = typer.Option(None, "--tag", "-t", help="Only export documents with tag."),
    project: str = typer.Option(None, "--project", "-p", help="Only export documents in project."),
    verbose: bool = typer.Option(False, "--verbose", "-V", help="Show detailed progress."),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Export knowledge base to an archive.

    Creates a portable tar.gz archive containing documents, chunks,
    embeddings, and metadata.

    Examples:
        ragd export ~/backup.tar.gz              # Full export
        ragd export ~/backup.tar.gz --no-embeddings  # Smaller archive
        ragd export ~/ml.tar.gz --tag "topic:ml"     # Export by tag
    """
    export_command(
        output_path=output_path,
        no_embeddings=no_embeddings,
        tag=tag,
        project=project,
        verbose=verbose,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@app.command("import", rich_help_panel="Knowledge Base")
def import_archive_cmd(
    archive_path: Annotated[Path, typer.Argument(help="Path to archive (.tar.gz).")],
    skip_conflicts: bool = typer.Option(False, "--skip-conflicts", help="Skip documents that already exist."),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing documents."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate without importing."),
    verbose: bool = typer.Option(False, "--verbose", "-V", help="Show detailed progress."),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Import knowledge base from an archive.

    Restores documents, chunks, embeddings, and metadata from
    a portable tar.gz archive.

    Examples:
        ragd import ~/backup.tar.gz               # Import with default settings
        ragd import ~/backup.tar.gz --dry-run     # Validate only
        ragd import ~/backup.tar.gz --overwrite   # Replace existing documents
    """
    import_command(
        archive_path=archive_path,
        skip_conflicts=skip_conflicts,
        overwrite=overwrite,
        dry_run=dry_run,
        verbose=verbose,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


# --- Watch subcommands ---

@watch_app.command("start")
def watch_start(
    directories: Annotated[list[Path], typer.Argument(help="Directories to watch.")],
    patterns: list[str] = typer.Option(
        None, "--pattern", "-p", help="File patterns to watch (e.g., '*.pdf')."
    ),
    recursive: bool = typer.Option(
        True, "--recursive/--no-recursive", "-r", help="Watch subdirectories."
    ),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Start watching folders for automatic indexing.

    Monitors specified directories for new or modified files and
    automatically indexes them.

    Examples:
        ragd watch start ~/Documents
        ragd watch start ~/PDFs ~/Notes --pattern "*.pdf"
        ragd watch start ~/Research --no-recursive
    """
    watch_start_command(
        directories=directories,
        patterns=patterns,
        recursive=recursive,
        no_color=no_color,
    )


@watch_app.command("stop")
def watch_stop(
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Stop the folder watcher.

    Stops the background watcher process if running.
    """
    watch_stop_command(no_color=no_color)


@watch_app.command("status")
def watch_status_cmd(
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Show watcher status.

    Displays whether the watcher is running and which folders are being monitored.
    """
    watch_status_command(
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


# --- Models subcommands ---

@models_app.command("list")
def models_list(
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """List available LLM models.

    Shows all models downloaded in Ollama and current configuration.
    """
    models_list_command(
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@models_app.command("recommend")
def models_recommend(
    use_case: Annotated[
        str | None, typer.Option("--use-case", "-u", help="Use case (quick_qa, research, coding, etc.).")
    ] = None,
    model_type: str = typer.Option("llm", "--type", "-t", help="Model type (llm, embedding)."),
    all_models: bool = typer.Option(False, "--all", "-a", help="Include non-installed models."),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Recommend models based on your hardware.

    Analyses your hardware capabilities and recommends optimal models
    for your use case.

    Use cases:
      - quick_qa: Fast Q&A, low latency
      - research: In-depth analysis, quality priority
      - coding: Code-related queries
      - summarisation: Document summarisation
      - multilingual: Non-English documents
      - agentic: CRAG/Self-RAG evaluation
      - embedding: Document embedding
      - contextual: Contextual retrieval

    Examples:
        ragd models recommend
        ragd models recommend --use-case research
        ragd models recommend --type embedding
        ragd models recommend --all  # Include non-installed models
    """
    models_recommend_command(
        use_case=use_case,
        model_type=model_type,
        require_installed=not all_models,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@models_app.command("show")
def models_show(
    model_id: Annotated[str, typer.Argument(help="Model ID to show details for.")],
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Show model card details.

    Displays detailed information about a model including capabilities,
    hardware requirements, strengths, weaknesses, and limitations.

    Examples:
        ragd models show llama3.2:3b
        ragd models show nomic-embed-text
        ragd models show qwen2.5:7b --format json
    """
    models_show_command(
        model_id=model_id,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@models_app.command("set")
def models_set(
    chat: str = typer.Option(None, "--chat", help="Set chat/generation model."),
    summary: str = typer.Option(None, "--summary", help="Set summary model."),
    classification: str = typer.Option(None, "--classification", help="Set classification model."),
    embedding: str = typer.Option(None, "--embedding", help="Set embedding model."),
    contextual: str = typer.Option(None, "--contextual", help="Set contextual retrieval model."),
    no_validate: bool = typer.Option(False, "--no-validate", help="Skip Ollama validation."),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Set models for specific purposes.

    Configures which model to use for each RAG function.
    Models are validated against Ollama before setting.

    Purposes:
      --chat          Main chat/generation model (ragd ask, ragd chat)
      --summary       Document summary generation
      --classification Document type classification
      --embedding     Vector embedding model (local, not Ollama)
      --contextual    Contextual retrieval augmentation

    Examples:
        ragd models set --chat llama3.1:8b
        ragd models set --summary llama3.2:3b --classification llama3.2:3b
        ragd models set --embedding nomic-embed-text
    """
    models_set_command(
        chat=chat,
        summary=summary,
        classification=classification,
        embedding=embedding,
        contextual=contextual,
        no_validate=no_validate,
        no_color=no_color,
    )


@models_app.command("discover")
def models_discover(
    model_id: Annotated[str, typer.Argument(help="Model ID to discover (e.g., 'llama3.2:3b').")],
    no_interactive: bool = typer.Option(False, "--no-interactive", help="Skip interactive confirmation."),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing card."),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Discover and create a model card.

    Fetches metadata from available sources (Ollama API, HuggingFace Hub,
    heuristics) and creates a model card. By default, prompts for
    confirmation before saving.

    Sources (in priority order):
      1. Ollama API (local installation)
      2. HuggingFace Hub (if internet available)
      3. Heuristics (name pattern inference, always available)

    Examples:
        ragd models discover llama3.2:3b
        ragd models discover qwen2.5:14b --no-interactive
        ragd models discover mistral:7b --force
    """
    from ragd.ui.cli import models_discover_command

    models_discover_command(
        model_id=model_id,
        interactive=not no_interactive,
        force=force,
        no_color=no_color,
    )


@models_app.command("cards")
def models_cards(
    show_all: bool = typer.Option(False, "--all", "-a", help="Include cached (auto-discovered) cards."),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """List all available model cards.

    Shows bundled and user-confirmed cards by default. Use --all to also
    include cached (auto-discovered) cards that haven't been confirmed.

    Card sources:
      - Bundled: Shipped with ragd
      - User: Confirmed and saved by user
      - Cached: Auto-discovered but not yet confirmed

    Examples:
        ragd models cards
        ragd models cards --all
        ragd models cards --format json
    """
    from ragd.ui.cli import models_cards_command

    models_cards_command(
        show_all=show_all,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@models_app.command("card-edit")
def models_card_edit(
    model_id: Annotated[str, typer.Argument(help="Model ID to edit.")],
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Edit an existing model card.

    Opens an interactive editor for modifying model card fields.
    Changes are saved to user storage (~/.ragd/model_cards/).

    Examples:
        ragd models card-edit llama3.2:3b
        ragd models card-edit qwen2.5:7b
    """
    from ragd.ui.cli import models_card_edit_command

    models_card_edit_command(
        model_id=model_id,
        no_color=no_color,
    )


# --- Ask/Chat commands ---

@app.command(rich_help_panel="Core Commands")
def ask(
    question: Annotated[str, typer.Argument(help="Question to ask.")],
    model: str = typer.Option(None, "--model", "-m", help="LLM model to use (default: from config)."),
    temperature: float = typer.Option(0.7, "--temperature", "-t", help="Sampling temperature (0.0-1.0)."),
    limit: int = typer.Option(5, "--limit", "-n", help="Maximum search results for context."),
    min_relevance: float = typer.Option(None, "--min-relevance", "-r", help="Minimum relevance score (0.0-1.0, default: from config)."),
    no_stream: bool = typer.Option(False, "--no-stream", help="Disable streaming output."),
    agentic: bool = typer.Option(None, "--agentic/--no-agentic", help="Enable/disable agentic RAG (CRAG + Self-RAG)."),
    show_confidence: bool = typer.Option(False, "--show-confidence", "-c", help="Show confidence score."),
    cite: str = typer.Option("numbered", "--cite", help="Citation style: none, numbered, inline."),
    verbose: bool = typer.Option(False, "--verbose", "-V", help="Show detailed progress."),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Ask a question using your knowledge base.

    Retrieves relevant documents and generates an answer using Ollama LLM.
    Requires Ollama to be running locally.

    Agentic mode (--agentic) enables:
    - CRAG: Evaluates retrieval quality and rewrites queries if needed
    - Self-RAG: Assesses response faithfulness and refines if needed

    Examples:
        ragd ask "What authentication methods are recommended?"
        ragd ask "Summarise the security policy" --model llama3.2:8b
        ragd ask "Compare the approaches" --agentic --show-confidence
    """
    ask_command(
        question=question,
        model=model,
        temperature=temperature,
        limit=limit,
        min_relevance=min_relevance,
        stream=not no_stream,
        agentic=agentic,
        show_confidence=show_confidence,
        cite=cite,
        verbose=verbose,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@app.command(rich_help_panel="Core Commands")
def chat(
    model: str = typer.Option(None, "--model", "-m", help="LLM model to use (default: from config)."),
    temperature: float = typer.Option(0.7, "--temperature", "-t", help="Sampling temperature (0.0-1.0)."),
    limit: int = typer.Option(5, "--limit", "-n", help="Maximum search results per query."),
    min_relevance: float = typer.Option(None, "--min-relevance", "-r", help="Minimum relevance score (0.0-1.0, default: from config)."),
    session_id: str = typer.Option(None, "--session", "-s", help="Resume a previous chat session."),
    cite: str = typer.Option(None, "--cite", "-c", help="Citation style: none, numbered (default from config)."),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Start an interactive chat with your knowledge base.

    Multi-turn conversation with RAG-powered responses. Each question
    retrieves relevant context from your documents.

    Requires Ollama to be running locally.

    Chat commands:
        /exit, /quit, /q  - Exit chat
        /clear            - Clear conversation history
        /history          - Show conversation history
        /help             - Show available commands

    Examples:
        ragd chat
        ragd chat --model llama3.2:8b
        ragd chat --cite none  # Disable citations
        ragd chat --session abc123  # Resume previous session
    """
    chat_command(
        model=model,
        temperature=temperature,
        limit=limit,
        min_relevance=min_relevance,
        session_id=session_id,
        cite=cite,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@app.command(
    hidden=not ADMIN_MODE,
    rich_help_panel="Maintenance" if ADMIN_MODE else None,
)
def evaluate(
    query: Annotated[str | None, typer.Option("--query", "-q", help="Single query to evaluate.")] = None,
    test_file: Annotated[Path | None, typer.Option("--test-file", "-t", help="YAML/JSON file with test queries.")] = None,
    expected: str = typer.Option(None, "--expected", "-e", help="Expected answer for recall computation."),
    limit: int = typer.Option(5, "--limit", "-n", help="Maximum search results."),
    threshold: float = typer.Option(0.5, "--threshold", help="Relevance threshold (0-1)."),
    include_llm: bool = typer.Option(
        False, "--include-llm", help="Include LLM-based metrics (faithfulness, answer_relevancy)."
    ),
    no_save: bool = typer.Option(False, "--no-save", help="Don't save evaluation results."),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Evaluate RAG retrieval quality.

    Computes metrics for your RAG system:
    - Context Precision: Are retrieved docs relevant?
    - Relevance Score: Weighted relevance with position decay

    With --include-llm (requires Ollama):
    - Faithfulness: Is the answer grounded in context?
    - Answer Relevancy: Does the answer address the question?

    Single query:
        ragd evaluate --query "What is machine learning?"

    With expected answer:
        ragd evaluate --query "..." --expected "ML is a subset of AI..."

    With LLM metrics:
        ragd evaluate --query "..." --expected "ML is..." --include-llm

    Batch evaluation:
        ragd evaluate --test-file queries.yaml

    Output as JSON:
        ragd evaluate --query "..." --format json
    """
    evaluate_command(
        query=query,
        test_file=test_file,
        expected=expected,
        limit=limit,
        threshold=threshold,
        include_llm=include_llm,
        save=not no_save,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@app.command(
    hidden=not ADMIN_MODE,
    rich_help_panel="Maintenance" if ADMIN_MODE else None,
)
def quality(
    document_id: Annotated[str | None, typer.Argument(help="Document ID to assess (omit for all).")] = None,
    below: float = typer.Option(None, "--below", "-b", help="Only show documents below quality threshold (0-1)."),
    file_type: str = typer.Option(None, "--type", "-t", help="Filter by file type (pdf, html, txt)."),
    test_corpus: Path = typer.Option(None, "--test", help="Test corpus path for CI/batch testing."),
    verbose: bool = typer.Option(False, "--verbose", "-V", help="Show detailed breakdown."),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Assess extraction quality for indexed documents.

    Shows quality metrics including completeness, character quality,
    structure preservation, and image/table handling.

    Modes:
      - No arguments: Report on all indexed documents
      - With document_id: Detailed report for specific document
      - With --test: Batch test a corpus (for CI)

    Examples:
        ragd quality                      # All documents summary
        ragd quality doc-123              # Specific document
        ragd quality --below 0.7          # Low-quality documents
        ragd quality --type pdf           # Only PDFs
        ragd quality --test ~/corpus/     # CI batch testing
        ragd quality --verbose            # Detailed breakdown
    """
    quality_command(
        document_id=document_id,
        below=below,
        file_type=file_type,
        test_corpus=test_corpus,
        verbose=verbose,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


# --- Backend subcommands ---

@backend_app.command("show")
def backend_show(
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Show current backend information.

    Displays the active vector store backend, status, and statistics.

    Examples:
        ragd backend show
        ragd backend show --format json
    """
    backend_show_command(
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@backend_app.command("list")
def backend_list(
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """List available backends.

    Shows all supported vector store backends and their installation status.

    Examples:
        ragd backend list
        ragd backend list --format json
    """
    backend_list_command(
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@backend_app.command("health")
def backend_health(
    backend: Annotated[
        str | None, typer.Argument(help="Backend to check (default: current).")
    ] = None,
    all_backends: bool = typer.Option(
        False, "--all", "-a", help="Check all available backends."
    ),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Run health checks on backends.

    Validates backend connectivity, performance, and data integrity.

    Examples:
        ragd backend health              # Current backend
        ragd backend health chromadb     # Specific backend
        ragd backend health --all        # All available backends
    """
    backend_health_command(
        backend=backend,
        all_backends=all_backends,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@backend_app.command("set")
def backend_set(
    backend: Annotated[str, typer.Argument(help="Backend to set as default.")],
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Set the default backend.

    Changes the vector store backend used for new operations.
    Existing data remains in the previous backend until migrated.

    Available backends: chromadb, faiss

    Examples:
        ragd backend set faiss
        ragd backend set chromadb
    """
    backend_set_command(
        backend=backend,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@backend_app.command("benchmark")
def backend_benchmark(
    backend: Annotated[
        str | None, typer.Argument(help="Backend to benchmark (default: current).")
    ] = None,
    vectors: int = typer.Option(1000, "--vectors", "-v", help="Number of vectors to add."),
    queries: int = typer.Option(100, "--queries", "-q", help="Number of search queries."),
    dimension: int = typer.Option(768, "--dimension", "-d", help="Vector dimension."),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Run performance benchmarks on a backend.

    Measures add, search, delete, and health check performance
    with synthetic data.

    Examples:
        ragd backend benchmark              # Benchmark current backend
        ragd backend benchmark chromadb     # Benchmark ChromaDB
        ragd backend benchmark --vectors 5000 --queries 500
    """
    backend_benchmark_command(
        backend=backend,
        vectors=vectors,
        queries=queries,
        dimension=dimension,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


# --- Delete command ---

delete_app = typer.Typer(help="Delete documents from knowledge base.")
app.add_typer(
    delete_app, name="delete",
    hidden=not ADMIN_MODE,
    rich_help_panel="Maintenance" if ADMIN_MODE else None,
)


@delete_app.callback(invoke_without_command=True)
def delete(
    ctx: typer.Context,
    document_ids: Annotated[
        list[str] | None, typer.Argument(help="Document IDs to delete.")
    ] = None,
    secure: bool = typer.Option(False, "--secure", "-s", help="Use secure deletion (overwrite storage)."),
    purge: bool = typer.Option(False, "--purge", "-p", help="Use cryptographic erasure (rotate key)."),
    source: str = typer.Option(None, "--source", help="Filter by source path."),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt."),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Delete documents from the knowledge base.

    Supports three deletion levels:
    - Standard (default): Remove from index
    - Secure (--secure): Overwrite storage locations
    - Purge (--purge): Cryptographic erasure with key rotation

    Examples:
        ragd delete doc-123              # Standard deletion
        ragd delete doc-123 --secure     # Secure deletion
        ragd delete doc-123 --purge      # Cryptographic erasure
        ragd delete doc-1 doc-2 doc-3    # Bulk deletion
        ragd delete --source ~/old-docs/ # Delete by source
    """
    if ctx.invoked_subcommand is not None:
        return

    if not document_ids and not source:
        ctx.get_help()
        raise typer.Exit(0)

    ids = list(document_ids) if document_ids else []

    delete_command(
        document_ids=ids,
        secure=secure,
        purge=purge,
        source=source,
        force=force,
        no_color=no_color,
    )


@delete_app.command("audit")
def delete_audit(
    show_all: bool = typer.Option(False, "--all", "-a", help="Show all entries."),
    limit: int = typer.Option(10, "--limit", "-n", help="Maximum entries to show."),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Show deletion audit log.

    Displays recent deletion operations for auditing purposes.

    Examples:
        ragd delete audit           # Recent deletions
        ragd delete audit --all     # Full history
        ragd delete audit -n 20     # Last 20 entries
    """
    delete_audit_command(
        show_all=show_all,
        limit=limit,
        no_color=no_color,
    )


# --- Security commands ---

@app.command(
    hidden=not ADMIN_MODE,
    rich_help_panel="Security" if ADMIN_MODE else None,
)
def unlock(
    extend: bool = typer.Option(False, "--extend", "-e", help="Extend existing session timer."),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Unlock encrypted database.

    Prompts for password and unlocks the session for the configured timeout.
    Use --extend to reset the timer on an already-unlocked session.

    Examples:
        ragd unlock              # Unlock with password
        ragd unlock --extend     # Reset session timer
    """
    unlock_command(no_color=no_color, extend=extend)


@app.command(
    hidden=not ADMIN_MODE,
    rich_help_panel="Security" if ADMIN_MODE else None,
)
def lock(
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Lock encryption session immediately.

    Clears encryption keys from memory. Requires re-authentication
    to access encrypted data.

    Examples:
        ragd lock
    """
    lock_command(no_color=no_color)


# --- Password subcommands ---

@password_app.command("change")
def password_change(
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Change encryption password.

    Prompts for current password and new password.
    The session remains active after changing password.

    Examples:
        ragd password change
    """
    password_change_command(no_color=no_color)


@password_app.command("reset")
def password_reset(
    confirm_data_loss: bool = typer.Option(
        False, "--confirm-data-loss", help="Confirm you understand data will be lost."
    ),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Reset encryption (WARNING: deletes all data).

    This is a destructive operation that removes all encryption keys.
    Any encrypted data will become PERMANENTLY INACCESSIBLE.

    Use this only if you've forgotten your password and accept data loss.

    Examples:
        ragd password reset --confirm-data-loss
    """
    password_reset_command(no_color=no_color, confirm_data_loss=confirm_data_loss)


# --- Session subcommands ---

@session_app.command("status")
def session_status(
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Show encryption session status.

    Displays current session state, time remaining until auto-lock,
    and failed authentication attempts.

    Examples:
        ragd session status
    """
    session_status_command(no_color=no_color)


# --- Collection subcommands ---

@collection_app.command("create")
def collection_create(
    name: Annotated[str, typer.Argument(help="Collection name.")],
    include_all: list[str] | None = typer.Option(
        None, "--include-all", "-a",
        help="Tags that must ALL be present (AND logic).",
    ),
    include_any: list[str] | None = typer.Option(
        None, "--include-any", "-o",
        help="Tags where at least ONE must be present (OR logic).",
    ),
    exclude: list[str] | None = typer.Option(
        None, "--exclude", "-x",
        help="Tags that must NOT be present.",
    ),
    description: str = typer.Option("", "--description", "-d", help="Collection description."),
    parent: str | None = typer.Option(None, "--parent", "-p", help="Parent collection name."),
) -> None:
    """Create a new smart collection.

    Smart collections are virtual folders based on tag queries.
    Documents matching the query automatically appear in the collection.

    Examples:
        ragd collection create "Q3 Finance" --include-all finance q3-2024 --exclude draft
        ragd collection create "Research" --include-any academic research papers
        ragd collection create "Active Projects" --include-any project/alpha project/beta
    """
    collection_create_command(
        name=name,
        include_all=include_all,
        include_any=include_any,
        exclude=exclude,
        description=description,
        parent=parent,
    )


@collection_app.command("list")
def collection_list(
    parent: str | None = typer.Option(None, "--parent", "-p", help="List children of this collection."),
) -> None:
    """List all collections.

    Shows collection names, document counts, and query definitions.

    Examples:
        ragd collection list
        ragd collection list --parent "Finance"
    """
    collection_list_command(parent=parent)


@collection_app.command("show")
def collection_show(
    name: Annotated[str, typer.Argument(help="Collection name.")],
    limit: int = typer.Option(20, "--limit", "-n", help="Maximum documents to show."),
) -> None:
    """Show collection details and contents.

    Displays the collection query and matching documents.

    Examples:
        ragd collection show "Q3 Finance"
        ragd collection show "Research" --limit 50
    """
    collection_show_command(name=name, limit=limit)


@collection_app.command("update")
def collection_update(
    name: Annotated[str, typer.Argument(help="Collection name.")],
    include_all: list[str] | None = typer.Option(
        None, "--include-all", "-a",
        help="New tags that must ALL be present.",
    ),
    include_any: list[str] | None = typer.Option(
        None, "--include-any", "-o",
        help="New tags where at least ONE must be present.",
    ),
    exclude: list[str] | None = typer.Option(
        None, "--exclude", "-x",
        help="New tags that must NOT be present.",
    ),
    description: str | None = typer.Option(None, "--description", "-d", help="New description."),
) -> None:
    """Update a collection's query or description.

    Examples:
        ragd collection update "Q3 Finance" --exclude draft review
        ragd collection update "Research" --description "Academic papers"
    """
    collection_update_command(
        name=name,
        include_all=include_all,
        include_any=include_any,
        exclude=exclude,
        description=description,
    )


@collection_app.command("delete")
def collection_delete(
    name: Annotated[str, typer.Argument(help="Collection name.")],
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation."),
) -> None:
    """Delete a collection.

    The documents in the collection are NOT deleted, only the collection definition.

    Examples:
        ragd collection delete "Q3 Finance"
        ragd collection delete "Old Projects" --force
    """
    collection_delete_command(name=name, force=force)


@collection_app.command("export")
def collection_export(
    name: Annotated[str, typer.Argument(help="Collection name.")],
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file."),
    format: str = typer.Option("json", "--format", "-f", help="Output format (json, csv, ids)."),
) -> None:
    """Export collection members.

    Examples:
        ragd collection export "Q3 Finance" --format json > q3_docs.json
        ragd collection export "Research" --format ids > doc_ids.txt
    """
    collection_export_command(name=name, output=output, format=format)


# --- Tag suggestions subcommands ---

@tag_app.command("suggestions")
def tag_suggestions(
    doc_id: Annotated[str, typer.Argument(help="Document ID.")],
    all_: bool = typer.Option(False, "--all", "-a", help="Show all suggestions (not just pending)."),
) -> None:
    """Show tag suggestions for a document.

    Displays auto-generated tag suggestions from KeyBERT, LLM, and NER.

    Examples:
        ragd tag suggestions doc-123
        ragd tag suggestions doc-123 --all
    """
    suggestions_show_command(doc_id=doc_id, all_=all_)


@tag_app.command("pending")
def tag_pending(
    limit: int = typer.Option(20, "--limit", "-n", help="Maximum documents to show."),
) -> None:
    """Show all documents with pending tag suggestions.

    Examples:
        ragd tag pending
        ragd tag pending --limit 50
    """
    suggestions_pending_command(limit=limit)


@tag_app.command("confirm")
def tag_confirm(
    doc_id: Annotated[str, typer.Argument(help="Document ID.")],
    tags: list[str] | None = typer.Argument(None, help="Specific tags to confirm."),
    min_confidence: float | None = typer.Option(
        None, "--min-confidence", "-c",
        help="Only confirm tags above this confidence.",
    ),
) -> None:
    """Confirm tag suggestions and apply them.

    Confirmed suggestions become regular tags with provenance tracking.

    Examples:
        ragd tag confirm doc-123 finance quarterly
        ragd tag confirm doc-123 --min-confidence 0.8
    """
    suggestions_confirm_command(doc_id=doc_id, tags=tags, min_confidence=min_confidence)


@tag_app.command("reject")
def tag_reject(
    doc_id: Annotated[str, typer.Argument(help="Document ID.")],
    tags: list[str] | None = typer.Argument(None, help="Specific tags to reject."),
) -> None:
    """Reject tag suggestions.

    Rejected suggestions won't be shown again.

    Examples:
        ragd tag reject doc-123 irrelevant-tag
        ragd tag reject doc-123  # Reject all pending
    """
    suggestions_reject_command(doc_id=doc_id, tags=tags)


@tag_app.command("stats")
def tag_stats() -> None:
    """Show tag suggestion statistics.

    Displays counts by status and source.

    Examples:
        ragd tag stats
    """
    suggestions_stats_command()


# --- Library subcommands ---

@library_app.command("show")
def library_show_cmd() -> None:
    """Show the tag library with all namespaces.

    Displays system and user namespaces with their allowed tags.

    Examples:
        ragd library show
    """
    library_show_command()


@library_app.command("create")
def library_create(
    name: Annotated[str, typer.Argument(help="Namespace name.")],
    open_: bool = typer.Option(False, "--open", "-o", help="Create as open namespace (any value allowed)."),
    closed: bool = typer.Option(False, "--closed", "-c", help="Create as closed namespace (predefined values only)."),
    description: str = typer.Option("", "--description", "-d", help="Namespace description."),
    tags: list[str] | None = typer.Option(None, "--tags", "-t", help="Initial tag values."),
) -> None:
    """Create a new namespace in the tag library.

    Examples:
        ragd library create project --closed --tags alpha beta gamma
        ragd library create topic --open
    """
    library_create_command(
        name=name,
        open_=open_,
        closed=closed,
        description=description,
        tags=tags,
    )


@library_app.command("add")
def library_add(
    namespace: Annotated[str, typer.Argument(help="Namespace name.")],
    tags: Annotated[list[str], typer.Argument(help="Tag values to add.")],
) -> None:
    """Add tag values to a namespace.

    Examples:
        ragd library add project delta
        ragd library add status pending complete
    """
    library_add_command(namespace=namespace, tags=tags)


@library_app.command("remove")
def library_remove(
    namespace: Annotated[str, typer.Argument(help="Namespace name.")],
    tags: Annotated[list[str], typer.Argument(help="Tag values to remove.")],
) -> None:
    """Remove tag values from a namespace.

    Examples:
        ragd library remove project gamma
    """
    library_remove_command(namespace=namespace, tags=tags)


@library_app.command("rename")
def library_rename(
    namespace: Annotated[str, typer.Argument(help="Namespace name.")],
    old_value: Annotated[str, typer.Argument(help="Current tag value.")],
    new_value: Annotated[str, typer.Argument(help="New tag value.")],
) -> None:
    """Rename a tag value in a namespace.

    Updates the namespace definition and all documents using this tag.

    Examples:
        ragd library rename project alpha apollo
    """
    library_rename_command(namespace=namespace, old_value=old_value, new_value=new_value)


@library_app.command("delete")
def library_delete_cmd(
    name: Annotated[str, typer.Argument(help="Namespace name to delete.")],
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation."),
) -> None:
    """Delete a namespace from the tag library.

    Cannot delete system namespaces. Tags in documents are NOT removed.

    Examples:
        ragd library delete project
        ragd library delete custom --force
    """
    library_delete_command(name=name, force=force)


@library_app.command("hide")
def library_hide(
    name: Annotated[str, typer.Argument(help="Namespace name.")],
    show: bool = typer.Option(False, "--show", "-s", help="Show instead of hide."),
) -> None:
    """Hide a namespace from listings.

    Hidden namespaces still work, just aren't shown in listings.

    Examples:
        ragd library hide sensitivity
        ragd library hide sensitivity --show  # Unhide
    """
    library_hide_command(name=name, show=show)


@library_app.command("validate")
def library_validate() -> None:
    """Validate all tags against the library.

    Shows tags that don't match any namespace definition.

    Examples:
        ragd library validate
    """
    library_validate_command()


@library_app.command("promote")
def library_promote(
    tag_name: Annotated[str, typer.Argument(help="Tag name to promote.")],
    namespace: str = typer.Option(..., "--namespace", "-n", help="Target namespace."),
) -> None:
    """Promote a pending tag to a namespace.

    Examples:
        ragd library promote machine-learning --namespace topic
    """
    library_promote_command(tag_name=tag_name, namespace=namespace)


@library_app.command("pending")
def library_pending() -> None:
    """Show pending tags awaiting promotion.

    Examples:
        ragd library pending
    """
    library_pending_command()


@library_app.command("stats")
def library_stats_cmd() -> None:
    """Show tag library statistics.

    Examples:
        ragd library stats
    """
    library_stats_command()


@app.command("help", rich_help_panel="Setup & Help")
def help_cmd(
    topic: Annotated[str | None, typer.Argument(help="Help topic (command name).")] = None,
    examples: bool = typer.Option(False, "--examples", "-e", help="Show only examples."),
) -> None:
    """Show extended help for commands.

    View detailed documentation with examples for any command.

    Examples:
        ragd help                  # List all help topics
        ragd help search           # Extended search help
        ragd help search --examples  # Just search examples
    """
    con = Console()

    if topic is None:
        list_help_topics(con)
    elif examples:
        show_examples(topic, con)
    else:
        show_extended_help(topic, con)


# --- Audit subcommands ---

@audit_app.command("list")
def audit_list(
    operation: str | None = typer.Option(None, "--operation", "-o", help="Filter by operation type."),
    result: str | None = typer.Option(None, "--result", "-r", help="Filter by result."),
    since: str | None = typer.Option(None, "--since", help="Show entries since date (YYYY-MM-DD)."),
    until: str | None = typer.Option(None, "--until", help="Show entries until date (YYYY-MM-DD)."),
    limit: int = typer.Option(20, "--limit", "-n", help="Maximum entries to show."),
    output_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """List recent operations from the audit log.

    Shows a table of recent operations with their results.

    Examples:
        ragd audit list
        ragd audit list --operation index
        ragd audit list --result failed --limit 50
        ragd audit list --since 2024-01-01
    """
    audit_list_command(
        console=Console(),
        operation=operation,
        result=result,
        since=since,
        until=until,
        limit=limit,
        output_json=output_json,
    )


@audit_app.command("show")
def audit_show(
    entry_id: Annotated[str, typer.Argument(help="Audit entry ID (or prefix).")],
    output_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Show details of a specific audit entry.

    Displays full details including operation-specific metadata.

    Examples:
        ragd audit show abc123
        ragd audit show abc123 --json
    """
    audit_show_command(
        console=Console(),
        entry_id=entry_id,
        output_json=output_json,
    )


@audit_app.command("clear")
def audit_clear(
    before: str | None = typer.Option(None, "--before", help="Clear entries before date (YYYY-MM-DD)."),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt."),
) -> None:
    """Clear audit log entries.

    Removes old entries from the audit log.

    Examples:
        ragd audit clear --before 2024-01-01
        ragd audit clear --force
    """
    audit_clear_command(
        console=Console(),
        before=before,
        force=force,
    )


@audit_app.command("stats")
def audit_stats(
    output_json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Show audit log statistics.

    Displays summary of operations in the audit log.

    Examples:
        ragd audit stats
        ragd audit stats --json
    """
    audit_stats_command(
        console=Console(),
        output_json=output_json,
    )


if __name__ == "__main__":
    app()
