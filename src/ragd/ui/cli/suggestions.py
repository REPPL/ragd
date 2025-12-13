"""CLI commands for Auto-Tag Suggestions.

F-061: Auto-Tag Suggestions
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from ragd.config import load_config
from ragd.metadata import MetadataStore, TagManager
from ragd.metadata.suggestions import SuggestionEngine

console = Console()


def _get_suggestion_engine() -> SuggestionEngine:
    """Get or create SuggestionEngine instance."""
    config = load_config()
    db_path = config.metadata_path
    store = MetadataStore(db_path)
    tag_manager = TagManager(store)
    return SuggestionEngine(db_path, tag_manager)


def suggestions_show_command(
    doc_id: str = typer.Argument(..., help="Document ID"),
    all_: bool = typer.Option(False, "--all", "-a", help="Show all suggestions (not just pending)"),
) -> None:
    """Show tag suggestions for a document."""
    engine = _get_suggestion_engine()
    config = load_config()
    store = MetadataStore(config.metadata_path)

    metadata = store.get(doc_id)
    if metadata is None:
        console.print(f"[red]Document not found: {doc_id}[/red]")
        raise typer.Exit(1)

    suggestions = engine.get_for_doc(
        doc_id,
        status=None if all_ else "pending",
    )

    if not suggestions:
        console.print(f"[yellow]No {'suggestions' if all_ else 'pending suggestions'} for this document[/yellow]")
        return

    console.print(f"\n[bold]Suggestions for:[/bold] {metadata.dc_title}")
    console.print()

    table = Table()
    table.add_column("Tag", style="cyan")
    table.add_column("Source")
    table.add_column("Confidence", justify="right")
    table.add_column("Status")

    source_colours = {
        "keybert": "blue",
        "llm": "magenta",
        "ner": "green",
        "imported": "yellow",
    }

    status_colours = {
        "pending": "yellow",
        "confirmed": "green",
        "rejected": "red",
    }

    for s in suggestions:
        source_style = source_colours.get(s.source, "white")
        status_style = status_colours.get(s.status, "white")

        table.add_row(
            s.tag_name,
            f"[{source_style}]{s.source}[/{source_style}]",
            f"{s.confidence:.2f}",
            f"[{status_style}]{s.status}[/{status_style}]",
        )

    console.print(table)


def suggestions_pending_command(
    limit: int = typer.Option(20, "--limit", "-n", help="Maximum documents to show"),
) -> None:
    """Show all documents with pending suggestions."""
    engine = _get_suggestion_engine()
    config = load_config()
    store = MetadataStore(config.metadata_path)

    doc_ids = engine.get_pending_docs()

    if not doc_ids:
        console.print("[green]No pending suggestions[/green]")
        return

    table = Table(title=f"Documents with Pending Suggestions ({len(doc_ids)} total)")
    table.add_column("Document ID", style="dim")
    table.add_column("Title")
    table.add_column("Pending", justify="right")

    for doc_id in doc_ids[:limit]:
        metadata = store.get(doc_id)
        count = engine.count_pending(doc_id)
        title = metadata.dc_title if metadata else "-"

        table.add_row(
            doc_id[:12] + "...",
            title[:40] + "..." if len(title) > 40 else title,
            str(count),
        )

    console.print(table)

    if len(doc_ids) > limit:
        console.print(f"\n[dim]Showing {limit} of {len(doc_ids)} documents[/dim]")


def suggestions_confirm_command(
    doc_id: str = typer.Argument(..., help="Document ID"),
    tags: list[str] | None = typer.Argument(None, help="Specific tags to confirm (default: all)"),
    min_confidence: float | None = typer.Option(
        None, "--min-confidence", "-c",
        help="Only confirm tags above this confidence",
    ),
) -> None:
    """Confirm tag suggestions and apply them."""
    engine = _get_suggestion_engine()
    config = load_config()
    store = MetadataStore(config.metadata_path)

    metadata = store.get(doc_id)
    if metadata is None:
        console.print(f"[red]Document not found: {doc_id}[/red]")
        raise typer.Exit(1)

    confirmed = engine.confirm(
        doc_id,
        tag_names=tags,
        min_confidence=min_confidence,
    )

    if confirmed:
        console.print(f"[green]Confirmed {confirmed} suggestions for '{metadata.dc_title}'[/green]")
    else:
        console.print("[yellow]No suggestions to confirm[/yellow]")


def suggestions_reject_command(
    doc_id: str = typer.Argument(..., help="Document ID"),
    tags: list[str] | None = typer.Argument(None, help="Specific tags to reject (default: all pending)"),
) -> None:
    """Reject tag suggestions."""
    engine = _get_suggestion_engine()
    config = load_config()
    store = MetadataStore(config.metadata_path)

    metadata = store.get(doc_id)
    if metadata is None:
        console.print(f"[red]Document not found: {doc_id}[/red]")
        raise typer.Exit(1)

    rejected = engine.reject(doc_id, tag_names=tags)

    if rejected:
        console.print(f"[green]Rejected {rejected} suggestions for '{metadata.dc_title}'[/green]")
    else:
        console.print("[yellow]No suggestions to reject[/yellow]")


def suggestions_stats_command() -> None:
    """Show suggestion statistics."""
    engine = _get_suggestion_engine()
    stats = engine.stats()

    console.print("\n[bold]Tag Suggestion Statistics[/bold]\n")

    # By status
    table = Table(title="By Status")
    table.add_column("Status")
    table.add_column("Count", justify="right")

    status_colours = {
        "pending": "yellow",
        "confirmed": "green",
        "rejected": "red",
    }

    for status, count in stats.get("by_status", {}).items():
        colour = status_colours.get(status, "white")
        table.add_row(f"[{colour}]{status}[/{colour}]", str(count))

    console.print(table)
    console.print()

    # By source
    table = Table(title="By Source")
    table.add_column("Source")
    table.add_column("Count", justify="right")

    for source, count in stats.get("by_source", {}).items():
        table.add_row(source, str(count))

    console.print(table)
    console.print()

    console.print(f"Documents with pending: {stats.get('docs_with_pending', 0)}")
    console.print(f"Total suggestions: {stats.get('total', 0)}")
