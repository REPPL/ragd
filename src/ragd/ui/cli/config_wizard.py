"""Interactive configuration wizard for ragd (F-088).

Provides a guided interface for configuring ragd without manual YAML editing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import questionary
from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt

from ragd.config import (
    RagdConfig,
    load_config,
    save_config,
)
from ragd.ui.styles import get_prompt_style, print_banner


def run_config_wizard(console: Console | None = None) -> None:
    """Run the interactive configuration wizard.

    Args:
        console: Rich console for output
    """
    con = console or Console()

    con.print()
    print_banner(
        con,
        "ragd Configuration",
        "Use arrow keys to navigate, Enter to select.",
    )

    # Load existing config
    config = load_config()

    # Menu choices
    menu_choices = [
        questionary.Choice("Model settings", value="models"),
        questionary.Choice("Search behaviour", value="search"),
        questionary.Choice("Storage settings", value="storage"),
        questionary.Choice("Security options", value="security"),
        questionary.Choice("Agentic RAG settings", value="agentic"),
        questionary.Choice("Advanced tuning", value="advanced"),
        questionary.Choice("Prompt templates", value="prompts"),
        questionary.Separator(),
        questionary.Choice("Show current config", value="show"),
        questionary.Choice("Save and exit", value="save"),
        questionary.Choice("Exit without saving", value="exit"),
    ]

    # Main menu
    while True:
        con.print()
        choice = questionary.select(
            "What would you like to configure?",
            choices=menu_choices,
            style=get_prompt_style(),
        ).ask()

        if choice is None or choice == "exit":
            if questionary.confirm("Discard changes?", default=False, style=get_prompt_style()).ask():
                con.print("[yellow]Changes discarded.[/yellow]")
                break
        elif choice == "models":
            config = _configure_models(config, con)
        elif choice == "search":
            config = _configure_search(config, con)
        elif choice == "storage":
            config = _configure_storage(config, con)
        elif choice == "security":
            config = _configure_security(config, con)
        elif choice == "agentic":
            config = _configure_agentic(config, con)
        elif choice == "advanced":
            config = _configure_advanced(config, con)
        elif choice == "prompts":
            _configure_prompts(config, con)
        elif choice == "show":
            _show_config(config, con)
        elif choice == "save":
            save_config(config)
            con.print("\n[green]✓[/green] Configuration saved!")
            break


def _configure_models(config: RagdConfig, console: Console) -> RagdConfig:
    """Configure model settings."""
    console.print("\n[bold]Model Settings[/bold]\n")

    # Embedding model
    console.print(f"Current embedding model: [cyan]{config.embedding.model}[/cyan]")
    new_model = questionary.text(
        "Embedding model:",
        default=config.embedding.model,
        style=get_prompt_style(),
    ).ask()
    if new_model and new_model != config.embedding.model:
        config.embedding.model = new_model

    # LLM provider
    console.print(f"\nCurrent LLM provider: [cyan]{config.llm.provider}[/cyan]")
    providers = [
        questionary.Choice("ollama", value="ollama"),
        questionary.Choice("openai", value="openai"),
        questionary.Choice("anthropic", value="anthropic"),
    ]
    new_provider = questionary.select(
        "LLM provider:",
        choices=providers,
        default=config.llm.provider,
        style=get_prompt_style(),
    ).ask()
    if new_provider and new_provider != config.llm.provider:
        config.llm.provider = new_provider

    # LLM model
    console.print(f"\nCurrent LLM model: [cyan]{config.llm.model}[/cyan]")
    new_llm = questionary.text(
        "LLM model:",
        default=config.llm.model,
        style=get_prompt_style(),
    ).ask()
    if new_llm and new_llm != config.llm.model:
        config.llm.model = new_llm

    console.print("\n[green]✓[/green] Model settings updated")
    return config


def _configure_search(config: RagdConfig, console: Console) -> RagdConfig:
    """Configure search behaviour."""
    console.print("\n[bold]Search Behaviour[/bold]\n")

    # Search mode
    console.print(f"Current search mode: [cyan]{config.search.mode}[/cyan]")
    modes = [
        questionary.Choice("hybrid (semantic + keyword)", value="hybrid"),
        questionary.Choice("semantic (embeddings only)", value="semantic"),
        questionary.Choice("keyword (BM25 only)", value="keyword"),
    ]
    new_mode = questionary.select(
        "Search mode:",
        choices=modes,
        default=config.search.mode,
        style=get_prompt_style(),
    ).ask()
    if new_mode and new_mode != config.search.mode:
        config.search.mode = new_mode

    # Semantic weight (only for hybrid)
    if config.search.mode == "hybrid":
        console.print(f"\nCurrent semantic weight: [cyan]{config.search.semantic_weight}[/cyan]")
        console.print("[dim]Higher = more semantic, lower = more keyword[/dim]")
        weight_str = questionary.text(
            "Semantic weight (0.0-1.0):",
            default=str(config.search.semantic_weight),
            style=get_prompt_style(),
        ).ask()
        if weight_str:
            try:
                weight = float(weight_str)
                if 0.0 <= weight <= 1.0:
                    config.search.semantic_weight = weight
                    config.search.keyword_weight = 1.0 - weight
            except ValueError:
                console.print("[red]Invalid weight, keeping current value[/red]")

    # Default limit
    console.print(f"\nCurrent default result limit: [cyan]{config.retrieval.default_limit}[/cyan]")
    new_limit = questionary.text(
        "Default result limit:",
        default=str(config.retrieval.default_limit),
        style=get_prompt_style(),
    ).ask()
    if new_limit:
        try:
            limit_int = int(new_limit)
            if limit_int != config.retrieval.default_limit:
                config.retrieval.default_limit = limit_int
        except ValueError:
            console.print("[red]Invalid limit, keeping current value[/red]")

    # Min score
    console.print(f"\nCurrent minimum score threshold: [cyan]{config.retrieval.min_score}[/cyan]")
    score_str = questionary.text(
        "Minimum score (0.0-1.0):",
        default=str(config.retrieval.min_score),
        style=get_prompt_style(),
    ).ask()
    if score_str:
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


def _configure_agentic(config: RagdConfig, console: Console) -> RagdConfig:
    """Configure agentic RAG settings (v1.0.5)."""
    console.print("\n[bold]Agentic RAG Settings[/bold]\n")
    console.print("[dim]These control CRAG and Self-RAG quality thresholds.[/dim]\n")

    params = config.agentic_params

    # Relevance threshold
    console.print(f"Relevance threshold: [cyan]{params.relevance_threshold}[/cyan]")
    console.print("[dim]Minimum score for context to be considered relevant (0.0-1.0)[/dim]")
    threshold_str = Prompt.ask(
        "Relevance threshold",
        default=str(params.relevance_threshold),
    )
    try:
        threshold = float(threshold_str)
        if 0.0 <= threshold <= 1.0:
            params.relevance_threshold = threshold
    except ValueError:
        console.print("[red]Invalid value, keeping current[/red]")

    # Faithfulness threshold
    console.print(f"\nFaithfulness threshold: [cyan]{params.faithfulness_threshold}[/cyan]")
    console.print("[dim]Minimum score for answer to be considered faithful (0.0-1.0)[/dim]")
    faith_str = Prompt.ask(
        "Faithfulness threshold",
        default=str(params.faithfulness_threshold),
    )
    try:
        faith = float(faith_str)
        if 0.0 <= faith <= 1.0:
            params.faithfulness_threshold = faith
    except ValueError:
        console.print("[red]Invalid value, keeping current[/red]")

    # Answer generation temperature
    answer_params = params.answer_generation
    console.print(f"\nAnswer generation temperature: [cyan]{answer_params.temperature}[/cyan]")
    console.print("[dim]Higher = more creative, lower = more focused (0.0-1.0)[/dim]")
    temp_str = Prompt.ask(
        "Answer temperature",
        default=str(answer_params.temperature or 0.7),
    )
    try:
        temp = float(temp_str)
        if 0.0 <= temp <= 1.0:
            answer_params.temperature = temp
    except ValueError:
        console.print("[red]Invalid value, keeping current[/red]")

    # Answer generation max tokens
    console.print(f"\nMax tokens for answer: [cyan]{answer_params.max_tokens}[/cyan]")
    new_tokens = IntPrompt.ask(
        "Max tokens",
        default=answer_params.max_tokens or 1024,
    )
    answer_params.max_tokens = max(100, min(4096, new_tokens))

    console.print("\n[green]✓[/green] Agentic RAG settings updated")
    return config


def _configure_advanced(config: RagdConfig, console: Console) -> RagdConfig:
    """Configure advanced tuning parameters (v1.0.5)."""
    console.print("\n[bold]Advanced Tuning[/bold]\n")

    # Sub-menu with arrow key navigation
    choices = [
        questionary.Choice("Search tuning (BM25, RRF)", value="search"),
        questionary.Choice("Processing parameters", value="processing"),
        questionary.Choice("Hardware thresholds", value="hardware"),
        questionary.Separator(),
        questionary.Choice("Back to main menu", value="back"),
    ]

    choice = questionary.select(
        "Select category:",
        choices=choices,
        style=get_prompt_style(),
    ).ask()

    if choice == "search":
        config = _configure_search_tuning(config, console)
    elif choice == "processing":
        config = _configure_processing(config, console)
    elif choice == "hardware":
        config = _configure_hardware_thresholds(config, console)

    return config


def _configure_search_tuning(config: RagdConfig, console: Console) -> RagdConfig:
    """Configure search tuning parameters."""
    console.print("\n[bold]Search Tuning[/bold]\n")

    tuning = config.search_tuning

    # BM25 normalisation divisor
    console.print(f"BM25 normalisation divisor: [cyan]{tuning.bm25_normalisation_divisor}[/cyan]")
    console.print("[dim]Higher values reduce BM25 score range (default: 10.0)[/dim]")
    bm25_str = Prompt.ask(
        "BM25 divisor",
        default=str(tuning.bm25_normalisation_divisor),
    )
    try:
        bm25 = float(bm25_str)
        if bm25 > 0:
            tuning.bm25_normalisation_divisor = bm25
    except ValueError:
        console.print("[red]Invalid value, keeping current[/red]")

    # RRF fetch multiplier
    console.print(f"\nRRF fetch multiplier: [cyan]{tuning.rrf_fetch_multiplier}[/cyan]")
    console.print("[dim]How many more results to fetch for rank fusion (default: 3)[/dim]")
    rrf = IntPrompt.ask(
        "RRF multiplier",
        default=tuning.rrf_fetch_multiplier,
    )
    tuning.rrf_fetch_multiplier = max(1, min(10, rrf))

    # Position decay factor
    console.print(f"\nPosition decay factor: [cyan]{tuning.position_decay_factor}[/cyan]")
    console.print("[dim]Decay rate for relevance scores by position (0.0-1.0)[/dim]")
    decay_str = Prompt.ask(
        "Decay factor",
        default=str(tuning.position_decay_factor),
    )
    try:
        decay = float(decay_str)
        if 0.0 <= decay <= 1.0:
            tuning.position_decay_factor = decay
    except ValueError:
        console.print("[red]Invalid value, keeping current[/red]")

    console.print("\n[green]✓[/green] Search tuning updated")
    return config


def _configure_processing(config: RagdConfig, console: Console) -> RagdConfig:
    """Configure processing parameters."""
    console.print("\n[bold]Processing Parameters[/bold]\n")

    processing = config.processing

    # Context truncation
    console.print(f"Context truncation (chars): [cyan]{processing.context_truncation_chars}[/cyan]")
    console.print("[dim]Maximum characters for context in evaluation (default: 2000)[/dim]")
    trunc = IntPrompt.ask(
        "Context truncation",
        default=processing.context_truncation_chars,
    )
    processing.context_truncation_chars = max(500, min(10000, trunc))

    # Chars per token estimate
    console.print(f"\nChars per token estimate: [cyan]{processing.chars_per_token_estimate}[/cyan]")
    console.print("[dim]Approximate characters per token for estimation (default: 4)[/dim]")
    cpt = IntPrompt.ask(
        "Chars per token",
        default=processing.chars_per_token_estimate,
    )
    processing.chars_per_token_estimate = max(1, min(10, cpt))

    # Token encoding
    console.print(f"\nToken encoding: [cyan]{processing.token_encoding}[/cyan]")
    new_encoding = Prompt.ask(
        "Token encoding",
        default=processing.token_encoding,
    )
    processing.token_encoding = new_encoding

    console.print("\n[green]✓[/green] Processing parameters updated")
    return config


def _configure_hardware_thresholds(config: RagdConfig, console: Console) -> RagdConfig:
    """Configure hardware tier thresholds."""
    console.print("\n[bold]Hardware Tier Thresholds[/bold]\n")
    console.print("[dim]Memory thresholds for tier classification (GB).[/dim]\n")

    thresholds = config.hardware_thresholds

    # Minimal max
    console.print(f"Minimal tier max memory: [cyan]{thresholds.minimal_max_memory_gb}[/cyan] GB")
    console.print("[dim]Systems below this are MINIMAL tier (default: 8)[/dim]")
    minimal = IntPrompt.ask(
        "Minimal max GB",
        default=int(thresholds.minimal_max_memory_gb),
    )
    thresholds.minimal_max_memory_gb = max(4, minimal)

    # Standard max
    console.print(f"\nStandard tier max memory: [cyan]{thresholds.standard_max_memory_gb}[/cyan] GB")
    console.print("[dim]Systems below this are STANDARD tier (default: 16)[/dim]")
    standard = IntPrompt.ask(
        "Standard max GB",
        default=int(thresholds.standard_max_memory_gb),
    )
    thresholds.standard_max_memory_gb = max(thresholds.minimal_max_memory_gb + 1, standard)

    # High max
    console.print(f"\nHigh tier max memory: [cyan]{thresholds.high_max_memory_gb}[/cyan] GB")
    console.print("[dim]Systems below this are HIGH tier, above are EXTREME (default: 32)[/dim]")
    high = IntPrompt.ask(
        "High max GB",
        default=int(thresholds.high_max_memory_gb),
    )
    thresholds.high_max_memory_gb = max(thresholds.standard_max_memory_gb + 1, high)

    console.print("\n[green]✓[/green] Hardware thresholds updated")
    return config


def _configure_prompts(config: RagdConfig, console: Console) -> None:
    """Configure prompt templates (v1.0.5)."""
    from ragd.prompts import export_default_prompts, list_prompts
    from ragd.prompts.loader import DEFAULT_PROMPTS_DIR, get_custom_prompt_status

    console.print("\n[bold]Prompt Template Management[/bold]\n")

    # Sub-menu with arrow key navigation
    choices = [
        questionary.Choice("List all prompts", value="list"),
        questionary.Choice("Export prompts for customisation", value="export"),
        questionary.Choice("Show customisation status", value="status"),
        questionary.Choice("View prompt content", value="view"),
        questionary.Separator(),
        questionary.Choice("Back to main menu", value="back"),
    ]

    choice = questionary.select(
        "Select action:",
        choices=choices,
        style=get_prompt_style(),
    ).ask()

    if choice == "list":
        prompts = list_prompts()
        console.print("\n[bold]Available Prompts:[/bold]\n")
        for category, names in prompts.items():
            console.print(f"  [cyan]{category}[/cyan]:")
            for name in names:
                console.print(f"    - {name}")

    elif choice == "export":
        console.print(f"\n[dim]Prompts will be exported to: {DEFAULT_PROMPTS_DIR}[/dim]")
        if Confirm.ask("Export all default prompts?", default=True):
            exported = export_default_prompts(overwrite=False)
            if exported:
                console.print(f"\n[green]✓[/green] Exported {len(exported)} prompt files")
                console.print("[dim]Edit these files to customise prompt behaviour.[/dim]")
            else:
                console.print("[yellow]No files exported (all already exist).[/yellow]")
                if Confirm.ask("Overwrite existing files?", default=False):
                    exported = export_default_prompts(overwrite=True)
                    console.print(f"[green]✓[/green] Exported {len(exported)} prompt files")

    elif choice == "status":
        status = get_custom_prompt_status(config)
        console.print("\n[bold]Customisation Status:[/bold]\n")
        for category, prompts_status in status.items():
            console.print(f"  [cyan]{category}[/cyan]:")
            for name, stat in prompts_status.items():
                style = "green" if stat == "default" else "yellow"
                console.print(f"    - {name}: [{style}]{stat}[/{style}]")

    elif choice == "view":
        from ragd.prompts.defaults import DEFAULT_PROMPTS

        prompts = list_prompts()
        console.print("\nAvailable prompts:")
        for category, names in prompts.items():
            for name in names:
                console.print(f"  {category}/{name}")

        prompt_name = questionary.text(
            "Enter prompt name (category/name):",
            style=get_prompt_style(),
        ).ask()
        if prompt_name:
            parts = prompt_name.split("/")
            if len(parts) == 2 and parts[0] in DEFAULT_PROMPTS:
                category, name = parts
                if name in DEFAULT_PROMPTS[category]:
                    content = DEFAULT_PROMPTS[category][name]
                    console.print(f"\n[bold]{category}/{name}:[/bold]\n")
                    console.print(content)
                else:
                    console.print(f"[red]Unknown prompt: {name}[/red]")
            else:
                console.print("[red]Invalid format. Use category/name (e.g., rag/answer)[/red]")
