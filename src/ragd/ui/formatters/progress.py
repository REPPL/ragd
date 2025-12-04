"""Progress indicators for ragd CLI operations.

Provides Rich-based progress bars that adapt to terminal capabilities.
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from typing import Generator

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)


def is_interactive() -> bool:
    """Check if we're running in an interactive terminal.

    Returns:
        True if interactive (should show progress bars)
    """
    # Check for NO_COLOR environment variable
    if os.environ.get("NO_COLOR"):
        return False

    # Check if stdout is a TTY
    if not sys.stdout.isatty():
        return False

    # Check for CI environment
    if os.environ.get("CI"):
        return False

    return True


def create_progress(
    console: Console | None = None,
    quiet: bool = False,
    verbose: bool = False,
) -> Progress:
    """Create a Rich Progress instance with appropriate columns.

    Args:
        console: Optional Rich console (creates new if not provided)
        quiet: If True, disable all progress output
        verbose: If True, show additional detail columns

    Returns:
        Configured Progress instance
    """
    if console is None:
        console = Console()

    # Quiet mode - minimal progress
    if quiet:
        return Progress(
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
            disable=True,  # Completely disable
        )

    # Verbose mode - detailed progress
    if verbose:
        return Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=console,
            transient=False,
        )

    # Standard mode - balanced progress
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    )


class IndexingProgress:
    """Progress tracker for document indexing operations.

    Wraps Rich Progress with indexing-specific methods and
    automatic terminal detection.

    Usage:
        with IndexingProgress(total=10) as progress:
            for doc in documents:
                progress.update(doc.name)
                process(doc)
                progress.advance()
    """

    def __init__(
        self,
        total: int,
        console: Console | None = None,
        quiet: bool = False,
        verbose: bool = False,
    ) -> None:
        """Initialise indexing progress tracker.

        Args:
            total: Total number of documents to process
            console: Optional Rich console
            quiet: Suppress progress output
            verbose: Show detailed progress
        """
        self.total = total
        self.console = console or Console()
        self.quiet = quiet
        self.verbose = verbose
        self.current = 0
        self.current_file = ""

        # Disable if not interactive (unless verbose explicitly requested)
        self._enabled = is_interactive() and not quiet

        self._progress: Progress | None = None
        self._task_id: TaskID | None = None

    def __enter__(self) -> IndexingProgress:
        """Start the progress display."""
        if self._enabled:
            self._progress = create_progress(
                console=self.console,
                quiet=self.quiet,
                verbose=self.verbose,
            )
            self._progress.start()
            self._task_id = self._progress.add_task(
                "Indexing documents...",
                total=self.total,
            )
        return self

    def __exit__(self, *args: object) -> None:
        """Stop the progress display."""
        if self._progress is not None:
            self._progress.stop()
            self._progress = None

    def update(self, filename: str) -> None:
        """Update the current file being processed.

        Args:
            filename: Name of file being processed
        """
        self.current_file = filename
        if self._progress is not None and self._task_id is not None:
            self._progress.update(
                self._task_id,
                description=f"Indexing: {filename}",
            )

    def advance(self, amount: int = 1) -> None:
        """Advance progress by the given amount.

        Args:
            amount: Number of items completed
        """
        self.current += amount
        if self._progress is not None and self._task_id is not None:
            self._progress.update(self._task_id, advance=amount)

    def set_description(self, description: str) -> None:
        """Set the progress description.

        Args:
            description: New description text
        """
        if self._progress is not None and self._task_id is not None:
            self._progress.update(self._task_id, description=description)


@contextmanager
def indexing_progress(
    total: int,
    console: Console | None = None,
    quiet: bool = False,
    verbose: bool = False,
) -> Generator[IndexingProgress, None, None]:
    """Context manager for indexing progress.

    Args:
        total: Total documents to process
        console: Optional Rich console
        quiet: Suppress progress output
        verbose: Show detailed progress

    Yields:
        IndexingProgress instance
    """
    progress = IndexingProgress(
        total=total,
        console=console,
        quiet=quiet,
        verbose=verbose,
    )
    with progress:
        yield progress
