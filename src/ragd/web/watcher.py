"""Watch folder auto-indexing for ragd.

This module implements F-037: Watch Folder Auto-Indexing, enabling
automatic document indexing when files change.
"""

from __future__ import annotations

import json
import logging
import os
import signal
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

from ragd.features import DependencyError

logger = logging.getLogger(__name__)

# Check for watchdog
try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    FileSystemEventHandler = object  # type: ignore
    Observer = None  # type: ignore


# Default configuration
DEFAULT_PATTERNS = ["*.pdf", "*.md", "*.txt", "*.docx", "*.html", "*.htm"]
DEFAULT_EXCLUDES = ["**/node_modules/**", "**/.git/**", "**/venv/**", "**/__pycache__/**"]
DEFAULT_DEBOUNCE_SECONDS = 5
DEFAULT_MAX_FILE_SIZE_MB = 100


@dataclass
class WatchEvent:
    """Record of a watch event."""

    timestamp: datetime
    event_type: str  # created, modified, deleted, skipped
    path: str
    reason: str = ""


@dataclass
class WatchStatus:
    """Status information for watch daemon."""

    running: bool
    pid: int | None = None
    uptime_seconds: float = 0
    directories: list[str] = field(default_factory=list)
    files_indexed: int = 0
    recent_events: list[WatchEvent] = field(default_factory=list)
    queue_size: int = 0


@dataclass
class WatchConfig:
    """Configuration for file watching."""

    directories: list[Path] = field(default_factory=list)
    patterns: list[str] = field(default_factory=lambda: list(DEFAULT_PATTERNS))
    excludes: list[str] = field(default_factory=lambda: list(DEFAULT_EXCLUDES))
    debounce_seconds: float = DEFAULT_DEBOUNCE_SECONDS
    max_file_size_mb: int = DEFAULT_MAX_FILE_SIZE_MB
    recursive: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "directories": [str(d) for d in self.directories],
            "patterns": self.patterns,
            "excludes": self.excludes,
            "debounce_seconds": self.debounce_seconds,
            "max_file_size_mb": self.max_file_size_mb,
            "recursive": self.recursive,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WatchConfig:
        """Create from dictionary."""
        return cls(
            directories=[Path(d) for d in data.get("directories", [])],
            patterns=data.get("patterns", DEFAULT_PATTERNS),
            excludes=data.get("excludes", DEFAULT_EXCLUDES),
            debounce_seconds=data.get("debounce_seconds", DEFAULT_DEBOUNCE_SECONDS),
            max_file_size_mb=data.get("max_file_size_mb", DEFAULT_MAX_FILE_SIZE_MB),
            recursive=data.get("recursive", True),
        )


def should_index(
    path: str,
    patterns: list[str],
    excludes: list[str],
    max_size_bytes: int,
) -> tuple[bool, str]:
    """Check if file should be indexed.

    Args:
        path: File path to check
        patterns: Glob patterns for files to include
        excludes: Glob patterns for files to exclude
        max_size_bytes: Maximum file size in bytes

    Returns:
        Tuple of (should_index, reason_if_not)
    """
    file_path = Path(path)

    # Check if file exists
    if not file_path.exists():
        return False, "file not found"

    # Check if it's a file (not directory)
    if file_path.is_dir():
        return False, "is directory"

    # Check exclusions first
    path_str = str(file_path)
    for exclude in excludes:
        if fnmatch(path_str, exclude):
            return False, f"excluded by pattern: {exclude}"

    # Check file size
    try:
        size = file_path.stat().st_size
        if size > max_size_bytes:
            return False, f"file too large: {size / (1024 * 1024):.1f}MB"
    except OSError:
        return False, "cannot read file size"

    # Check if matches any pattern
    filename = file_path.name
    for pattern in patterns:
        if fnmatch(filename, pattern):
            return True, ""

    return False, "no matching pattern"


class IndexEventHandler(FileSystemEventHandler):
    """Handle file system events for indexing.

    Implements debouncing to avoid indexing files that are still
    being written or rapidly modified.
    """

    def __init__(
        self,
        config: WatchConfig,
        index_callback: Callable[[Path], bool],
        remove_callback: Callable[[Path], bool] | None = None,
    ) -> None:
        """Initialise the event handler.

        Args:
            config: Watch configuration
            index_callback: Function to call for indexing files
            remove_callback: Function to call when files are deleted
        """
        super().__init__()
        self._config = config
        self._index = index_callback
        self._remove = remove_callback
        self._pending: dict[str, float] = {}  # path -> timestamp
        self._lock = threading.Lock()
        self._events: list[WatchEvent] = []
        self._max_events = 100  # Keep last N events
        self._indexed_count = 0
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    def pending_count(self) -> int:
        """Number of pending files."""
        with self._lock:
            return len(self._pending)

    @property
    def indexed_count(self) -> int:
        """Number of files indexed."""
        return self._indexed_count

    @property
    def recent_events(self) -> list[WatchEvent]:
        """Recent events."""
        with self._lock:
            return list(self._events)

    def on_created(self, event: Any) -> None:
        """Handle file creation."""
        if event.is_directory:
            return
        self._queue_index(event.src_path, "created")

    def on_modified(self, event: Any) -> None:
        """Handle file modification."""
        if event.is_directory:
            return
        self._queue_index(event.src_path, "modified")

    def on_deleted(self, event: Any) -> None:
        """Handle file deletion."""
        if event.is_directory:
            return
        self._handle_deleted(event.src_path)

    def on_moved(self, event: Any) -> None:
        """Handle file move/rename."""
        if event.is_directory:
            return
        # Treat as delete of old path, create of new path
        self._handle_deleted(event.src_path)
        self._queue_index(event.dest_path, "moved")

    def _queue_index(self, path: str, event_type: str) -> None:
        """Queue a file for indexing after debounce."""
        max_size = self._config.max_file_size_mb * 1024 * 1024
        should, reason = should_index(
            path,
            self._config.patterns,
            self._config.excludes,
            max_size,
        )

        if not should:
            self._add_event("skipped", path, reason)
            return

        with self._lock:
            self._pending[path] = time.time()

        self._logger.debug("Queued for indexing: %s (%s)", path, event_type)

    def _handle_deleted(self, path: str) -> None:
        """Handle file deletion."""
        # Remove from pending if present
        with self._lock:
            if path in self._pending:
                del self._pending[path]

        # Call remove callback if available
        if self._remove:
            try:
                self._remove(Path(path))
                self._add_event("deleted", path)
            except Exception as e:
                self._logger.error("Failed to remove %s: %s", path, e)

    def _add_event(self, event_type: str, path: str, reason: str = "") -> None:
        """Add event to history."""
        event = WatchEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            path=path,
            reason=reason,
        )
        with self._lock:
            self._events.append(event)
            if len(self._events) > self._max_events:
                self._events = self._events[-self._max_events :]

    def process_pending(self) -> int:
        """Process files that have been stable past debounce period.

        Returns:
            Number of files processed
        """
        now = time.time()
        ready: list[str] = []

        with self._lock:
            ready = [
                path
                for path, ts in self._pending.items()
                if now - ts >= self._config.debounce_seconds
            ]
            for path in ready:
                del self._pending[path]

        processed = 0
        for path in ready:
            try:
                file_path = Path(path)
                if file_path.exists():
                    success = self._index(file_path)
                    if success:
                        self._indexed_count += 1
                        self._add_event("indexed", path)
                        processed += 1
                    else:
                        self._add_event("skipped", path, "indexing failed")
            except Exception as e:
                self._logger.error("Failed to index %s: %s", path, e)
                self._add_event("skipped", path, str(e))

        return processed


class FolderWatcher:
    """Watch folders for changes and trigger indexing.

    Provides a high-level interface for the watch daemon functionality.

    Example:
        >>> watcher = FolderWatcher(config)
        >>> watcher.start()
        >>> # ... watcher runs in background
        >>> watcher.stop()
    """

    PID_FILE = Path.home() / ".ragd" / "watch.pid"
    STATUS_FILE = Path.home() / ".ragd" / "watch.status"

    def __init__(
        self,
        config: WatchConfig,
        index_callback: Callable[[Path], bool],
        remove_callback: Callable[[Path], bool] | None = None,
    ) -> None:
        """Initialise the watcher.

        Args:
            config: Watch configuration
            index_callback: Function to call for indexing
            remove_callback: Function to call when files are deleted

        Raises:
            DependencyError: If watchdog library not installed
        """
        if not WATCHDOG_AVAILABLE:
            raise DependencyError(
                "watchdog library required for folder watching",
                feature="watch",
                install_command="pip install watchdog",
            )

        self._config = config
        self._index = index_callback
        self._remove = remove_callback
        self._observer: Any = None
        self._handler: IndexEventHandler | None = None
        self._running = False
        self._start_time: float | None = None
        self._stop_event = threading.Event()
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def start(self, daemon: bool = False) -> None:
        """Start watching directories.

        Args:
            daemon: If True, fork and run as background daemon
        """
        if daemon:
            self._start_daemon()
        else:
            self._start_foreground()

    def _start_foreground(self) -> None:
        """Start watcher in foreground."""
        self._handler = IndexEventHandler(
            self._config,
            self._index,
            self._remove,
        )

        self._observer = Observer()
        for directory in self._config.directories:
            if directory.exists():
                self._observer.schedule(
                    self._handler,
                    str(directory),
                    recursive=self._config.recursive,
                )
                self._logger.info("Watching: %s", directory)
            else:
                self._logger.warning("Directory not found: %s", directory)

        self._observer.start()
        self._running = True
        self._start_time = time.time()

        # Save PID
        self.PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.PID_FILE.write_text(str(os.getpid()))

        self._logger.info("Watch started (PID %d)", os.getpid())

    def _start_daemon(self) -> None:
        """Start watcher as daemon process."""
        # This is a simplified version - proper daemonisation
        # would use python-daemon or similar
        self._start_foreground()

    def run(self) -> None:
        """Run the watcher loop (blocking).

        Call this after start() to run the main loop.
        """
        try:
            while self._running and not self._stop_event.is_set():
                # Process pending files
                if self._handler:
                    self._handler.process_pending()

                # Update status file
                self._write_status()

                # Sleep briefly
                self._stop_event.wait(timeout=1.0)

        except KeyboardInterrupt:
            self._logger.info("Interrupted")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop watching."""
        self._running = False
        self._stop_event.set()

        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5.0)

        # Clean up PID file
        if self.PID_FILE.exists():
            self.PID_FILE.unlink()

        self._logger.info("Watch stopped")

    def get_status(self) -> WatchStatus:
        """Get current watcher status."""
        uptime = 0.0
        if self._start_time:
            uptime = time.time() - self._start_time

        return WatchStatus(
            running=self._running,
            pid=os.getpid() if self._running else None,
            uptime_seconds=uptime,
            directories=[str(d) for d in self._config.directories],
            files_indexed=self._handler.indexed_count if self._handler else 0,
            recent_events=self._handler.recent_events if self._handler else [],
            queue_size=self._handler.pending_count if self._handler else 0,
        )

    def _write_status(self) -> None:
        """Write status to file."""
        try:
            status = self.get_status()
            data = {
                "running": status.running,
                "pid": status.pid,
                "uptime_seconds": status.uptime_seconds,
                "directories": status.directories,
                "files_indexed": status.files_indexed,
                "queue_size": status.queue_size,
                "recent_events": [
                    {
                        "timestamp": e.timestamp.isoformat(),
                        "event_type": e.event_type,
                        "path": e.path,
                        "reason": e.reason,
                    }
                    for e in status.recent_events[-10:]  # Last 10 events
                ],
                "updated_at": datetime.now().isoformat(),
            }

            self.STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.STATUS_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self._logger.debug("Failed to write status: %s", e)

    @classmethod
    def read_status(cls) -> WatchStatus | None:
        """Read status from file.

        Returns:
            WatchStatus if available, None otherwise
        """
        if not cls.STATUS_FILE.exists():
            return None

        try:
            with open(cls.STATUS_FILE) as f:
                data = json.load(f)

            return WatchStatus(
                running=data.get("running", False),
                pid=data.get("pid"),
                uptime_seconds=data.get("uptime_seconds", 0),
                directories=data.get("directories", []),
                files_indexed=data.get("files_indexed", 0),
                recent_events=[
                    WatchEvent(
                        timestamp=datetime.fromisoformat(e["timestamp"]),
                        event_type=e["event_type"],
                        path=e["path"],
                        reason=e.get("reason", ""),
                    )
                    for e in data.get("recent_events", [])
                ],
                queue_size=data.get("queue_size", 0),
            )
        except Exception:
            return None

    @classmethod
    def stop_daemon(cls) -> bool:
        """Stop a running daemon.

        Returns:
            True if daemon was stopped, False if not running
        """
        if not cls.PID_FILE.exists():
            return False

        try:
            pid = int(cls.PID_FILE.read_text())
            os.kill(pid, signal.SIGTERM)
            cls.PID_FILE.unlink()
            if cls.STATUS_FILE.exists():
                cls.STATUS_FILE.unlink()
            return True
        except ProcessLookupError:
            # Process not running, clean up stale files
            cls.PID_FILE.unlink()
            if cls.STATUS_FILE.exists():
                cls.STATUS_FILE.unlink()
            return False
        except Exception:
            return False

    @classmethod
    def is_running(cls) -> bool:
        """Check if daemon is running."""
        if not cls.PID_FILE.exists():
            return False

        try:
            pid = int(cls.PID_FILE.read_text())
            os.kill(pid, 0)  # Check if process exists
            return True
        except (ProcessLookupError, ValueError):
            return False
