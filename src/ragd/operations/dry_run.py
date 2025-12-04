"""Dry-run mode for ragd operations.

Allows previewing destructive operations without making changes:
- ragd index --dry-run
- ragd delete --dry-run
- ragd doctor --fix --dry-run
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class OperationType(Enum):
    """Types of operations that can be previewed."""

    INDEX = "index"
    DELETE = "delete"
    REPAIR = "repair"
    CLEAN = "clean"


class ActionType(Enum):
    """Types of actions within an operation."""

    ADD = "add"
    UPDATE = "update"
    REMOVE = "remove"
    SKIP = "skip"
    FIX = "fix"


@dataclass
class PlannedAction:
    """A single planned action within an operation.

    Represents what would happen to a specific target.
    """

    action: ActionType
    target: Path | str
    reason: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def icon(self) -> str:
        """Get icon for this action type."""
        icons = {
            ActionType.ADD: "+",
            ActionType.UPDATE: "~",
            ActionType.REMOVE: "-",
            ActionType.SKIP: "○",
            ActionType.FIX: "✓",
        }
        return icons.get(self.action, "?")

    @property
    def colour(self) -> str:
        """Get colour for this action type."""
        colours = {
            ActionType.ADD: "green",
            ActionType.UPDATE: "yellow",
            ActionType.REMOVE: "red",
            ActionType.SKIP: "dim",
            ActionType.FIX: "cyan",
        }
        return colours.get(self.action, "white")


@dataclass
class OperationPlan:
    """Plan for a dry-run operation.

    Collects all planned actions and provides display methods.
    """

    operation: OperationType
    actions: list[PlannedAction] = field(default_factory=list)
    source_path: Path | None = None

    def add_action(
        self,
        action: ActionType,
        target: Path | str,
        reason: str = "",
        **details: Any,
    ) -> None:
        """Add an action to the plan.

        Args:
            action: Type of action
            target: Target file/item
            reason: Why this action would happen
            **details: Additional details
        """
        self.actions.append(
            PlannedAction(
                action=action,
                target=target,
                reason=reason,
                details=details,
            )
        )

    @property
    def total(self) -> int:
        """Total number of actions."""
        return len(self.actions)

    @property
    def adds(self) -> int:
        """Number of add actions."""
        return sum(1 for a in self.actions if a.action == ActionType.ADD)

    @property
    def updates(self) -> int:
        """Number of update actions."""
        return sum(1 for a in self.actions if a.action == ActionType.UPDATE)

    @property
    def removes(self) -> int:
        """Number of remove actions."""
        return sum(1 for a in self.actions if a.action == ActionType.REMOVE)

    @property
    def skips(self) -> int:
        """Number of skip actions."""
        return sum(1 for a in self.actions if a.action == ActionType.SKIP)

    @property
    def fixes(self) -> int:
        """Number of fix actions."""
        return sum(1 for a in self.actions if a.action == ActionType.FIX)

    def get_by_type(self, action_type: ActionType) -> list[PlannedAction]:
        """Get actions of a specific type."""
        return [a for a in self.actions if a.action == action_type]


def display_plan(
    plan: OperationPlan,
    console: Console | None = None,
    max_items: int = 20,
    verbose: bool = False,
) -> None:
    """Display a dry-run operation plan.

    Args:
        plan: The operation plan to display
        console: Rich console for output
        max_items: Maximum items to show (use verbose for all)
        verbose: Show all items regardless of max_items
    """
    if console is None:
        console = Console()

    # Header
    console.print()
    console.print(
        f"[bold yellow][DRY RUN][/bold yellow] "
        f"Preview of {plan.operation.value} operation"
    )
    if plan.source_path:
        console.print(f"[dim]Source: {plan.source_path}[/dim]")
    console.print()

    if not plan.actions:
        console.print("[dim]No actions would be performed.[/dim]")
        return

    # Summary counts
    summary = Table(show_header=False, box=None, padding=(0, 2))
    summary.add_column("Action", style="dim")
    summary.add_column("Count")

    if plan.adds > 0:
        summary.add_row(
            Text("+ Would add", style="green"),
            str(plan.adds),
        )
    if plan.updates > 0:
        summary.add_row(
            Text("~ Would update", style="yellow"),
            str(plan.updates),
        )
    if plan.removes > 0:
        summary.add_row(
            Text("- Would remove", style="red"),
            str(plan.removes),
        )
    if plan.skips > 0:
        summary.add_row(
            Text("○ Would skip", style="dim"),
            str(plan.skips),
        )
    if plan.fixes > 0:
        summary.add_row(
            Text("✓ Would fix", style="cyan"),
            str(plan.fixes),
        )

    console.print(summary)
    console.print()

    # Detailed action list
    actions_to_show = plan.actions if verbose else plan.actions[:max_items]

    for action in actions_to_show:
        text = Text()
        text.append(f"  [{action.icon}] ", style=action.colour)
        text.append(str(action.target), style="white")
        if action.reason:
            text.append(f" ({action.reason})", style="dim")
        console.print(text)

    # Truncation notice
    remaining = len(plan.actions) - len(actions_to_show)
    if remaining > 0:
        console.print(
            f"\n[dim]... and {remaining} more. Use --verbose to see all.[/dim]"
        )

    # Footer
    console.print()
    console.print("[yellow]No changes made.[/yellow] Remove --dry-run to proceed.")


def create_index_plan(
    files: list[Path],
    existing_hashes: set[str] | None = None,
    console: Console | None = None,
) -> OperationPlan:
    """Create a dry-run plan for indexing.

    Args:
        files: Files to potentially index
        existing_hashes: Set of already-indexed content hashes
        console: Optional console for progress

    Returns:
        OperationPlan with planned actions
    """
    from ragd.storage.chromadb import generate_content_hash

    plan = OperationPlan(operation=OperationType.INDEX)

    for file_path in files:
        try:
            # Check if file is readable
            if not file_path.exists():
                plan.add_action(
                    ActionType.SKIP,
                    file_path,
                    reason="file not found",
                )
                continue

            if not file_path.is_file():
                plan.add_action(
                    ActionType.SKIP,
                    file_path,
                    reason="not a file",
                )
                continue

            # Check for duplicates if hashes provided
            if existing_hashes:
                try:
                    content = file_path.read_text(errors="ignore")
                    content_hash = generate_content_hash(content)
                    if content_hash in existing_hashes:
                        plan.add_action(
                            ActionType.SKIP,
                            file_path,
                            reason="already indexed",
                        )
                        continue
                except Exception:
                    pass  # Will try to index anyway

            # Would index this file
            plan.add_action(
                ActionType.ADD,
                file_path,
                reason="new file",
                file_size=file_path.stat().st_size,
            )

        except PermissionError:
            plan.add_action(
                ActionType.SKIP,
                file_path,
                reason="permission denied",
            )
        except Exception as e:
            plan.add_action(
                ActionType.SKIP,
                file_path,
                reason=str(e),
            )

    return plan


def create_delete_plan(
    document_ids: list[str],
    document_paths: dict[str, str],
) -> OperationPlan:
    """Create a dry-run plan for deletion.

    Args:
        document_ids: IDs of documents to delete
        document_paths: Mapping of ID to path

    Returns:
        OperationPlan with planned actions
    """
    plan = OperationPlan(operation=OperationType.DELETE)

    for doc_id in document_ids:
        path = document_paths.get(doc_id, doc_id)
        plan.add_action(
            ActionType.REMOVE,
            path,
            reason="marked for deletion",
            document_id=doc_id,
        )

    return plan


def create_repair_plan(
    issues: list[dict[str, Any]],
) -> OperationPlan:
    """Create a dry-run plan for doctor repairs.

    Args:
        issues: List of detected issues

    Returns:
        OperationPlan with planned actions
    """
    plan = OperationPlan(operation=OperationType.REPAIR)

    for issue in issues:
        issue_type = issue.get("type", "unknown")
        target = issue.get("target", "unknown")
        fixable = issue.get("fixable", False)

        if fixable:
            plan.add_action(
                ActionType.FIX,
                target,
                reason=issue_type,
            )
        else:
            plan.add_action(
                ActionType.SKIP,
                target,
                reason=f"{issue_type} (manual fix required)",
            )

    return plan
