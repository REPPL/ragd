"""Interactive prompts for model card discovery.

Provides Rich-based UI for confirming and editing discovered model cards.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

from ragd.models.cards import ModelCard

if TYPE_CHECKING:
    from rich.console import Console


def prompt_card_confirmation(
    card: ModelCard,
    console: Console,
) -> ModelCard | None:
    """Prompt user to confirm or edit a discovered model card.

    Args:
        card: Draft ModelCard to confirm
        console: Rich console for output

    Returns:
        Confirmed ModelCard or None if cancelled
    """
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.table import Table

    # Display discovered metadata
    console.print()
    console.print(f"[bold]Discovered metadata for {card.id}[/bold]")
    console.print()

    # Create summary table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style="dim")
    table.add_column("Value")

    table.add_row("Name", card.name)
    table.add_row("Type", card.model_type.value.upper())
    table.add_row("Provider", card.provider)

    if card.parameters:
        table.add_row("Parameters", f"{card.parameters}B")
    if card.context_length:
        table.add_row("Context Length", f"{card.context_length:,} tokens")

    if card.capabilities:
        caps = ", ".join(c.value for c in card.capabilities)
        table.add_row("Capabilities", caps)

    if card.hardware:
        ram = f"{card.hardware.min_ram_gb}GB min"
        table.add_row("RAM", ram)

    # Show sources
    sources = card.metadata.get("sources", [])
    if sources:
        table.add_row("Sources", ", ".join(sources))

    console.print(Panel(table, title="Model Card Preview", border_style="blue"))
    console.print()

    # Prompt for action
    console.print("[1] Save card as-is")
    console.print("[2] Edit before saving")
    console.print("[3] View full YAML")
    console.print("[4] Cancel (use in-memory only)")
    console.print()

    choice = Prompt.ask(
        "Choice",
        choices=["1", "2", "3", "4"],
        default="1",
        console=console,
    )

    if choice == "1":
        return card

    elif choice == "2":
        return _edit_card(card, console)

    elif choice == "3":
        # Show full YAML
        yaml_str = yaml.dump(card.to_dict(), default_flow_style=False)
        console.print(Panel(yaml_str, title="Full YAML", border_style="green"))
        console.print()

        # Ask again
        save = Prompt.ask(
            "Save this card?",
            choices=["y", "n"],
            default="y",
            console=console,
        )
        if save.lower() == "y":
            return card
        return None

    else:  # choice == "4"
        console.print("[dim]Card not saved, using in-memory only.[/dim]")
        return None


def _edit_card(card: ModelCard, console: Console) -> ModelCard | None:
    """Edit card fields interactively.

    Args:
        card: Card to edit
        console: Rich console

    Returns:
        Edited card or None if cancelled
    """
    from rich.prompt import Prompt

    console.print()
    console.print("[bold]Edit Model Card[/bold]")
    console.print("[dim]Press Enter to keep current value, or type new value[/dim]")
    console.print()

    # Edit name
    new_name = Prompt.ask(
        "Name",
        default=card.name,
        console=console,
    )

    # Edit context length
    ctx_default = str(card.context_length) if card.context_length else ""
    ctx_str = Prompt.ask(
        "Context length (tokens)",
        default=ctx_default,
        console=console,
    )
    try:
        new_context = int(ctx_str) if ctx_str else None
    except ValueError:
        new_context = card.context_length

    # Edit parameters
    param_default = str(card.parameters) if card.parameters else ""
    param_str = Prompt.ask(
        "Parameters (billions)",
        default=param_default,
        console=console,
    )
    try:
        new_params = float(param_str) if param_str else None
    except ValueError:
        new_params = card.parameters

    # Edit description
    new_desc = Prompt.ask(
        "Description",
        default=card.description,
        console=console,
    )

    # Create updated card
    updated_card = ModelCard(
        id=card.id,
        name=new_name,
        model_type=card.model_type,
        provider=card.provider,
        description=new_desc,
        capabilities=card.capabilities,
        hardware=card.hardware,
        strengths=card.strengths,
        weaknesses=card.weaknesses,
        limitations=card.limitations,
        use_cases=card.use_cases,
        context_length=new_context,
        parameters=new_params,
        licence=card.licence,
        metadata=card.metadata,
    )

    console.print()
    save = Prompt.ask(
        "Save edited card?",
        choices=["y", "n"],
        default="y",
        console=console,
    )

    if save.lower() == "y":
        return updated_card
    return None


def display_card_summary(
    card: ModelCard,
    console: Console,
    is_cached: bool = False,
) -> None:
    """Display a brief card summary.

    Args:
        card: ModelCard to display
        console: Rich console
        is_cached: Whether this is a cached (unconfirmed) card
    """
    from rich.text import Text

    status = "[dim](cached)[/dim]" if is_cached else ""

    text = Text()
    text.append(f"{card.id} ", style="bold")
    text.append(f"({card.model_type.value}) ", style="dim")

    if card.parameters:
        text.append(f"{card.parameters}B ", style="cyan")

    if card.context_length:
        text.append(f"{card.context_length // 1000}K ctx ", style="green")

    if is_cached:
        text.append("(cached)", style="yellow")

    console.print(text)
