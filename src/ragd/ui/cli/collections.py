"""CLI commands for Smart Collections.

F-063: Smart Collections
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from ragd.config import load_config
from ragd.metadata import MetadataStore, TagManager
from ragd.metadata.collections import CollectionManager

console = Console()


def _get_collection_manager() -> CollectionManager:
    """Get or create CollectionManager instance."""
    config = load_config()
    db_path = config.metadata_path
    store = MetadataStore(db_path)
    tag_manager = TagManager(store)
    return CollectionManager(db_path, tag_manager)


def collection_create_command(
    name: str = typer.Argument(..., help="Collection name"),
    include_all: list[str] | None = typer.Option(
        None, "--include-all", "-a",
        help="Tags that must ALL be present (AND logic)",
    ),
    include_any: list[str] | None = typer.Option(
        None, "--include-any", "-o",
        help="Tags where at least ONE must be present (OR logic)",
    ),
    exclude: list[str] | None = typer.Option(
        None, "--exclude", "-x",
        help="Tags that must NOT be present",
    ),
    description: str = typer.Option("", "--description", "-d", help="Collection description"),
    parent: str | None = typer.Option(None, "--parent", "-p", help="Parent collection name"),
) -> None:
    """Create a new smart collection."""
    try:
        manager = _get_collection_manager()
        collection = manager.create(
            name,
            include_all=include_all,
            include_any=include_any,
            exclude=exclude,
            description=description,
            parent_name=parent,
        )
        count = manager.count_members(name)
        console.print(f"[green]Created collection '{name}'[/green]")
        console.print(f"  Query: {collection.query.to_string()}")
        console.print(f"  Documents: {count}")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e


def collection_list_command(
    parent: str | None = typer.Option(None, "--parent", "-p", help="List children of this collection"),
) -> None:
    """List all collections."""
    manager = _get_collection_manager()

    if parent:
        collections = manager.list_children(parent)
        if not collections:
            console.print(f"[yellow]No child collections for '{parent}'[/yellow]")
            return
    else:
        collections = manager.list_all()
        if not collections:
            console.print("[yellow]No collections defined[/yellow]")
            return

    table = Table(title="Smart Collections")
    table.add_column("Name", style="cyan")
    table.add_column("Documents", justify="right")
    table.add_column("Query")
    table.add_column("Parent")

    for col in collections:
        count = manager.count_members(col.name)
        parent_col = None
        if col.parent_id:
            parent_obj = manager.get(col.parent_id)
            parent_col = parent_obj.name if parent_obj else None

        table.add_row(
            col.name,
            str(count),
            col.query.to_string(),
            parent_col or "-",
        )

    console.print(table)


def collection_show_command(
    name: str = typer.Argument(..., help="Collection name"),
    limit: int = typer.Option(20, "--limit", "-n", help="Maximum documents to show"),
) -> None:
    """Show collection details and contents."""
    manager = _get_collection_manager()
    collection = manager.get_by_name(name)

    if collection is None:
        console.print(f"[red]Collection not found: {name}[/red]")
        raise typer.Exit(1)

    members = manager.get_members(name)

    console.print(f"\n[bold cyan]{collection.name}[/bold cyan]")
    if collection.description:
        console.print(f"  {collection.description}")
    console.print(f"\n  Query: [yellow]{collection.query.to_string()}[/yellow]")
    console.print(f"  Documents: {len(members)}")

    if collection.parent_id:
        parent = manager.get(collection.parent_id)
        if parent:
            console.print(f"  Parent: {parent.name}")

    children = manager.list_children(name)
    if children:
        console.print(f"  Children: {', '.join(c.name for c in children)}")

    console.print()

    if members:
        config = load_config()
        store = MetadataStore(config.metadata_path)
        tag_manager = TagManager(store)

        table = Table(title=f"Documents ({len(members)} total)")
        table.add_column("ID", style="dim")
        table.add_column("Title")
        table.add_column("Tags")

        for doc_id in members[:limit]:
            metadata = store.get(doc_id)
            tags = tag_manager.get_names(doc_id)
            title = metadata.dc_title if metadata else "-"
            table.add_row(
                doc_id[:12] + "...",
                title[:40] + "..." if len(title) > 40 else title,
                ", ".join(tags[:5]) + ("..." if len(tags) > 5 else ""),
            )

        console.print(table)

        if len(members) > limit:
            console.print(f"\n[dim]Showing {limit} of {len(members)} documents[/dim]")


def collection_update_command(
    name: str = typer.Argument(..., help="Collection name"),
    include_all: list[str] | None = typer.Option(
        None, "--include-all", "-a",
        help="New tags that must ALL be present",
    ),
    include_any: list[str] | None = typer.Option(
        None, "--include-any", "-o",
        help="New tags where at least ONE must be present",
    ),
    exclude: list[str] | None = typer.Option(
        None, "--exclude", "-x",
        help="New tags that must NOT be present",
    ),
    description: str | None = typer.Option(None, "--description", "-d", help="New description"),
) -> None:
    """Update a collection's query or description."""
    manager = _get_collection_manager()

    if not manager.update(
        name,
        include_all=include_all,
        include_any=include_any,
        exclude=exclude,
        description=description,
    ):
        console.print(f"[red]Collection not found: {name}[/red]")
        raise typer.Exit(1)

    collection = manager.get_by_name(name)
    count = manager.count_members(name)
    console.print(f"[green]Updated collection '{name}'[/green]")
    if collection:
        console.print(f"  Query: {collection.query.to_string()}")
    console.print(f"  Documents: {count}")


def collection_delete_command(
    name: str = typer.Argument(..., help="Collection name"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete a collection (does not delete documents)."""
    manager = _get_collection_manager()
    collection = manager.get_by_name(name)

    if collection is None:
        console.print(f"[red]Collection not found: {name}[/red]")
        raise typer.Exit(1)

    if not force:
        count = manager.count_members(name)
        console.print(f"Collection '{name}' contains {count} documents.")
        console.print("[yellow]The documents will NOT be deleted, only the collection.[/yellow]")
        if not typer.confirm("Delete this collection?"):
            raise typer.Exit(0)

    if manager.delete(name):
        console.print(f"[green]Deleted collection '{name}'[/green]")
    else:
        console.print("[red]Failed to delete collection[/red]")
        raise typer.Exit(1)


def collection_export_command(
    name: str = typer.Argument(..., help="Collection name"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file (default: stdout)"),
    format: str = typer.Option("json", "--format", "-f", help="Output format (json, csv, ids)"),
) -> None:
    """Export collection members."""
    manager = _get_collection_manager()
    collection = manager.get_by_name(name)

    if collection is None:
        console.print(f"[red]Collection not found: {name}[/red]")
        raise typer.Exit(1)

    members = manager.get_members(name)
    config = load_config()
    store = MetadataStore(config.metadata_path)

    if format == "ids":
        content = "\n".join(members)
    elif format == "csv":
        lines = ["id,title,source_path"]
        for doc_id in members:
            metadata = store.get(doc_id)
            if metadata:
                title = metadata.dc_title.replace('"', '""')
                path = metadata.ragd_source_path or ""
                lines.append(f'"{doc_id}","{title}","{path}"')
        content = "\n".join(lines)
    else:  # json
        data = {
            "collection": name,
            "query": collection.query.to_dict(),
            "count": len(members),
            "documents": [],
        }
        for doc_id in members:
            metadata = store.get(doc_id)
            if metadata:
                data["documents"].append({
                    "id": doc_id,
                    "title": metadata.dc_title,
                    "source_path": metadata.ragd_source_path,
                })
        content = json.dumps(data, indent=2)

    if output:
        output.write_text(content)
        console.print(f"[green]Exported {len(members)} documents to {output}[/green]")
    else:
        console.print(content)
