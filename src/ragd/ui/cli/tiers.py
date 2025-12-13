"""Data tier CLI commands for ragd.

This module provides CLI commands for data sensitivity tier management:
- tier set: Set document tier
- tier list: List documents by tier
- tier show: Show tier for a document
- tier summary: Show tier distribution
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from rich.table import Table

from ragd.config import load_config
from ragd.ui.styles import Icons


def _get_tier_manager(config_path: Path | None = None):
    """Get tier manager instance.

    Args:
        config_path: Optional path to config file.

    Returns:
        TierManager instance.
    """
    from ragd.metadata.store import MetadataStore
    from ragd.security.tiers import DataTier, TierConfig, TierManager

    config = load_config(config_path)

    # Create metadata store
    store = MetadataStore(config.metadata_db_path)

    # Get session manager if available
    session = None
    try:
        from ragd.security import SessionConfig, SessionManager
        from ragd.security.crypto import CryptoConfig

        session_config = SessionConfig(
            auto_lock_minutes=config.security.session.auto_lock_minutes,
            failed_attempts_lockout=config.security.session.failed_attempts_lockout,
            lockout_minutes=config.security.session.lockout_minutes,
            activity_resets_timer=config.security.session.activity_resets_timer,
        )

        crypto_config = CryptoConfig(
            memory_kb=config.security.encryption.kdf_memory_mb * 1024,
            iterations=config.security.encryption.kdf_iterations,
            parallelism=config.security.encryption.kdf_parallelism,
        )

        session = SessionManager(
            config.security_path,
            session_config,
            crypto_config,
        )
    except ImportError:
        pass  # Session not available

    # Build tier config
    tier_config = TierConfig(
        default_tier=DataTier.PERSONAL,
    )

    return TierManager(store, session, tier_config)


def tier_set_command(
    document_id: str,
    tier: str,
    no_color: bool = False,
) -> None:
    """Set the sensitivity tier for a document.

    Args:
        document_id: Document ID to update.
        tier: Tier name (public, personal, sensitive, critical).
        no_color: Disable coloured output.
    """
    from ragd.security.tiers import DataTier, get_tier_colour, get_tier_icon
    from ragd.ui.cli.commands import get_console

    con = get_console(no_color)

    # Parse tier
    try:
        data_tier = DataTier.from_string(tier)
    except ValueError as e:
        con.print(f"{Icons.ERROR} {e}")
        raise SystemExit(1)

    manager = _get_tier_manager()

    if manager.set_tier(document_id, data_tier):
        colour = get_tier_colour(data_tier)
        icon = get_tier_icon(data_tier)
        con.print(
            f"{Icons.OK} Set tier for [cyan]{document_id}[/cyan] to "
            f"[{colour}]{icon} {data_tier.value}[/{colour}]"
        )
    else:
        con.print(f"{Icons.ERROR} Document not found: {document_id}")
        raise SystemExit(1)


def tier_show_command(
    document_id: str,
    no_color: bool = False,
) -> None:
    """Show the sensitivity tier for a document.

    Args:
        document_id: Document ID to query.
        no_color: Disable coloured output.
    """
    from ragd.security.tiers import get_tier_colour, get_tier_icon
    from ragd.ui.cli.commands import get_console

    con = get_console(no_color)
    manager = _get_tier_manager()

    tier = manager.get_tier(document_id)
    colour = get_tier_colour(tier)
    icon = get_tier_icon(tier)

    con.print(
        f"[cyan]{document_id}[/cyan]: [{colour}]{icon} {tier.value}[/{colour}]"
    )
    con.print(f"[dim]{tier.description}[/dim]")


def tier_list_command(
    tier: str | None = None,
    output_format: Literal["rich", "plain", "json"] = "rich",
    no_color: bool = False,
) -> None:
    """List documents by tier.

    Args:
        tier: Filter by specific tier (optional).
        output_format: Output format.
        no_color: Disable coloured output.
    """
    import json as json_module

    from ragd.security.tiers import DataTier, get_tier_colour, get_tier_icon
    from ragd.ui.cli.commands import get_console

    con = get_console(no_color)
    manager = _get_tier_manager()

    # Filter by tier if specified
    if tier:
        try:
            filter_tier = DataTier.from_string(tier)
        except ValueError as e:
            con.print(f"{Icons.ERROR} {e}")
            raise SystemExit(1)

        doc_ids = manager.list_by_tier(filter_tier)

        if output_format == "json":
            result = {
                "tier": filter_tier.value,
                "count": len(doc_ids),
                "documents": doc_ids,
            }
            con.print(json_module.dumps(result, indent=2))
            return

        if not doc_ids:
            con.print(f"{Icons.INFO} No documents with tier '{filter_tier.value}'")
            return

        colour = get_tier_colour(filter_tier)
        icon = get_tier_icon(filter_tier)
        con.print(f"\n[{colour}]{icon} {filter_tier.value.upper()}[/{colour}] ({len(doc_ids)} documents)\n")

        for doc_id in doc_ids:
            con.print(f"  {doc_id}")
        con.print()

    else:
        # Show all tiers
        counts = manager.tier_counts()

        if output_format == "json":
            result = {
                "tiers": {t.value: {"count": c} for t, c in counts.items()},
                "total": sum(counts.values()),
            }
            con.print(json_module.dumps(result, indent=2))
            return

        table = Table(title="Documents by Tier", show_header=True)
        table.add_column("Tier", style="bold")
        table.add_column("Count", justify="right")
        table.add_column("Description", style="dim")

        for tier_enum in DataTier:
            count = counts[tier_enum]
            colour = get_tier_colour(tier_enum)
            icon = get_tier_icon(tier_enum)
            table.add_row(
                f"[{colour}]{icon} {tier_enum.value}[/{colour}]",
                str(count),
                tier_enum.description,
            )

        con.print()
        con.print(table)
        con.print()


def tier_summary_command(
    output_format: Literal["rich", "plain", "json"] = "rich",
    no_color: bool = False,
) -> None:
    """Show tier distribution summary.

    Args:
        output_format: Output format.
        no_color: Disable coloured output.
    """
    import json as json_module

    from ragd.security.tiers import DataTier, get_tier_colour, get_tier_icon
    from ragd.ui.cli.commands import get_console

    con = get_console(no_color)
    manager = _get_tier_manager()

    summary = manager.tier_summary()

    if output_format == "json":
        con.print(json_module.dumps(summary, indent=2))
        return

    total = summary["total_documents"]
    con.print(f"\n[bold]Tier Distribution[/bold] ({total} total documents)\n")

    # Create progress bar style display
    for tier_enum in DataTier:
        tier_data = summary["tiers"][tier_enum.value]
        count = tier_data["count"]
        pct = tier_data["percentage"]
        colour = get_tier_colour(tier_enum)
        icon = get_tier_icon(tier_enum)

        # Create a simple bar
        bar_width = 30
        filled = int(bar_width * pct / 100) if total > 0 else 0
        bar = "\u2588" * filled + "\u2591" * (bar_width - filled)

        con.print(
            f"  [{colour}]{icon} {tier_enum.value:10}[/{colour}] "
            f"[{colour}]{bar}[/{colour}] {count:4} ({pct:5.1f}%)"
        )

    con.print()


def tier_promote_command(
    document_id: str,
    no_color: bool = False,
) -> None:
    """Increase document sensitivity by one level.

    Args:
        document_id: Document ID to promote.
        no_color: Disable coloured output.
    """
    from ragd.security.tiers import get_tier_colour, get_tier_icon
    from ragd.ui.cli.commands import get_console

    con = get_console(no_color)
    manager = _get_tier_manager()

    old_tier = manager.get_tier(document_id)
    new_tier = manager.promote_tier(document_id)

    if new_tier is None:
        colour = get_tier_colour(old_tier)
        con.print(
            f"{Icons.INFO} Document already at maximum tier "
            f"([{colour}]{old_tier.value}[/{colour}])"
        )
        return

    old_colour = get_tier_colour(old_tier)
    new_colour = get_tier_colour(new_tier)
    new_icon = get_tier_icon(new_tier)

    con.print(
        f"{Icons.OK} Promoted [cyan]{document_id}[/cyan]: "
        f"[{old_colour}]{old_tier.value}[/{old_colour}] -> "
        f"[{new_colour}]{new_icon} {new_tier.value}[/{new_colour}]"
    )


def tier_demote_command(
    document_id: str,
    no_color: bool = False,
) -> None:
    """Decrease document sensitivity by one level.

    Args:
        document_id: Document ID to demote.
        no_color: Disable coloured output.
    """
    from ragd.security.tiers import get_tier_colour, get_tier_icon
    from ragd.ui.cli.commands import get_console

    con = get_console(no_color)
    manager = _get_tier_manager()

    old_tier = manager.get_tier(document_id)
    new_tier = manager.demote_tier(document_id)

    if new_tier is None:
        colour = get_tier_colour(old_tier)
        con.print(
            f"{Icons.INFO} Document already at minimum tier "
            f"([{colour}]{old_tier.value}[/{colour}])"
        )
        return

    old_colour = get_tier_colour(old_tier)
    new_colour = get_tier_colour(new_tier)
    new_icon = get_tier_icon(new_tier)

    con.print(
        f"{Icons.OK} Demoted [cyan]{document_id}[/cyan]: "
        f"[{old_colour}]{old_tier.value}[/{old_colour}] -> "
        f"[{new_colour}]{new_icon} {new_tier.value}[/{new_colour}]"
    )
