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
)

app = typer.Typer(
    name="ragd",
    help="Local RAG for personal knowledge management.",
    no_args_is_help=True,
)
console = Console()


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
    verbose: bool = typer.Option(
        False, "--verbose", "-V", help="Show per-file progress instead of progress bar."
    ),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Index documents from a file or directory.

    Supported formats: PDF, TXT, MD, HTML
    """
    index_command(
        path=path,
        recursive=recursive,
        skip_duplicates=skip_duplicates,
        verbose=verbose,
        output_format=output_format,  # type: ignore
        no_color=no_color,
    )


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Search query.")],
    limit: int = typer.Option(10, "--limit", "-n", help="Maximum number of results."),
    min_score: float = typer.Option(
        None, "--min-score", help="Minimum similarity score (0-1). Default: 0.3"
    ),
    no_interactive: bool = typer.Option(
        False, "--no-interactive", help="Disable interactive navigator, print results directly."
    ),
    output_format: FormatOption = "rich",
    no_color: bool = typer.Option(False, "--no-color", help="Disable colour output."),
) -> None:
    """Search indexed documents with natural language.

    Returns the most relevant document chunks based on semantic similarity.
    By default, opens an interactive navigator to browse results (use j/k or arrows to navigate, q to quit).
    """
    search_command(
        query=query,
        limit=limit,
        min_score=min_score,
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


if __name__ == "__main__":
    app()
