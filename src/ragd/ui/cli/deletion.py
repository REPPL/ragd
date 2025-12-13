"""Deletion CLI commands for ragd.

This module provides CLI commands for deleting documents:
- delete: Remove documents from the knowledge base
- With --secure: Secure deletion with overwrite
- With --purge: Cryptographic erasure with key rotation
"""

from __future__ import annotations

import getpass
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree

from ragd.config import load_config
from ragd.security.deletion import DeletionLevel, DeletionResult, SecureDeleter
from ragd.ui.styles import Icons


def _get_secure_deleter(config_path: Path | None = None) -> SecureDeleter:
    """Get secure deleter with configured stores.

    Args:
        config_path: Optional path to config file.

    Returns:
        SecureDeleter instance.
    """

    config = load_config(config_path)

    # Build audit log path
    audit_path = config.data_path / "audit" / "deletions.log"

    # Get deletion configuration
    enable_audit = config.security.deletion.audit_log

    return SecureDeleter(
        audit_log_path=audit_path,
        enable_audit=enable_audit,
    )


def _confirm_deletion(
    con: Console,
    document_ids: list[str],
    level: DeletionLevel,
    source: str | None = None,
) -> bool:
    """Prompt user to confirm deletion.

    Args:
        con: Console for output.
        document_ids: Documents to delete.
        level: Deletion level.
        source: Optional source path filter.

    Returns:
        True if user confirms.
    """
    import typer

    count = len(document_ids)

    if level == DeletionLevel.CRYPTOGRAPHIC:
        con.print(Panel(
            "[bold red]WARNING: PURGE MODE[/bold red]\n\n"
            "This will:\n"
            "  1. Permanently delete selected documents\n"
            "  2. Rotate the encryption key\n"
            "  3. Re-encrypt all remaining data\n\n"
            "[yellow]This cannot be undone.[/yellow]",
            title="Cryptographic Erasure",
            border_style="red",
        ))
        prompt = f"PURGE {count} document(s)?"
    elif level == DeletionLevel.SECURE:
        con.print("\n[yellow]Secure deletion[/yellow] will overwrite storage locations.")
        prompt = f"Securely delete {count} document(s)?"
    else:
        if source:
            prompt = f"Delete {count} document(s) from {source}?"
        else:
            prompt = f"Delete {count} document(s)?"

    return typer.confirm(prompt)


def _prompt_password(prompt: str = "Enter password to confirm: ") -> str:
    """Prompt for password securely.

    Args:
        prompt: Prompt text.

    Returns:
        Entered password.

    Raises:
        SystemExit: If empty password.
    """
    password = getpass.getpass(prompt)

    if not password:
        print("Error: Password cannot be empty", file=sys.stderr)
        raise SystemExit(1)

    return password


def delete_command(
    document_ids: list[str],
    secure: bool = False,
    purge: bool = False,
    source: str | None = None,
    force: bool = False,
    no_color: bool = False,
) -> None:
    """Delete documents from the knowledge base.

    Supports three deletion levels:
    - Standard: Remove from index (default)
    - Secure (--secure): Overwrite storage locations
    - Purge (--purge): Rotate encryption key

    Args:
        document_ids: Document IDs to delete.
        secure: Use secure deletion with overwrite.
        purge: Use cryptographic erasure with key rotation.
        source: Filter by source path.
        force: Skip confirmation prompt.
        no_color: Disable coloured output.
    """
    from ragd.ui.cli.commands import get_console

    con = get_console(no_color)

    # Determine deletion level
    if purge:
        level = DeletionLevel.CRYPTOGRAPHIC
    elif secure:
        level = DeletionLevel.SECURE
    else:
        level = DeletionLevel.STANDARD

    # Validate inputs
    if not document_ids:
        con.print(f"{Icons.ERROR} No documents specified")
        con.print("[dim]Use 'ragd list' to see available documents[/dim]")
        raise SystemExit(1)

    # Confirmation
    if not force:
        from ragd.config import load_config
        config = load_config()
        if config.security.deletion.require_confirmation:
            if not _confirm_deletion(con, document_ids, level, source):
                con.print("[yellow]Cancelled[/yellow]")
                raise SystemExit(0)

    # Password for cryptographic erasure
    password = None
    if level == DeletionLevel.CRYPTOGRAPHIC:
        password = _prompt_password()

    # Create deleter
    deleter = _get_secure_deleter()

    # Progress display
    if len(document_ids) == 1:
        # Single document deletion
        doc_id = document_ids[0]

        tree = Tree(f"[bold]Deleting {doc_id}[/bold]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=con,
            transient=True,
        ) as progress:
            task = progress.add_task("Deleting...", total=None)

            steps_completed = []

            def progress_callback(msg: str) -> None:
                progress.update(task, description=msg)
                steps_completed.append(msg)

            try:
                result = deleter.delete(
                    doc_id,
                    level=level,
                    password=password,
                    progress_callback=progress_callback,
                )

                # Build result tree
                for step in steps_completed[:-1]:  # Exclude "complete" message
                    tree.add(f"[dim]{step}[/dim] done")

                con.print(tree)
                _print_result(con, result)

            except Exception as e:
                con.print(f"{Icons.ERROR} Deletion failed: {e}")
                raise SystemExit(1)
    else:
        # Bulk deletion
        con.print(f"\n[bold]Deleting {len(document_ids)} documents...[/bold]\n")

        def bulk_progress(doc_id: str, current: int, total: int) -> None:
            con.print(f"  [{current}/{total}] {doc_id}...")

        try:
            results = deleter.bulk_delete(
                document_ids,
                level=level,
                password=password,
                progress_callback=bulk_progress,
            )

            # Summary
            successful = sum(1 for r in results if r.chunks_deleted >= 0)
            total_chunks = sum(r.chunks_deleted for r in results)

            con.print()
            con.print(f"{Icons.OK} Deleted {successful}/{len(document_ids)} documents")
            con.print(f"[dim]  Total chunks removed: {total_chunks}[/dim]")

            if any(r.key_rotated for r in results):
                con.print(f"{Icons.WARN} Encryption key rotated")

        except Exception as e:
            con.print(f"{Icons.ERROR} Bulk deletion failed: {e}")
            raise SystemExit(1)


def _print_result(con: Console, result: DeletionResult) -> None:
    """Print deletion result summary.

    Args:
        con: Console for output.
        result: Deletion result to display.
    """
    level_names = {
        DeletionLevel.STANDARD: "Removed from index",
        DeletionLevel.SECURE: "Securely deleted",
        DeletionLevel.CRYPTOGRAPHIC: "Purged with key rotation",
    }

    level_icons = {
        DeletionLevel.STANDARD: Icons.OK,
        DeletionLevel.SECURE: Icons.OK,
        DeletionLevel.CRYPTOGRAPHIC: Icons.WARN,
    }

    icon = level_icons.get(result.level, Icons.OK)
    name = level_names.get(result.level, "Deleted")

    con.print(f"\n{icon} {name}")

    if result.chunks_deleted > 0:
        con.print(f"[dim]  Chunks removed: {result.chunks_deleted}[/dim]")
    if result.vectors_deleted > 0:
        con.print(f"[dim]  Vectors removed: {result.vectors_deleted}[/dim]")
    if result.key_rotated:
        con.print("[dim]  Encryption key rotated[/dim]")
    if result.audit_logged:
        con.print("[dim]  Audit entry created[/dim]")


def delete_audit_command(
    show_all: bool = False,
    limit: int = 10,
    no_color: bool = False,
) -> None:
    """Show deletion audit log.

    Args:
        show_all: Show all entries (not just recent).
        limit: Maximum entries to show.
        no_color: Disable coloured output.
    """
    from rich.table import Table

    from ragd.ui.cli.commands import get_console

    con = get_console(no_color)
    deleter = _get_secure_deleter()

    entries = deleter.get_audit_log()

    if entries is None:
        con.print(f"{Icons.INFO} Audit logging is disabled")
        return

    if not entries:
        con.print(f"{Icons.INFO} No deletion records found")
        return

    # Limit entries unless showing all
    if not show_all and len(entries) > limit:
        entries = entries[-limit:]
        con.print(f"[dim]Showing last {limit} entries (use --all for full history)[/dim]\n")

    # Create table
    table = Table(title="Deletion Audit Log")
    table.add_column("Timestamp", style="dim")
    table.add_column("Document")
    table.add_column("Action")
    table.add_column("Chunks")
    table.add_column("Key Rotated")

    for entry in entries:
        action_style = {
            "delete": "white",
            "secure_delete": "yellow",
            "cryptographic_erase": "red",
        }.get(entry.action, "white")

        table.add_row(
            entry.timestamp.strftime("%Y-%m-%d %H:%M"),
            entry.document_id[:20] + "..." if len(entry.document_id) > 20 else entry.document_id,
            f"[{action_style}]{entry.action}[/{action_style}]",
            str(entry.chunks_removed),
            "Yes" if entry.key_rotated else "No",
        )

    con.print(table)
    con.print(f"\n[dim]Total entries: {deleter.get_audit_count()}[/dim]")
