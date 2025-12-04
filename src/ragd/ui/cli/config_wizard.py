"""Interactive configuration wizard for ragd (F-088).

Provides a guided interface for configuring ragd without manual YAML editing.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt

from ragd.config import (
    DEFAULT_CONFIG_PATH,
    RagdConfig,
    load_config,
    save_config,
)


def run_config_wizard(console: Console | None = None) -> None:
    """Run the interactive configuration wizard.

    Args:
        console: Rich console for output
    """
    con = console or Console()

    con.print(Panel(
        "[bold]ragd Configuration Wizard[/bold]\n\n"
        "This wizard will help you configure ragd.\n"
        "Press Enter to keep current values.",
        title="Configuration",
        border_style="blue",
    ))

    # Load existing config
    config = load_config()

    # Main menu
    while True:
        con.print("\n[bold]What would you like to configure?[/bold]\n")
        con.print("  [1] Model settings")
        con.print("  [2] Search behaviour")
        con.print("  [3] Storage settings")
        con.print("  [4] Security options")
        con.print("  [5] Show current config")
        con.print("  [6] Save and exit")
        con.print("  [7] Exit without saving")

        choice = Prompt.ask("\nEnter choice", choices=["1", "2", "3", "4", "5", "6", "7"])

        if choice == "1":
            config = _configure_models(config, con)
        elif choice == "2":
            config = _configure_search(config, con)
        elif choice == "3":
            config = _configure_storage(config, con)
        elif choice == "4":
            config = _configure_security(config, con)
        elif choice == "5":
            _show_config(config, con)
        elif choice == "6":
            save_config(config)
            con.print("\n[green]✓[/green] Configuration saved!")
            break
        elif choice == "7":
            if Confirm.ask("Discard changes?", default=False):
                con.print("[yellow]Changes discarded.[/yellow]")
                break


def _configure_models(config: RagdConfig, console: Console) -> RagdConfig:
    """Configure model settings."""
    console.print("\n[bold]Model Settings[/bold]\n")

    # Embedding model
    console.print(f"Current embedding model: [cyan]{config.embedding.model}[/cyan]")
    new_model = Prompt.ask(
        "Embedding model",
        default=config.embedding.model,
    )
    if new_model != config.embedding.model:
        config.embedding.model = new_model

    # LLM provider
    console.print(f"\nCurrent LLM provider: [cyan]{config.llm.provider}[/cyan]")
    new_provider = Prompt.ask(
        "LLM provider",
        choices=["ollama", "openai", "anthropic"],
        default=config.llm.provider,
    )
    if new_provider != config.llm.provider:
        config.llm.provider = new_provider

    # LLM model
    console.print(f"\nCurrent LLM model: [cyan]{config.llm.model}[/cyan]")
    new_llm = Prompt.ask(
        "LLM model",
        default=config.llm.model,
    )
    if new_llm != config.llm.model:
        config.llm.model = new_llm

    console.print("\n[green]✓[/green] Model settings updated")
    return config


def _configure_search(config: RagdConfig, console: Console) -> RagdConfig:
    """Configure search behaviour."""
    console.print("\n[bold]Search Behaviour[/bold]\n")

    # Search mode
    console.print(f"Current search mode: [cyan]{config.search.mode}[/cyan]")
    new_mode = Prompt.ask(
        "Search mode",
        choices=["hybrid", "semantic", "keyword"],
        default=config.search.mode,
    )
    if new_mode != config.search.mode:
        config.search.mode = new_mode

    # Semantic weight (only for hybrid)
    if config.search.mode == "hybrid":
        console.print(f"\nCurrent semantic weight: [cyan]{config.search.semantic_weight}[/cyan]")
        console.print("[dim]Higher = more semantic, lower = more keyword[/dim]")
        weight_str = Prompt.ask(
            "Semantic weight (0.0-1.0)",
            default=str(config.search.semantic_weight),
        )
        try:
            weight = float(weight_str)
            if 0.0 <= weight <= 1.0:
                config.search.semantic_weight = weight
                config.search.keyword_weight = 1.0 - weight
        except ValueError:
            console.print("[red]Invalid weight, keeping current value[/red]")

    # Default limit
    console.print(f"\nCurrent default result limit: [cyan]{config.retrieval.default_limit}[/cyan]")
    new_limit = IntPrompt.ask(
        "Default result limit",
        default=config.retrieval.default_limit,
    )
    if new_limit != config.retrieval.default_limit:
        config.retrieval.default_limit = new_limit

    # Min score
    console.print(f"\nCurrent minimum score threshold: [cyan]{config.retrieval.min_score}[/cyan]")
    score_str = Prompt.ask(
        "Minimum score (0.0-1.0)",
        default=str(config.retrieval.min_score),
    )
    try:
        score = float(score_str)
        if 0.0 <= score <= 1.0:
            config.retrieval.min_score = score
    except ValueError:
        console.print("[red]Invalid score, keeping current value[/red]")

    console.print("\n[green]✓[/green] Search settings updated")
    return config


def _configure_storage(config: RagdConfig, console: Console) -> RagdConfig:
    """Configure storage settings."""
    console.print("\n[bold]Storage Settings[/bold]\n")

    # Data directory
    console.print(f"Current data directory: [cyan]{config.storage.data_dir}[/cyan]")
    new_dir = Prompt.ask(
        "Data directory",
        default=str(config.storage.data_dir),
    )
    if Path(new_dir) != config.storage.data_dir:
        config.storage.data_dir = Path(new_dir).expanduser()

    # Chunk size
    console.print(f"\nCurrent chunk size: [cyan]{config.chunking.chunk_size}[/cyan] tokens")
    new_size = IntPrompt.ask(
        "Chunk size (tokens)",
        default=config.chunking.chunk_size,
    )
    if new_size != config.chunking.chunk_size:
        config.chunking.chunk_size = max(100, min(4096, new_size))

    # Chunk overlap
    console.print(f"\nCurrent chunk overlap: [cyan]{config.chunking.overlap}[/cyan] tokens")
    new_overlap = IntPrompt.ask(
        "Chunk overlap (tokens)",
        default=config.chunking.overlap,
    )
    if new_overlap != config.chunking.overlap:
        config.chunking.overlap = max(0, min(config.chunking.chunk_size // 2, new_overlap))

    console.print("\n[green]✓[/green] Storage settings updated")
    return config


def _configure_security(config: RagdConfig, console: Console) -> RagdConfig:
    """Configure security options."""
    console.print("\n[bold]Security Options[/bold]\n")

    # Encryption
    console.print(f"Encryption enabled: [cyan]{config.security.encryption.enabled}[/cyan]")
    if not config.security.encryption.enabled:
        if Confirm.ask("Enable encryption?", default=False):
            config.security.encryption.enabled = True
            console.print("[yellow]Note: Run 'ragd init --encrypted' to set up encryption.[/yellow]")

    # Session timeout
    console.print(f"\nSession auto-lock (minutes): [cyan]{config.security.session.auto_lock_minutes}[/cyan]")
    console.print("[dim]0 = disabled[/dim]")
    new_timeout = IntPrompt.ask(
        "Auto-lock timeout (minutes)",
        default=config.security.session.auto_lock_minutes,
    )
    if new_timeout != config.security.session.auto_lock_minutes:
        config.security.session.auto_lock_minutes = max(0, new_timeout)

    # Deletion confirmation
    console.print(f"\nRequire deletion confirmation: [cyan]{config.security.deletion.require_confirmation}[/cyan]")
    new_confirm = Confirm.ask(
        "Require confirmation before deletion?",
        default=config.security.deletion.require_confirmation,
    )
    config.security.deletion.require_confirmation = new_confirm

    console.print("\n[green]✓[/green] Security settings updated")
    return config


def _show_config(config: RagdConfig, console: Console) -> None:
    """Display current configuration."""
    import yaml

    console.print("\n[bold]Current Configuration[/bold]\n")

    # Convert to dict for display
    data = config.model_dump()

    # Convert Path objects to strings
    def path_to_str(obj: Any) -> Any:
        if isinstance(obj, Path):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: path_to_str(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [path_to_str(v) for v in obj]
        return obj

    data = path_to_str(data)

    console.print(yaml.safe_dump(data, default_flow_style=False, sort_keys=False))
