"""Indexing checkpoint for resume capability (F-102).

Saves progress during large indexing operations for recovery.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_CHECKPOINT_FILE = Path.home() / ".ragd" / ".indexing_checkpoint.json"


@dataclass
class IndexingCheckpoint:
    """Checkpoint state for indexing operations."""

    started_at: str
    source_path: str
    total_files: int
    completed: int = 0
    last_file: str | None = None
    files_completed: list[str] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)

    @classmethod
    def create(cls, source_path: Path, total_files: int) -> IndexingCheckpoint:
        """Create new checkpoint.

        Args:
            source_path: Source directory being indexed
            total_files: Total files to process

        Returns:
            New checkpoint instance
        """
        return cls(
            started_at=datetime.now(UTC).isoformat(),
            source_path=str(source_path),
            total_files=total_files,
        )

    def mark_complete(self, file_path: str) -> None:
        """Mark a file as completed.

        Args:
            file_path: Path to completed file
        """
        self.completed += 1
        self.last_file = file_path
        self.files_completed.append(file_path)

    def mark_error(self, file_path: str, error: str) -> None:
        """Mark a file as failed.

        Args:
            file_path: Path to failed file
            error: Error message
        """
        self.errors.append({"file": file_path, "error": error})

    @property
    def is_complete(self) -> bool:
        """Check if indexing is complete."""
        return self.completed >= self.total_files

    @property
    def progress_percent(self) -> float:
        """Get completion percentage."""
        if self.total_files == 0:
            return 100.0
        return (self.completed / self.total_files) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IndexingCheckpoint:
        """Create from dictionary.

        Args:
            data: Checkpoint data

        Returns:
            Checkpoint instance
        """
        return cls(**data)


def save_checkpoint(
    checkpoint: IndexingCheckpoint,
    path: Path | None = None,
) -> None:
    """Save checkpoint to file.

    Args:
        checkpoint: Checkpoint to save
        path: Path to checkpoint file
    """
    checkpoint_path = path or DEFAULT_CHECKPOINT_FILE
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    with open(checkpoint_path, "w") as f:
        json.dump(checkpoint.to_dict(), f, indent=2)


def load_checkpoint(path: Path | None = None) -> IndexingCheckpoint | None:
    """Load checkpoint from file.

    Args:
        path: Path to checkpoint file

    Returns:
        Checkpoint if exists, None otherwise
    """
    checkpoint_path = path or DEFAULT_CHECKPOINT_FILE

    if not checkpoint_path.exists():
        return None

    with open(checkpoint_path) as f:
        data = json.load(f)

    return IndexingCheckpoint.from_dict(data)


def clear_checkpoint(path: Path | None = None) -> None:
    """Remove checkpoint file.

    Args:
        path: Path to checkpoint file
    """
    checkpoint_path = path or DEFAULT_CHECKPOINT_FILE

    if checkpoint_path.exists():
        checkpoint_path.unlink()


def get_remaining_files(
    checkpoint: IndexingCheckpoint,
    all_files: list[Path],
) -> list[Path]:
    """Get files not yet processed.

    Args:
        checkpoint: Current checkpoint
        all_files: All files to process

    Returns:
        Files not yet completed
    """
    completed_set = set(checkpoint.files_completed)
    return [f for f in all_files if str(f) not in completed_set]
