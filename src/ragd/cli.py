"""CLI interface for ragd using Typer."""

import typer
from rich.console import Console

from ragd import __version__

app = typer.Typer(
    name="ragd",
    help="Local RAG for personal knowledge management.",
    no_args_is_help=True,
)
console = Console()


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
def status() -> None:
    """Show ragd status."""
    console.print("[green]ragd is ready[/green]")
    console.print(f"Version: {__version__}")


if __name__ == "__main__":
    app()
