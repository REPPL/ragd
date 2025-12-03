"""Security CLI commands for ragd.

This module provides CLI commands for encryption and session management:
- unlock: Unlock encrypted database
- lock: Lock session immediately
- password: Change password or rotate key
"""

from __future__ import annotations

import getpass
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ragd.config import load_config
from ragd.ui.styles import Icons


def _get_session_manager(config_path: Path | None = None):
    """Get or create session manager.

    Args:
        config_path: Optional path to config file.

    Returns:
        SessionManager instance.

    Raises:
        ImportError: If encryption dependencies not available.
    """
    from ragd.config import load_config
    from ragd.security import SessionManager, SessionConfig
    from ragd.security.crypto import CryptoConfig

    config = load_config(config_path)

    # Build session config from ragd config
    session_config = SessionConfig(
        auto_lock_minutes=config.security.session.auto_lock_minutes,
        failed_attempts_lockout=config.security.session.failed_attempts_lockout,
        lockout_minutes=config.security.session.lockout_minutes,
        activity_resets_timer=config.security.session.activity_resets_timer,
    )

    # Build crypto config from ragd config
    crypto_config = CryptoConfig(
        memory_kb=config.security.encryption.kdf_memory_mb * 1024,
        iterations=config.security.encryption.kdf_iterations,
        parallelism=config.security.encryption.kdf_parallelism,
    )

    return SessionManager(
        config.security_path,
        session_config,
        crypto_config,
    )


def _prompt_password(prompt: str = "Password: ", confirm: bool = False) -> str:
    """Prompt for password securely.

    Args:
        prompt: Prompt text.
        confirm: Whether to confirm password.

    Returns:
        Entered password.

    Raises:
        SystemExit: If passwords don't match or empty.
    """
    password = getpass.getpass(prompt)

    if not password:
        print("Error: Password cannot be empty", file=sys.stderr)
        raise SystemExit(1)

    if confirm:
        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            print("Error: Passwords do not match", file=sys.stderr)
            raise SystemExit(1)

    return password


def _format_time_remaining(seconds: int | None) -> str:
    """Format time remaining as human-readable string.

    Args:
        seconds: Seconds remaining, or None.

    Returns:
        Formatted string like "4:32" or "disabled".
    """
    if seconds is None:
        return "disabled"
    if seconds <= 0:
        return "0:00"

    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"


def unlock_command(
    no_color: bool = False,
    extend: bool = False,
) -> None:
    """Unlock encrypted database.

    Prompts for password and unlocks the session for the configured timeout.

    Args:
        no_color: Disable coloured output.
        extend: Extend existing session instead of new unlock.
    """
    from ragd.ui.cli.commands import get_console
    from ragd.security import (
        AuthenticationError,
        LockoutError,
        SessionError,
        SessionLockError,
    )

    con = get_console(no_color)

    try:
        manager = _get_session_manager()
    except ImportError as e:
        con.print(f"{Icons.ERROR} {e}")
        raise SystemExit(1)

    # Check if encryption is initialised
    if not manager.is_initialised:
        con.print(f"{Icons.ERROR} Encryption not initialised")
        con.print("[dim]Run 'ragd init' with encryption enabled first[/dim]")
        raise SystemExit(1)

    # Handle extend mode
    if extend:
        if manager.is_locked:
            con.print(f"{Icons.ERROR} Session is locked. Use 'ragd unlock' first.")
            raise SystemExit(1)
        manager.extend()
        status = manager.get_status()
        remaining = _format_time_remaining(status["time_remaining_seconds"])
        con.print(f"{Icons.OK} Session extended ({remaining} remaining)")
        return

    # Already unlocked?
    if manager.is_active:
        status = manager.get_status()
        remaining = _format_time_remaining(status["time_remaining_seconds"])
        con.print(f"{Icons.INFO} Session already unlocked ({remaining} remaining)")
        con.print("[dim]Use --extend to reset the timer[/dim]")
        return

    # Prompt for password
    try:
        password = _prompt_password("Enter password: ")
    except SystemExit:
        raise

    # Attempt unlock
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=con,
            transient=True,
        ) as progress:
            progress.add_task("Unlocking...", total=None)
            manager.unlock(password)

        status = manager.get_status()
        remaining = _format_time_remaining(status["time_remaining_seconds"])
        con.print(f"{Icons.OK} Session unlocked ({remaining} remaining)")

    except LockoutError as e:
        con.print(f"{Icons.ERROR} Account locked")
        con.print(f"[dim]{e}[/dim]")
        con.print("\n[dim]Use 'ragd password reset' to reset (WARNING: deletes all data)[/dim]")
        raise SystemExit(1)

    except AuthenticationError:
        con.print(f"{Icons.ERROR} Incorrect password")
        status = manager.get_status()
        attempts = status["failed_attempts"]
        if attempts > 0:
            con.print(f"[dim]Failed attempts: {attempts}[/dim]")
        raise SystemExit(1)

    except SessionError as e:
        con.print(f"{Icons.ERROR} {e}")
        raise SystemExit(1)


def lock_command(
    no_color: bool = False,
) -> None:
    """Lock session immediately.

    Clears encryption keys from memory.

    Args:
        no_color: Disable coloured output.
    """
    from ragd.ui.cli.commands import get_console

    con = get_console(no_color)

    try:
        manager = _get_session_manager()
    except ImportError as e:
        con.print(f"{Icons.ERROR} {e}")
        raise SystemExit(1)

    if not manager.is_initialised:
        con.print(f"{Icons.INFO} Encryption not initialised")
        return

    if manager.is_locked:
        con.print(f"{Icons.INFO} Session already locked")
        return

    manager.lock()
    con.print(f"{Icons.OK} Session locked")


def password_change_command(
    no_color: bool = False,
) -> None:
    """Change encryption password.

    Prompts for current password and new password.

    Args:
        no_color: Disable coloured output.
    """
    from ragd.ui.cli.commands import get_console
    from ragd.security import AuthenticationError, SessionError

    con = get_console(no_color)

    try:
        manager = _get_session_manager()
    except ImportError as e:
        con.print(f"{Icons.ERROR} {e}")
        raise SystemExit(1)

    if not manager.is_initialised:
        con.print(f"{Icons.ERROR} Encryption not initialised")
        raise SystemExit(1)

    # Prompt for passwords
    try:
        current_password = _prompt_password("Current password: ")
        new_password = _prompt_password("New password: ", confirm=True)
    except SystemExit:
        raise

    # Change password
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=con,
            transient=True,
        ) as progress:
            progress.add_task("Changing password...", total=None)
            manager.change_password(current_password, new_password)

        con.print(f"{Icons.OK} Password changed successfully")

    except AuthenticationError:
        con.print(f"{Icons.ERROR} Incorrect current password")
        raise SystemExit(1)

    except SessionError as e:
        con.print(f"{Icons.ERROR} {e}")
        raise SystemExit(1)


def password_reset_command(
    no_color: bool = False,
    confirm_data_loss: bool = False,
) -> None:
    """Reset encryption (WARNING: deletes all data).

    This is a destructive operation that removes all encryption keys.
    Any encrypted data will become permanently inaccessible.

    Args:
        no_color: Disable coloured output.
        confirm_data_loss: Must be True to proceed.
    """
    from ragd.ui.cli.commands import get_console
    import typer

    con = get_console(no_color)

    try:
        manager = _get_session_manager()
    except ImportError as e:
        con.print(f"{Icons.ERROR} {e}")
        raise SystemExit(1)

    if not manager.is_initialised:
        con.print(f"{Icons.INFO} Encryption not initialised - nothing to reset")
        return

    # Require explicit confirmation
    if not confirm_data_loss:
        con.print(Panel(
            "[bold red]WARNING: This will delete all encryption keys![/bold red]\n\n"
            "Any encrypted data will become PERMANENTLY INACCESSIBLE.\n"
            "This action cannot be undone.\n\n"
            "To proceed, run:\n"
            "  [cyan]ragd password reset --confirm-data-loss[/cyan]",
            title="Data Loss Warning",
            border_style="red",
        ))
        raise SystemExit(1)

    # Double-check with user
    if not typer.confirm("Are you SURE you want to delete all encryption keys?"):
        con.print("[yellow]Cancelled[/yellow]")
        raise SystemExit(0)

    manager.reset(confirm=True)
    con.print(f"{Icons.WARN} Encryption reset - all keys deleted")
    con.print("[dim]Run 'ragd init' to set up encryption again[/dim]")


def session_status_command(
    no_color: bool = False,
) -> None:
    """Show session status.

    Displays current session state, time remaining, and failed attempts.

    Args:
        no_color: Disable coloured output.
    """
    from ragd.ui.cli.commands import get_console

    con = get_console(no_color)

    try:
        manager = _get_session_manager()
    except ImportError as e:
        con.print(f"{Icons.ERROR} {e}")
        raise SystemExit(1)

    status = manager.get_status()

    # Format state
    if not status["is_initialised"]:
        state_icon = Icons.INFO
        state_text = "Not initialised"
    elif status["is_locked"]:
        state_icon = "[red][LOCKED][/red]"
        state_text = "Locked"
    else:
        state_icon = "[green][UNLOCKED][/green]"
        remaining = _format_time_remaining(status["time_remaining_seconds"])
        state_text = f"Unlocked ({remaining} remaining)"

    con.print(f"\n[bold]Session Status[/bold]")
    con.print(f"  {state_icon} {state_text}")

    if status["is_initialised"]:
        if status["failed_attempts"] > 0:
            con.print(f"  {Icons.WARN} Failed attempts: {status['failed_attempts']}")
        if status["is_locked_out"]:
            con.print(f"  {Icons.ERROR} Account is locked out")

    con.print()
