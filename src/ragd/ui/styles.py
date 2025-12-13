"""Visual styles and helpers for ragd CLI.

Rich Panel banners and standardised formatting for a clean, professional CLI.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from ragd import __description__


# Status indicators (ASCII-only)
class Icons:
    """Standardised ASCII status indicators."""

    OK = "[green][OK][/green]"
    WARN = "[yellow][!!][/yellow]"
    ERROR = "[red][XX][/red]"
    INFO = "[dim][--][/dim]"
    ARROW = "->"
    BULLET = "*"


def print_banner(
    console: Console,
    title: str,
    subtitle: str | None = None,
    border_style: str = "cyan",
) -> None:
    """Print a Rich Panel banner.

    Args:
        console: Rich console instance
        title: Main title text
        subtitle: Optional subtitle text
        border_style: Panel border colour (default: cyan)
    """
    content = f"[bold cyan]{title}[/bold cyan]"
    if subtitle:
        content += f"\n[dim]{subtitle}[/dim]"
    console.print(Panel(content, expand=False, border_style=border_style))


def print_chat_header(
    console: Console,
    model: str,
    context_window: int | None = None,
) -> None:
    """Print the chat command header.

    Args:
        console: Rich console instance
        model: Model name to display
        context_window: Context window size in tokens (optional)
    """
    print_banner(
        console,
        "ragd Chat",
        __description__,
    )
    # Format context window with comma separators (e.g., 131,072)
    if context_window:
        ctx_display = f"{context_window:,}"
        console.print(f"[dim]Model: {model} | Context: {ctx_display} tokens | Type '/help' for commands[/dim]\n")
    else:
        console.print(f"[dim]Model: {model} | Type '/help' for commands[/dim]\n")


def print_init_header(console: Console) -> None:
    """Print the init command header.

    Args:
        console: Rich console instance
    """
    print_banner(
        console,
        "ragd Setup",
        __description__,
    )
    console.print()


def print_search_header(console: Console, query: str, result_count: int) -> None:
    """Print the search command header.

    Args:
        console: Rich console instance
        query: Search query
        result_count: Number of results found
    """
    truncated_query = query[:40] + "..." if len(query) > 40 else query
    console.print(f"\n[bold]Search Results[/bold] for: [cyan]{truncated_query}[/cyan]")
    console.print(f"[dim]Found {result_count} result{'s' if result_count != 1 else ''}[/dim]\n")


def format_health_check(
    name: str,
    status: str,
    message: str,
    width: int = 50,
) -> str:
    """Format a single health check result.

    Args:
        name: Check name
        status: Status (healthy, degraded, unhealthy)
        message: Status message
        width: Total width for alignment

    Returns:
        Formatted string for display
    """
    icon = {
        "healthy": Icons.OK,
        "degraded": Icons.WARN,
        "unhealthy": Icons.ERROR,
    }.get(status.lower(), Icons.INFO)

    # Truncate message if needed
    max_msg_len = width - len(name) - 10
    if len(message) > max_msg_len:
        message = message[: max_msg_len - 3] + "..."

    return f"  {icon} {name:<20} {message}"


def print_dependency_error(
    console: Console,
    feature: str,
    install_command: str,
    extra_steps: str | None = None,
) -> None:
    """Print a formatted dependency error message.

    Args:
        console: Rich console instance
        feature: Feature name that requires the dependency
        install_command: pip install command
        extra_steps: Optional additional setup steps
    """
    width = 60
    border = "+" + "-" * (width - 2) + "+"
    empty = "|" + " " * (width - 2) + "|"

    console.print()
    console.print("+-- [red]Missing Optional Dependency[/red] " + "-" * (width - 34) + "+")
    console.print(empty)
    console.print(f"|  The '{feature}' feature is required for this operation." + " " * (width - 53 - len(feature)) + "|")
    console.print(empty)
    console.print("|  [dim]To install:[/dim]" + " " * (width - 16) + "|")
    console.print(f"|    [cyan]{install_command}[/cyan]" + " " * (width - 8 - len(install_command)) + "|")

    if extra_steps:
        console.print(empty)
        console.print("|  [dim]Then run:[/dim]" + " " * (width - 14) + "|")
        console.print(f"|    [cyan]{extra_steps}[/cyan]" + " " * (width - 8 - len(extra_steps)) + "|")

    console.print(empty)
    console.print(border)
    console.print()
