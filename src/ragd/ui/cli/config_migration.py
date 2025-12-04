"""Configuration migration tools for ragd (F-096).

Handles version-aware configuration migration with backup and rollback.
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import yaml
from rich.console import Console

from ragd.config import DEFAULT_CONFIG_PATH


# Current config schema version
CURRENT_VERSION = 2

# Migration registry: version -> migration function
_migrations: dict[int, Callable[[dict], dict]] = {}


def register_migration(from_version: int) -> Callable[[Callable[[dict], dict]], Callable[[dict], dict]]:
    """Register a migration function.

    Args:
        from_version: Source version number

    Returns:
        Decorator function
    """
    def decorator(func: Callable[[dict], dict]) -> Callable[[dict], dict]:
        _migrations[from_version] = func
        return func
    return decorator


@register_migration(1)
def migrate_v1_to_v2(config: dict) -> dict:
    """Migrate configuration from v1 to v2.

    Changes:
    - Add version field if missing
    - Ensure contextual retrieval section exists
    - Add security.session options
    """
    config["version"] = 2

    # Ensure retrieval.contextual exists
    retrieval = config.setdefault("retrieval", {})
    retrieval.setdefault("contextual", {
        "enabled": False,
        "provider": "ollama",
        "model": "llama3.2:3b",
        "base_url": "http://localhost:11434",
        "timeout_seconds": 60,
        "batch_size": 10,
        "prompt_template": "",
    })

    # Ensure security.session exists
    security = config.setdefault("security", {})
    session = security.setdefault("session", {})
    session.setdefault("auto_lock_minutes", 5)
    session.setdefault("failed_attempts_lockout", 5)
    session.setdefault("lockout_minutes", 15)
    session.setdefault("activity_resets_timer", True)

    return config


def get_config_version(config: dict) -> int:
    """Get version from config dict.

    Args:
        config: Configuration dictionary

    Returns:
        Version number (1 if not present)
    """
    return config.get("version", 1)


def needs_migration(config_path: Path | None = None) -> tuple[bool, int, int]:
    """Check if configuration needs migration.

    Args:
        config_path: Path to config file

    Returns:
        Tuple of (needs_migration, current_version, target_version)
    """
    path = config_path or DEFAULT_CONFIG_PATH

    if not path.exists():
        return False, CURRENT_VERSION, CURRENT_VERSION

    with open(path) as f:
        config = yaml.safe_load(f) or {}

    current = get_config_version(config)
    return current < CURRENT_VERSION, current, CURRENT_VERSION


def create_backup(config_path: Path | None = None) -> Path:
    """Create backup of configuration file.

    Args:
        config_path: Path to config file

    Returns:
        Path to backup file
    """
    path = config_path or DEFAULT_CONFIG_PATH

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    # Create backup with version and timestamp
    with open(path) as f:
        config = yaml.safe_load(f) or {}

    version = get_config_version(config)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_suffix(f".v{version}.{timestamp}.backup")

    shutil.copy2(path, backup_path)
    return backup_path


def migrate_config(
    config_path: Path | None = None,
    dry_run: bool = False,
    console: Console | None = None,
) -> bool:
    """Migrate configuration to current version.

    Args:
        config_path: Path to config file
        dry_run: If True, show changes without applying
        console: Rich console for output

    Returns:
        True if migration was successful
    """
    path = config_path or DEFAULT_CONFIG_PATH
    con = console or Console()

    if not path.exists():
        con.print("[yellow]No configuration file found, nothing to migrate.[/yellow]")
        return True

    # Load current config
    with open(path) as f:
        config = yaml.safe_load(f) or {}

    current_version = get_config_version(config)

    if current_version >= CURRENT_VERSION:
        con.print(f"[green]✓[/green] Configuration is already at version {current_version}")
        return True

    con.print(f"Detected config version: [cyan]{current_version}[/cyan]")
    con.print(f"Current version: [cyan]{CURRENT_VERSION}[/cyan]")

    if dry_run:
        con.print("\n[yellow]Dry run - showing changes without applying[/yellow]\n")

    # Create backup (unless dry run)
    if not dry_run:
        backup_path = create_backup(path)
        con.print(f"Creating backup: [dim]{backup_path}[/dim]")

    # Apply migrations
    con.print("\nMigrating...")
    migrated = config.copy()

    for version in range(current_version, CURRENT_VERSION):
        migration = _migrations.get(version)
        if migration:
            con.print(f"  [dim]Applying v{version} -> v{version + 1} migration[/dim]")
            migrated = migration(migrated)
        else:
            con.print(f"  [yellow]Warning: No migration for v{version} -> v{version + 1}[/yellow]")
            migrated["version"] = version + 1

    # Show changes
    _show_changes(config, migrated, con)

    # Save (unless dry run)
    if not dry_run:
        with open(path, "w") as f:
            yaml.safe_dump(migrated, f, default_flow_style=False, sort_keys=False)
        con.print("\n[green]✓[/green] Migration complete!")
    else:
        con.print("\n[yellow]Dry run complete. Run without --dry-run to apply changes.[/yellow]")

    return True


def rollback_config(
    config_path: Path | None = None,
    console: Console | None = None,
) -> bool:
    """Rollback to most recent backup.

    Args:
        config_path: Path to config file
        console: Rich console for output

    Returns:
        True if rollback was successful
    """
    path = config_path or DEFAULT_CONFIG_PATH
    con = console or Console()

    # Find most recent backup
    backups = sorted(
        path.parent.glob(f"{path.name}.v*.backup"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not backups:
        con.print("[red]No backup files found.[/red]")
        return False

    backup = backups[0]
    con.print(f"Found backup: [dim]{backup}[/dim]")

    # Restore backup
    shutil.copy2(backup, path)
    con.print(f"[green]✓[/green] Restored configuration from {backup.name}")

    return True


def _show_changes(old: dict, new: dict, console: Console, path: str = "") -> None:
    """Show changes between old and new config."""
    all_keys = set(old.keys()) | set(new.keys())

    for key in sorted(all_keys):
        current_path = f"{path}.{key}" if path else key
        old_value = old.get(key)
        new_value = new.get(key)

        if key not in old:
            console.print(f"  [green]+ {current_path}[/green]")
        elif key not in new:
            console.print(f"  [red]- {current_path}[/red]")
        elif isinstance(old_value, dict) and isinstance(new_value, dict):
            _show_changes(old_value, new_value, console, current_path)
        elif old_value != new_value:
            console.print(f"  [yellow]~ {current_path}[/yellow]: {old_value} -> {new_value}")
