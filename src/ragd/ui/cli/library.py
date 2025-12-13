"""CLI commands for Tag Library Management.

F-062: Tag Library Management
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from ragd.config import load_config
from ragd.metadata import MetadataStore, TagManager
from ragd.metadata.library import TagLibrary

console = Console()


def _get_tag_library() -> TagLibrary:
    """Get or create TagLibrary instance."""
    config = load_config()
    db_path = config.metadata_path
    store = MetadataStore(db_path)
    tag_manager = TagManager(store)
    return TagLibrary(db_path, tag_manager)


def library_show_command() -> None:
    """Show the tag library with all namespaces."""
    library = _get_tag_library()
    namespaces = library.list_namespaces(include_hidden=False)

    if not namespaces:
        console.print("[yellow]No namespaces defined[/yellow]")
        return

    # Separate system and user namespaces
    system_ns = [ns for ns in namespaces if ns.is_system]
    user_ns = [ns for ns in namespaces if not ns.is_system]

    if system_ns:
        console.print("\n[bold]System Namespaces[/bold]")
        for ns in system_ns:
            mode = "[dim]open[/dim]" if ns.is_open else ""
            tags_str = ", ".join(ns.tags) if ns.tags else "[dim]*[/dim]"
            console.print(f"  [cyan]{ns.name}[/cyan]: {tags_str} {mode}")

    if user_ns:
        console.print("\n[bold]User Namespaces[/bold]")
        for ns in user_ns:
            mode = "[yellow](open)[/yellow]" if ns.is_open else "[blue](closed)[/blue]"
            tags_str = ", ".join(ns.tags) if ns.tags else "[dim]*[/dim]"
            console.print(f"  [cyan]{ns.name}[/cyan]: {tags_str} {mode}")

    # Pending tags
    pending = library.get_pending_tags()
    if pending:
        console.print(f"\n[yellow]Pending Suggestions:[/yellow] {len(pending)} tags awaiting review")

    console.print()


def library_create_command(
    name: str = typer.Argument(..., help="Namespace name"),
    open_: bool = typer.Option(False, "--open", "-o", help="Create as open namespace (any value allowed)"),
    closed: bool = typer.Option(False, "--closed", "-c", help="Create as closed namespace (predefined values only)"),
    description: str = typer.Option("", "--description", "-d", help="Namespace description"),
    tags: list[str] | None = typer.Option(None, "--tags", "-t", help="Initial tag values (for closed namespaces)"),
) -> None:
    """Create a new namespace in the tag library."""
    library = _get_tag_library()

    # Determine mode
    is_open = open_
    if closed:
        is_open = False
    elif not open_ and not closed:
        is_open = False  # Default to closed

    try:
        namespace = library.create_namespace(
            name,
            is_open=is_open,
            description=description,
            tags=tags,
        )
        mode = "open" if namespace.is_open else "closed"
        console.print(f"[green]Created namespace '{name}' ({mode})[/green]")
        if tags:
            console.print(f"  Tags: {', '.join(tags)}")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


def library_add_command(
    namespace: str = typer.Argument(..., help="Namespace name"),
    tags: list[str] = typer.Argument(..., help="Tag values to add"),
) -> None:
    """Add tag values to a namespace."""
    library = _get_tag_library()

    added = 0
    for tag in tags:
        if library.add_tag_to_namespace(namespace, tag):
            added += 1

    if added:
        console.print(f"[green]Added {added} tag(s) to namespace '{namespace}'[/green]")
    else:
        console.print("[yellow]No tags added (namespace not found or tags already exist)[/yellow]")


def library_remove_command(
    namespace: str = typer.Argument(..., help="Namespace name"),
    tags: list[str] = typer.Argument(..., help="Tag values to remove"),
) -> None:
    """Remove tag values from a namespace."""
    library = _get_tag_library()

    removed = 0
    for tag in tags:
        if library.remove_tag_from_namespace(namespace, tag):
            removed += 1

    if removed:
        console.print(f"[green]Removed {removed} tag(s) from namespace '{namespace}'[/green]")
    else:
        console.print("[yellow]No tags removed (not found)[/yellow]")


def library_rename_command(
    namespace: str = typer.Argument(..., help="Namespace name"),
    old_value: str = typer.Argument(..., help="Current tag value"),
    new_value: str = typer.Argument(..., help="New tag value"),
) -> None:
    """Rename a tag value in a namespace (updates all documents)."""
    library = _get_tag_library()

    updated = library.rename_tag_in_namespace(namespace, old_value, new_value)

    if updated:
        console.print(f"[green]Renamed '{old_value}' to '{new_value}' in {updated} documents[/green]")
    else:
        console.print("[yellow]No documents updated[/yellow]")


def library_delete_command(
    name: str = typer.Argument(..., help="Namespace name to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete a namespace from the tag library."""
    library = _get_tag_library()
    namespace = library.get_namespace(name)

    if namespace is None:
        console.print(f"[red]Namespace not found: {name}[/red]")
        raise typer.Exit(1)

    if namespace.is_system:
        console.print(f"[red]Cannot delete system namespace: {name}[/red]")
        raise typer.Exit(1)

    if not force:
        console.print(f"Namespace '{name}' contains {len(namespace.tags)} tag values.")
        console.print("[yellow]Tags in documents will NOT be removed, only the namespace definition.[/yellow]")
        if not typer.confirm("Delete this namespace?"):
            raise typer.Exit(0)

    try:
        library.delete_namespace(name)
        console.print(f"[green]Deleted namespace '{name}'[/green]")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


def library_hide_command(
    name: str = typer.Argument(..., help="Namespace name"),
    show: bool = typer.Option(False, "--show", "-s", help="Show instead of hide"),
) -> None:
    """Hide a namespace from listings (still functional)."""
    library = _get_tag_library()

    if library.hide_namespace(name, hidden=not show):
        action = "Showing" if show else "Hidden"
        console.print(f"[green]{action} namespace '{name}'[/green]")
    else:
        console.print(f"[red]Namespace not found: {name}[/red]")
        raise typer.Exit(1)


def library_validate_command() -> None:
    """Validate all tags in the knowledge base against the library."""
    library = _get_tag_library()
    invalid = library.validate_all_tags()

    if not invalid:
        console.print("[green]All tags are valid[/green]")
        return

    table = Table(title=f"Invalid Tags ({len(invalid)} found)")
    table.add_column("Document ID", style="dim")
    table.add_column("Tag", style="cyan")
    table.add_column("Error", style="red")

    for doc_id, tag, error in invalid[:50]:
        table.add_row(
            doc_id[:12] + "...",
            tag,
            error,
        )

    console.print(table)

    if len(invalid) > 50:
        console.print(f"\n[dim]Showing 50 of {len(invalid)} invalid tags[/dim]")


def library_promote_command(
    tag_name: str = typer.Argument(..., help="Tag name to promote"),
    namespace: str = typer.Option(..., "--namespace", "-n", help="Target namespace"),
) -> None:
    """Promote a pending tag to a namespace."""
    library = _get_tag_library()

    if library.promote_pending_tag(tag_name, namespace):
        console.print(f"[green]Promoted '{tag_name}' to namespace '{namespace}'[/green]")
    else:
        console.print("[red]Failed to promote tag (namespace not found or tag not in pending)[/red]")
        raise typer.Exit(1)


def library_pending_command() -> None:
    """Show pending tags awaiting promotion to library."""
    library = _get_tag_library()
    pending = library.get_pending_tags()

    if not pending:
        console.print("[green]No pending tags[/green]")
        return

    table = Table(title="Pending Tags")
    table.add_column("Tag Name", style="cyan")
    table.add_column("Suggested Namespace")

    for tag_name, namespace in pending:
        table.add_row(tag_name, namespace or "-")

    console.print(table)


def library_stats_command() -> None:
    """Show tag library statistics."""
    library = _get_tag_library()
    stats = library.stats()

    console.print("\n[bold]Tag Library Statistics[/bold]\n")
    console.print(f"  Total namespaces: {stats['total_namespaces']}")
    console.print(f"    System: {stats['system_namespaces']}")
    console.print(f"    User: {stats['user_namespaces']}")
    console.print(f"  Total tag values: {stats['total_tag_values']}")
    console.print(f"  Pending tags: {stats['pending_tags']}")
    console.print()
