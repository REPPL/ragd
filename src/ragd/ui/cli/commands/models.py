"""Models CLI commands for ragd.

This module contains commands for managing LLM models and model cards.
"""

from __future__ import annotations

import typer

from ragd.ui import OutputFormat
from ragd.ui.cli.utils import get_console


def models_list_command(
    output_format: OutputFormat = "rich",
    no_color: bool = False,
) -> None:
    """List models by purpose and show Ollama availability.

    Shows configured models for each purpose (chat, summary, etc.)
    and available Ollama models grouped by type.
    """
    from ragd.config import load_config
    from ragd.llm import ModelRegistry, OllamaClient
    from ragd.models.cards import ModelType, infer_model_type

    con = get_console(no_color)
    config = load_config()

    # Get installed Ollama models
    ollama_models: list = []
    ollama_available = True
    try:
        client = OllamaClient(base_url=config.llm.base_url, model=config.llm.model)
        registry = ModelRegistry(client)
        ollama_models = registry.list_available(refresh=True)
    except Exception:
        ollama_available = False

    installed_names = {m.name for m in ollama_models}

    # Define purposes and their config locations
    purposes = {
        "Chat": config.llm.model,
        "Summary": config.metadata.summary_model,
        "Classification": config.metadata.classification_model,
        "Embedding": config.embedding.model,
        "Contextual": config.retrieval.contextual.model,
    }

    if output_format == "json":
        import json

        # Group Ollama models by type
        models_by_type: dict[str, list[dict]] = {}
        for m in ollama_models:
            mt = infer_model_type(m.name)
            if mt.value not in models_by_type:
                models_by_type[mt.value] = []
            models_by_type[mt.value].append({
                "name": m.name,
                "size_bytes": m.size_bytes,
                "size_display": m.display_size,
                "parameters": m.parameters,
                "quantisation": m.quantisation,
            })

        data = {
            "configured_models": purposes,
            "ollama_available": ollama_available,
            "ollama_url": config.llm.base_url,
            "installed_models": models_by_type,
        }
        con.print(json.dumps(data, indent=2))
        return

    # Rich output
    from rich.table import Table

    # Purpose table - show configured models
    purpose_table = Table(title="Configured Models by Purpose")
    purpose_table.add_column("Purpose", style="cyan")
    purpose_table.add_column("Model")
    purpose_table.add_column("Status")

    for purpose, model in purposes.items():
        # Check if installed
        is_embedding = purpose == "Embedding"
        if is_embedding:
            # Embedding models are local (sentence-transformers)
            status = "[dim]Local[/dim]"
        elif model in installed_names:
            status = "[green]✓ Installed[/green]"
        elif any(m.startswith(model.split(":")[0]) for m in installed_names):
            # Partial match (e.g., "llama3.2" matches "llama3.2:3b")
            status = "[green]✓ Installed[/green]"
        elif not ollama_available:
            status = "[yellow]? Ollama offline[/yellow]"
        else:
            status = "[red]✗ Not installed[/red]"

        purpose_table.add_row(purpose, model, status)

    con.print(purpose_table)

    # Ollama models table (grouped by type)
    if ollama_models:
        con.print()

        # Group by type
        by_type: dict[ModelType, list] = {}
        for m in ollama_models:
            mt = infer_model_type(m.name)
            if mt not in by_type:
                by_type[mt] = []
            by_type[mt].append(m)

        ollama_table = Table(title="Available Ollama Models")
        ollama_table.add_column("Model", style="cyan")
        ollama_table.add_column("Type")
        ollama_table.add_column("Size", justify="right")
        ollama_table.add_column("Parameters")

        # Order: LLM, Embedding, Vision, Reranker
        type_order = [ModelType.LLM, ModelType.EMBEDDING, ModelType.VISION, ModelType.RERANKER]
        for mt in type_order:
            for m in sorted(by_type.get(mt, []), key=lambda x: x.name):
                ollama_table.add_row(
                    m.name,
                    mt.value.capitalize(),
                    m.display_size,
                    m.parameters or "-",
                )

        con.print(ollama_table)
        con.print(f"\n[dim]Ollama URL: {config.llm.base_url}[/dim]")

    elif not ollama_available:
        con.print("\n[yellow]Ollama not available. Start with: ollama serve[/yellow]")
    else:
        con.print("\n[yellow]No Ollama models installed.[/yellow]")
        con.print("Pull a model: [cyan]ollama pull llama3.2:3b[/cyan]")


def models_set_command(
    chat: str | None = None,
    summary: str | None = None,
    classification: str | None = None,
    embedding: str | None = None,
    contextual: str | None = None,
    no_validate: bool = False,
    no_color: bool = False,
) -> None:
    """Set models for specific purposes.

    Updates the configuration file with the specified model assignments.
    Validates that Ollama models are installed (unless --no-validate).
    """
    from ragd.config import load_config, save_config
    from ragd.llm import OllamaClient

    con = get_console(no_color)
    config = load_config()

    # Track changes
    changes: list[str] = []

    # Get installed models for validation
    installed_models: set[str] = set()
    if not no_validate:
        try:
            client = OllamaClient(base_url=config.llm.base_url, model=config.llm.model)
            models = client.list_models()
            installed_models = set(models)
        except Exception:
            con.print("[yellow]Warning: Could not verify models (Ollama unavailable)[/yellow]")
            no_validate = True

    def validate_ollama_model(model: str, purpose: str) -> bool:
        """Validate model exists in Ollama."""
        if no_validate:
            return True
        if model in installed_models:
            return True
        # Check prefix match (e.g., "llama3.2" matches "llama3.2:3b")
        base = model.split(":")[0]
        if any(m.startswith(base) for m in installed_models):
            return True
        con.print(f"[red]Model '{model}' not installed in Ollama.[/red]")
        con.print(f"Install with: [cyan]ollama pull {model}[/cyan]")
        return False

    # Process each purpose
    if chat:
        if validate_ollama_model(chat, "chat"):
            config.llm.model = chat
            changes.append(f"Chat: {chat}")

    if summary:
        if validate_ollama_model(summary, "summary"):
            config.metadata.summary_model = summary
            changes.append(f"Summary: {summary}")

    if classification:
        if validate_ollama_model(classification, "classification"):
            config.metadata.classification_model = classification
            changes.append(f"Classification: {classification}")

    if embedding:
        # Embedding models are local (sentence-transformers), no Ollama validation
        config.embedding.model = embedding
        changes.append(f"Embedding: {embedding}")

    if contextual:
        if validate_ollama_model(contextual, "contextual"):
            config.retrieval.contextual.model = contextual
            changes.append(f"Contextual: {contextual}")

    if not changes:
        # No arguments - enter interactive mode
        import questionary

        # Step 1: Ask for purpose
        purposes = [
            questionary.Choice("Chat (main generation model)", value="chat"),
            questionary.Choice("Summary (document summarisation)", value="summary"),
            questionary.Choice("Classification (document type)", value="classification"),
            questionary.Choice("Embedding (vector embeddings)", value="embedding"),
            questionary.Choice("Contextual (retrieval augmentation)", value="contextual"),
        ]

        from ragd.ui.styles import get_prompt_style

        purpose = questionary.select(
            "Which model purpose?",
            choices=purposes,
            style=get_prompt_style(),
        ).ask()

        if not purpose:
            return  # User cancelled

        # Step 2: Select model
        if purpose == "embedding":
            con.print("[dim]Embedding models are local (sentence-transformers), not Ollama.[/dim]")
            con.print("[dim]Examples: all-mpnet-base-v2, all-MiniLM-L6-v2[/dim]")
            model = questionary.text(
                "Enter embedding model name:",
                style=get_prompt_style(),
            ).ask()
            if model:
                config.embedding.model = model
                changes.append(f"Embedding: {model}")
        else:
            if not installed_models:
                con.print("[red]No Ollama models found.[/red]")
                con.print("Install models first: [cyan]ollama pull llama3.2:3b[/cyan]")
                return

            model = questionary.select(
                f"Select {purpose} model:",
                choices=sorted(installed_models),
                style=get_prompt_style(),
            ).ask()

            if model:
                if purpose == "chat":
                    config.llm.model = model
                    changes.append(f"Chat: {model}")
                elif purpose == "summary":
                    config.metadata.summary_model = model
                    changes.append(f"Summary: {model}")
                elif purpose == "classification":
                    config.metadata.classification_model = model
                    changes.append(f"Classification: {model}")
                elif purpose == "contextual":
                    config.retrieval.contextual.model = model
                    changes.append(f"Contextual: {model}")

        if not changes:
            return  # User cancelled model selection

    # Save configuration
    save_config(config)

    con.print("[green]✓[/green] Model configuration updated:")
    for change in changes:
        con.print(f"  • {change}")


def models_recommend_command(
    use_case: str | None = None,
    model_type: str = "llm",
    require_installed: bool = True,
    output_format: OutputFormat = "rich",
    no_color: bool = False,
) -> None:
    """Recommend models based on hardware and use case.

    Shows optimal model recommendations based on detected hardware
    capabilities and specified use case requirements.
    """
    from rich.panel import Panel
    from rich.table import Table

    from ragd.models import (
        ModelRecommender,
        ModelType,
        UseCase,
    )

    con = get_console(no_color)

    # Parse model type
    try:
        mt = ModelType(model_type)
    except ValueError:
        con.print(f"[red]Unknown model type: {model_type}[/red]")
        con.print(f"Valid types: {', '.join(t.value for t in ModelType)}")
        raise typer.Exit(1)

    # Parse use case
    uc = None
    if use_case:
        try:
            uc = UseCase(use_case)
        except ValueError:
            con.print(f"[red]Unknown use case: {use_case}[/red]")
            con.print(f"Valid use cases: {', '.join(u.value for u in UseCase)}")
            raise typer.Exit(1)

    # Create recommender
    recommender = ModelRecommender()
    hw = recommender.hardware

    # Get recommendations
    recommendations = recommender.recommend(
        use_case=uc,
        model_type=mt,
        prefer_installed=require_installed,
        max_recommendations=5,
    )

    if output_format == "json":
        import json
        data = {
            "hardware": {
                "total_ram_gb": hw.total_ram_gb,
                "available_ram_gb": hw.available_ram_gb,
                "has_gpu": hw.has_gpu,
                "gpu_name": hw.gpu_name,
                "gpu_vram_gb": hw.gpu_vram_gb,
                "is_apple_silicon": hw.is_apple_silicon,
            },
            "recommendations": [
                {
                    "model_id": r.model_id,
                    "score": r.score,
                    "reasons": r.reasons,
                    "warnings": r.warnings,
                    "is_installed": r.is_installed,
                }
                for r in recommendations
            ],
        }
        con.print(json.dumps(data, indent=2))
        return

    # Rich output
    # Hardware panel
    hw_lines = [
        f"RAM: {hw.available_ram_gb:.1f} / {hw.total_ram_gb:.1f} GB",
        f"CPU Cores: {hw.cpu_cores}",
    ]
    if hw.has_gpu:
        hw_lines.append(f"GPU: {hw.gpu_name}")
        if hw.gpu_vram_gb:
            hw_lines.append(f"VRAM: {hw.gpu_vram_gb:.1f} GB")
    if hw.is_apple_silicon:
        hw_lines.append("Apple Silicon: Yes (MPS enabled)")

    con.print(Panel("\n".join(hw_lines), title="Detected Hardware", border_style="blue"))

    if not recommendations:
        con.print("\n[yellow]No model recommendations available.[/yellow]")
        if require_installed:
            con.print("Try with --all to see models that can be installed.")
        return

    # Recommendations table
    table = Table(title=f"Model Recommendations ({mt.value})")
    table.add_column("Model", style="cyan")
    table.add_column("Score", justify="center")
    table.add_column("Status")
    table.add_column("Reasons")

    for r in recommendations:
        score_color = "green" if r.score >= 0.7 else "yellow" if r.score >= 0.5 else "red"
        status = "[green]Installed[/green]" if r.is_installed else "[dim]Not installed[/dim]"

        reasons_text = "; ".join(r.reasons[:2])
        if r.warnings:
            reasons_text += f" [yellow]({r.warnings[0]})[/yellow]"

        table.add_row(
            r.model_id,
            f"[{score_color}]{r.score:.0%}[/{score_color}]",
            status,
            reasons_text,
        )

    con.print(table)

    # Show use cases if none specified
    if not use_case:
        con.print("\n[bold]Available use cases:[/bold]")
        for uc_item in UseCase:
            con.print(f"  --use-case {uc_item.value}")


def models_show_command(
    model_id: str,
    output_format: OutputFormat = "rich",
    no_color: bool = False,
) -> None:
    """Show detailed information about a model.

    Displays the model card with capabilities, hardware requirements,
    strengths, weaknesses, and limitations.
    """
    from rich.panel import Panel

    from ragd.models import get_installed_models, load_model_card

    con = get_console(no_color)

    card = load_model_card(model_id)
    if not card:
        con.print(f"[red]Model card not found: {model_id}[/red]")
        con.print("\nAvailable model cards:")
        from ragd.models import list_model_cards
        for c in list_model_cards():
            con.print(f"  {c.id}")
        raise typer.Exit(1)

    installed_models = get_installed_models()
    is_installed = model_id in installed_models or any(
        m.startswith(model_id.split(":")[0]) for m in installed_models
    )

    if output_format == "json":
        import json
        data = card.to_dict()
        data["is_installed"] = is_installed
        con.print(json.dumps(data, indent=2))
        return

    # Rich output
    # Header panel
    status = "[green]Installed[/green]" if is_installed else "[dim]Not installed[/dim]"
    header_text = f"{card.name}\n{card.description}\n\nType: {card.model_type.value} | Provider: {card.provider} | Status: {status}"
    con.print(Panel(header_text, title=f"Model: {card.id}", border_style="blue"))

    # Capabilities
    if card.capabilities:
        con.print("\n[bold]Capabilities:[/bold]")
        caps = ", ".join(c.value for c in card.capabilities)
        con.print(f"  {caps}")

    # Hardware requirements
    if card.hardware:
        con.print("\n[bold]Hardware Requirements:[/bold]")
        hw = card.hardware
        con.print(f"  RAM: {hw.min_ram_gb:.0f} GB min, {hw.recommended_ram_gb:.0f} GB recommended")
        if hw.min_vram_gb:
            con.print(f"  VRAM: {hw.min_vram_gb:.0f} GB min, {hw.recommended_vram_gb:.0f} GB recommended")
        inference = []
        if hw.cpu_inference:
            inference.append("CPU")
        if hw.mps_inference:
            inference.append("MPS")
        if hw.cuda_inference:
            inference.append("CUDA")
        con.print(f"  Inference: {', '.join(inference)}")

    # Strengths, Weaknesses, Limitations
    if card.strengths:
        con.print("\n[bold green]Strengths:[/bold green]")
        for s in card.strengths:
            con.print(f"  + {s}")

    if card.weaknesses:
        con.print("\n[bold yellow]Weaknesses:[/bold yellow]")
        for w in card.weaknesses:
            con.print(f"  - {w}")

    if card.limitations:
        con.print("\n[bold red]Limitations:[/bold red]")
        for lim in card.limitations:
            con.print(f"  ! {lim}")

    # Use cases
    if card.use_cases:
        con.print("\n[bold]Recommended Use Cases:[/bold]")
        for uc in card.use_cases:
            con.print(f"  * {uc}")

    # Additional info
    if card.context_length or card.parameters:
        con.print("\n[bold]Specifications:[/bold]")
        if card.context_length:
            con.print(f"  Context length: {card.context_length:,} tokens")
        if card.parameters:
            con.print(f"  Parameters: {card.parameters:.1f}B")
        if card.licence:
            con.print(f"  Licence: {card.licence}")


def models_discover_command(
    model_id: str,
    interactive: bool = True,
    force: bool = False,
    no_color: bool = False,
) -> None:
    """Discover and create a model card for a model.

    Fetches metadata from available sources (Ollama API, HuggingFace Hub,
    heuristics) and optionally prompts for confirmation before saving.

    Args:
        model_id: Model identifier (e.g., 'llama3.2:3b', 'qwen2.5:14b')
        interactive: Prompt for confirmation before saving (default: True)
        force: Overwrite existing card if present
        no_color: Disable colour output
    """
    from ragd.models import load_model_card
    from ragd.models.discovery import AutoDiscoveryService
    from ragd.models.discovery.connectivity import (
        is_internet_available,
        is_ollama_available,
    )

    con = get_console(no_color)

    # Check if card already exists (unless force)
    if not force:
        existing = load_model_card(model_id, auto_discover=False)
        if existing:
            con.print(f"[yellow]Model card already exists for {model_id}[/yellow]")
            con.print(f"Use [cyan]ragd models show {model_id}[/cyan] to view it")
            con.print("Use [cyan]--force[/cyan] to overwrite")
            raise typer.Exit(0)

    # Show connectivity status
    con.print(f"\n[bold]Discovering metadata for {model_id}...[/bold]\n")

    ollama_up = is_ollama_available()
    internet_up = is_internet_available()

    con.print(f"  Ollama:    {'[green]✓[/green]' if ollama_up else '[dim]✗ offline[/dim]'}")
    con.print(f"  Internet:  {'[green]✓[/green]' if internet_up else '[dim]✗ offline[/dim]'}")
    con.print()

    # Run discovery
    service = AutoDiscoveryService()

    try:
        card = service.discover(
            model_id,
            interactive=interactive,
            console=con if interactive else None,
        )
    except Exception as e:
        con.print(f"[red]Discovery failed: {e}[/red]")
        raise typer.Exit(1)

    if card:
        con.print()
        con.print(f"[green]✓[/green] Model card {'saved' if interactive else 'cached'} for {card.id}")

        # Show card location
        storage = service.get_storage()
        filename = card.id.replace(":", "-").replace("/", "-") + ".yaml"
        if interactive:
            card_path = storage.base_dir / filename
        else:
            card_path = storage.cache_dir / filename
        if card_path.exists():
            con.print(f"[dim]Location: {card_path}[/dim]")

        con.print(f"\nView with: [cyan]ragd models show {model_id}[/cyan]")
    else:
        con.print("[yellow]No model card created.[/yellow]")


def models_cards_command(
    show_all: bool = False,
    output_format: OutputFormat = "rich",
    no_color: bool = False,
) -> None:
    """List all available model cards.

    Shows bundled and user-confirmed cards by default.
    Use --all to also include cached (auto-discovered) cards.

    Args:
        show_all: Include cached (unconfirmed) cards
        output_format: Output format (rich, json, plain)
        no_color: Disable colour output
    """
    from ragd.models import list_model_cards
    from ragd.models.discovery.storage import UserCardStorage

    con = get_console(no_color)

    # Get bundled cards
    bundled_cards = list_model_cards()

    # Get user cards (list_cards returns list of (card, is_confirmed) tuples)
    storage = UserCardStorage()
    user_card_tuples = storage.list_cards(include_cache=show_all)

    # Track user card status
    user_cards_map: dict[str, tuple] = {}  # id -> (card, is_confirmed)
    for card, is_confirmed in user_card_tuples:
        user_cards_map[card.id] = (card, is_confirmed)

    user_ids = set(user_cards_map.keys())

    # Cards only in bundled (not overridden by user)
    bundled_only = [c for c in bundled_cards if c.id not in user_ids]

    # All cards combined
    all_cards = [t[0] for t in user_card_tuples] + bundled_only

    if output_format == "json":
        import json

        data = {
            "cards": [
                {
                    "id": c.id,
                    "name": c.name,
                    "type": c.model_type.value,
                    "source": (
                        "user" if c.id in user_ids and user_cards_map[c.id][1]
                        else "cached" if c.id in user_ids
                        else "bundled"
                    ),
                    "context_length": c.context_length,
                    "parameters": c.parameters,
                }
                for c in sorted(all_cards, key=lambda x: x.id)
            ],
            "count": len(all_cards),
        }
        con.print(json.dumps(data, indent=2))
        return

    # Rich output
    from rich.table import Table

    table = Table(title="Available Model Cards")
    table.add_column("Model ID", style="cyan")
    table.add_column("Type")
    table.add_column("Parameters")
    table.add_column("Context")
    table.add_column("Source")

    for card in sorted(all_cards, key=lambda x: x.id):
        if card.id in user_ids:
            is_confirmed = user_cards_map[card.id][1]
            source = "[green]User[/green]" if is_confirmed else "[yellow]Cached[/yellow]"
        else:
            source = "[dim]Bundled[/dim]"

        params = f"{card.parameters}B" if card.parameters else "-"
        ctx = f"{card.context_length // 1000}K" if card.context_length else "-"

        table.add_row(
            card.id,
            card.model_type.value,
            params,
            ctx,
            source,
        )

    con.print(table)
    con.print(f"\n[dim]Total: {len(all_cards)} cards[/dim]")

    if not show_all:
        con.print("[dim]Use --all to include cached (auto-discovered) cards[/dim]")


def models_card_edit_command(
    model_id: str,
    no_color: bool = False,
) -> None:
    """Edit an existing model card interactively.

    Opens the card for editing, allowing you to modify fields
    and save changes to user storage.

    Args:
        model_id: Model identifier to edit
        no_color: Disable colour output
    """
    from ragd.models import load_model_card
    from ragd.models.discovery.prompts import prompt_card_confirmation
    from ragd.models.discovery.storage import UserCardStorage

    con = get_console(no_color)

    # Load existing card
    card = load_model_card(model_id, auto_discover=False)
    if not card:
        con.print(f"[red]Model card not found: {model_id}[/red]")
        con.print(f"\nDiscover with: [cyan]ragd models discover {model_id}[/cyan]")
        raise typer.Exit(1)

    con.print(f"\n[bold]Editing model card: {model_id}[/bold]")

    # Use the confirmation prompt (which includes editing)
    edited_card = prompt_card_confirmation(card, con)

    if edited_card:
        # Save to user storage (confirmed)
        storage = UserCardStorage()
        path = storage.save_card(edited_card, confirmed=True)
        con.print()
        con.print(f"[green]✓[/green] Saved to {path}")
    else:
        con.print("\n[yellow]No changes saved.[/yellow]")


__all__ = [
    "models_list_command",
    "models_set_command",
    "models_recommend_command",
    "models_show_command",
    "models_discover_command",
    "models_cards_command",
    "models_card_edit_command",
]
