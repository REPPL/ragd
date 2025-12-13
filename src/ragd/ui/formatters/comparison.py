"""Model comparison output formatter (F-057).

Formats model comparison results for Rich terminal output.
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ragd.llm.comparator import ComparisonResult


def format_comparison(result: ComparisonResult, console: Console) -> None:
    """Format and print comparison result.

    Args:
        result: ComparisonResult to format
        console: Rich console for output
    """
    # Header panel
    header = Panel(
        f"[bold]Query:[/bold] {result.query}\n"
        f"[dim]Context: {len(result.context)} characters[/dim]",
        title="Model Comparison",
        border_style="blue",
    )
    console.print(header)
    console.print()

    # Response panels
    for resp in result.responses:
        if resp.error:
            panel = Panel(
                f"[red]Error: {resp.error}[/red]",
                title=f"[red]{resp.model}[/red]",
                border_style="red",
            )
        else:
            footer = f"Time: {resp.time_ms:,.0f}ms | Tokens: {resp.tokens}"
            panel = Panel(
                resp.response,
                title=f"[bold cyan]{resp.model}[/bold cyan]",
                subtitle=footer,
                border_style="cyan",
            )
        console.print(panel)
        console.print()

    # Judge evaluation
    if result.evaluation:
        _format_judge_evaluation(result, console)

    # Ensemble result
    if result.ensemble_winner:
        _format_ensemble_result(result, console)


def _format_judge_evaluation(result: ComparisonResult, console: Console) -> None:
    """Format judge evaluation section.

    Args:
        result: ComparisonResult with evaluation
        console: Rich console for output
    """
    eval = result.evaluation
    if not eval:
        return

    # Winner announcement
    winner_text = Text()
    if eval.winner == "A":
        winner_model = result.responses[0].model
        winner_text.append("Winner: ", style="bold")
        winner_text.append(winner_model, style="bold green")
    elif eval.winner == "B":
        winner_model = result.responses[1].model
        winner_text.append("Winner: ", style="bold")
        winner_text.append(winner_model, style="bold green")
    else:
        winner_text.append("Result: ", style="bold")
        winner_text.append("Tie", style="yellow")

    # Scores table
    scores_table = Table(show_header=True, header_style="bold")
    scores_table.add_column("Criterion")

    models = list(eval.scores.keys())
    for model in models:
        scores_table.add_column(model, justify="center")

    criteria = ["Accuracy", "Completeness", "Clarity", "Citations"]
    for criterion in criteria:
        row = [criterion]
        for model in models:
            score = eval.scores[model]
            value = getattr(score, criterion.lower())
            stars = _format_stars(value)
            row.append(stars)
        scores_table.add_row(*row)

    # Total row
    total_row = ["[bold]Total[/bold]"]
    for model in models:
        total = eval.scores[model].total
        total_row.append(f"[bold]{total}/20[/bold]")
    scores_table.add_row(*total_row)

    # Build content
    content = Text()
    content.append_text(winner_text)
    content.append("\n\n")

    panel = Panel(
        Group(
            winner_text,
            "",
            scores_table,
            "",
            Text(f"[dim]Reasoning:[/dim] {eval.reasoning}"),
        ),
        title=f"Judge Evaluation ({eval.judge_model})",
        subtitle=f"Evaluation time: {eval.time_ms:,.0f}ms",
        border_style="yellow",
    )
    console.print(panel)


def _format_ensemble_result(result: ComparisonResult, console: Console) -> None:
    """Format ensemble result section.

    Args:
        result: ComparisonResult with ensemble winner
        console: Rich console for output
    """
    winner_text = Text()
    winner_text.append("Winner: ", style="bold")
    winner_text.append(result.ensemble_winner or "None", style="bold green")
    winner_text.append(f"\nConfidence: {result.ensemble_confidence:.0%}")
    winner_text.append(f"\nVotes: {len(result.ensemble_votes)}")

    panel = Panel(
        winner_text,
        title="Ensemble Result",
        border_style="magenta",
    )
    console.print(panel)


def _format_stars(score: int) -> str:
    """Format score as stars.

    Args:
        score: Score 1-5

    Returns:
        Star string
    """
    filled = "★" * score
    empty = "☆" * (5 - score)
    return filled + empty


class Group:
    """Simple group of renderables for Rich."""

    def __init__(self, *renderables: object) -> None:
        self.renderables = renderables

    def __rich_console__(self, console: Console, options: object) -> object:
        for r in self.renderables:
            if r == "":
                yield Text()
            else:
                yield r


def print_comparison(result: ComparisonResult, no_color: bool = False) -> None:
    """Print comparison result to terminal.

    Args:
        result: ComparisonResult to print
        no_color: Disable colour output
    """
    console = Console(no_color=no_color)
    format_comparison(result, console)
