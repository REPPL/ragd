"""CLI interface for ragd using Typer.

This module provides the command-line interface for ragd, including commands
for initialisation, indexing, searching, and system status.

Command implementations are in ragd.ui.cli.commands.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from ragd import __version__
from ragd.ui.cli import (
    get_console,
    init_command,
    index_command,
    search_command,
    status_command,
    doctor_command,
    config_command,
    reindex_command,
    meta_show_command,
    meta_edit_command,
    tag_add_command,
    tag_remove_command,
    tag_list_command,
    list_documents_command,
)

app = typer.Typer(
    name="ragd",
    help="Local RAG for personal knowledge management.",
    no_args_is_help=True,
)
console = Console()

# Subcommand groups
meta_app = typer.Typer(help="Manage document metadata.")
tag_app = typer.Typer(help="Manage document tags.")
app.add_typer(meta_app, name="meta")
app.add_typer(tag_app, name="tag")


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


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """ragd - Local RAG for personal knowledge management."""


@app.command()
def init(
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Initialise ragd with guided setup.

    Detects hardware capabilities and creates optimal configuration.
    """
    init_command(no_color=no_color)


@app.command()
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


@app.command()
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
    )


@app.command()
def status(
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Show ragd status and statistics."""
    status_command(
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@app.command()
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


@app.command()
def config(
    show: bool = typer.Option(False, "--show", "-s", help="Show current configuration."),
    path: bool = typer.Option(False, "--path", "-p", help="Show configuration file path."),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Manage ragd configuration."""
    config_command(
        show=show,
        path=path,
        no_color=no_color,
    )


@app.command()
def reindex(
    document_id: Annotated[
        str | None, typer.Argument(help="Specific document ID to re-index.")
    ] = None,
    all_docs: bool = typer.Option(False, "--all", "-a", help="Re-index all documents."),
    file_type: str = typer.Option(None, "--type", "-t", help="Re-index by file type (pdf, html)."),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt."),
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


# --- List command ---

@app.command("list")
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


if __name__ == "__main__":
    app()
