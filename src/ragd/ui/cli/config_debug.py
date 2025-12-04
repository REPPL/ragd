"""Configuration debugging tools for ragd (F-097).

Provides tools for inspecting effective configuration and diagnosing issues.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

from ragd.config import (
    DEFAULT_CONFIG_PATH,
    RagdConfig,
    create_default_config,
    load_config,
)


def show_effective_config(
    console: Console,
    format: str = "yaml",
) -> None:
    """Show effective configuration including defaults.

    Args:
        console: Rich console for output
        format: Output format (yaml, json)
    """
    config = load_config()
    data = _config_to_dict(config)

    if format == "json":
        console.print(json.dumps(data, indent=2, default=str))
    else:
        console.print(Panel("[bold]Effective Configuration[/bold]", border_style="blue"))
        console.print(Syntax(
            yaml.safe_dump(data, default_flow_style=False, sort_keys=False),
            "yaml",
            theme="monokai",
            line_numbers=False,
        ))


def show_config_diff(
    console: Console,
    format: str = "yaml",
) -> None:
    """Show only non-default configuration values.

    Args:
        console: Rich console for output
        format: Output format (yaml, json)
    """
    current = load_config()
    default = create_default_config()

    current_dict = _config_to_dict(current)
    default_dict = _config_to_dict(default)

    diff = _find_differences(current_dict, default_dict)

    if not diff:
        console.print("[dim]No configuration changes from defaults.[/dim]")
        return

    if format == "json":
        console.print(json.dumps(diff, indent=2, default=str))
    else:
        console.print(Panel("[bold]Non-Default Configuration[/bold]", border_style="yellow"))
        console.print(Syntax(
            yaml.safe_dump(diff, default_flow_style=False, sort_keys=False),
            "yaml",
            theme="monokai",
            line_numbers=False,
        ))


def show_config_source(console: Console) -> None:
    """Show where configuration values come from.

    Args:
        console: Rich console for output
    """
    config_path = DEFAULT_CONFIG_PATH

    table = Table(title="Configuration Sources")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Source", style="yellow")

    current = load_config()
    default = create_default_config()

    current_dict = _config_to_dict(current)
    default_dict = _config_to_dict(default)

    def add_rows(current: dict, default: dict, prefix: str = "") -> None:
        for key, value in current.items():
            full_key = f"{prefix}.{key}" if prefix else key
            default_value = default.get(key)

            if isinstance(value, dict) and isinstance(default_value, dict):
                add_rows(value, default_value, full_key)
            else:
                source = "default" if value == default_value else str(config_path)
                # Truncate long values
                display_value = str(value)
                if len(display_value) > 40:
                    display_value = display_value[:37] + "..."
                table.add_row(full_key, display_value, source)

    add_rows(current_dict, default_dict)
    console.print(table)


def validate_config(console: Console) -> bool:
    """Validate configuration and report issues.

    Args:
        console: Rich console for output

    Returns:
        True if configuration is valid, False otherwise
    """
    issues: list[tuple[str, str]] = []

    try:
        config = load_config()
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to load configuration: {e}")
        return False

    # Check data directory exists or is creatable
    if not config.storage.data_dir.exists():
        try:
            config.storage.data_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            issues.append(("storage.data_dir", f"Cannot create: {config.storage.data_dir}"))

    # Check embedding model
    if not config.embedding.model:
        issues.append(("embedding.model", "Embedding model not specified"))

    # Check LLM configuration
    if not config.llm.model:
        issues.append(("llm.model", "LLM model not specified"))

    # Check chunk size bounds
    if config.chunking.chunk_size < 100:
        issues.append(("chunking.chunk_size", "Chunk size too small (< 100)"))
    elif config.chunking.chunk_size > 4096:
        issues.append(("chunking.chunk_size", "Chunk size too large (> 4096)"))

    # Check overlap bounds
    if config.chunking.overlap >= config.chunking.chunk_size:
        issues.append(("chunking.overlap", "Overlap must be smaller than chunk size"))

    # Check search weights
    if config.search.mode == "hybrid":
        total_weight = config.search.semantic_weight + config.search.keyword_weight
        if abs(total_weight - 1.0) > 0.01:
            issues.append(("search", f"Weights should sum to 1.0, got {total_weight}"))

    # Report results
    if issues:
        console.print(Panel("[bold red]Configuration Issues[/bold red]", border_style="red"))
        for setting, issue in issues:
            console.print(f"  [red]✗[/red] [cyan]{setting}[/cyan]: {issue}")
        return False
    else:
        console.print("[green]✓[/green] Configuration is valid")
        return True


def _config_to_dict(config: RagdConfig) -> dict[str, Any]:
    """Convert config to serialisable dictionary."""
    data = config.model_dump()

    def convert(obj: Any) -> Any:
        if isinstance(obj, Path):
            return str(obj)
        elif hasattr(obj, "value"):  # Enum
            return obj.value
        elif isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(v) for v in obj]
        return obj

    return convert(data)


def _find_differences(current: dict, default: dict, path: str = "") -> dict:
    """Find differences between current and default config."""
    diff = {}

    for key, value in current.items():
        default_value = default.get(key)

        if isinstance(value, dict) and isinstance(default_value, dict):
            nested_diff = _find_differences(value, default_value, f"{path}.{key}")
            if nested_diff:
                diff[key] = nested_diff
        elif value != default_value:
            diff[key] = value

    return diff
