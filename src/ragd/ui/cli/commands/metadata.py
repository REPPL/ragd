"""Metadata CLI commands for ragd.

This module contains commands for managing document metadata and tags.
"""

from __future__ import annotations

import typer

from ragd.ui import OutputFormat
from ragd.ui.cli.utils import get_console


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
        changes.append("Description: updated")

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


__all__ = [
    "meta_show_command",
    "meta_edit_command",
    "tag_add_command",
    "tag_remove_command",
    "tag_list_command",
]
