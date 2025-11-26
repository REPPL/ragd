# ADR-0014: Daemon Process Management

## Status

Accepted

## Context

The watch folder feature (F-037) requires a background process that:
- Monitors directories for file changes
- Survives terminal close
- Runs continuously without user interaction
- Can be started, stopped, and queried for status

This requires daemon process management - a notoriously platform-specific challenge with multiple approaches available.

## Decision

Use **PID file-based daemon management** with **SIGTERM graceful shutdown** for Unix systems (macOS, Linux). Windows support deferred to future implementation.

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   ragd watch daemon                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ~/.ragd/watch.pid ◄── PID file for status/control      │
│  ~/.ragd/watch.log ◄── Log file for debugging           │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐│
│  │              watchdog Observer                       ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ ││
│  │  │ ~/Documents │  │ ~/Projects  │  │ ~/Archives  │ ││
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ ││
│  │         │                │                │         ││
│  │         └────────────────┴────────────────┘         ││
│  │                          │                          ││
│  │                    Event Queue                      ││
│  │                          │                          ││
│  │                   Debounce (5s)                     ││
│  │                          │                          ││
│  │                   Index Pipeline                    ││
│  └─────────────────────────────────────────────────────┘│
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Daemon Lifecycle

**Start:**
```python
import os
import signal
from pathlib import Path

PID_FILE = Path.home() / ".ragd" / "watch.pid"
LOG_FILE = Path.home() / ".ragd" / "watch.log"

def start_daemon():
    """Start watch daemon in background."""
    if PID_FILE.exists():
        pid = int(PID_FILE.read_text())
        if _process_exists(pid):
            raise RuntimeError(f"Daemon already running (PID {pid})")
        PID_FILE.unlink()  # Clean up stale PID

    pid = os.fork()
    if pid > 0:
        # Parent: save PID and exit
        PID_FILE.write_text(str(pid))
        print(f"Watch daemon started (PID {pid})")
        return

    # Child: become daemon
    os.setsid()
    os.umask(0)

    # Redirect stdio
    with open(LOG_FILE, "a") as log:
        os.dup2(log.fileno(), 1)  # stdout
        os.dup2(log.fileno(), 2)  # stderr

    # Run watcher loop
    _run_watcher()
```

**Stop:**
```python
def stop_daemon():
    """Stop running watch daemon."""
    if not PID_FILE.exists():
        print("No watch daemon running")
        return

    pid = int(PID_FILE.read_text())
    try:
        os.kill(pid, signal.SIGTERM)
        PID_FILE.unlink()
        print(f"Watch daemon stopped (PID {pid})")
    except ProcessLookupError:
        PID_FILE.unlink()
        print("Daemon was not running (cleaned up stale PID)")
```

**Status:**
```python
def daemon_status() -> dict:
    """Get daemon status."""
    if not PID_FILE.exists():
        return {"running": False}

    pid = int(PID_FILE.read_text())
    if not _process_exists(pid):
        return {"running": False, "stale_pid": pid}

    return {
        "running": True,
        "pid": pid,
        "uptime": _get_process_uptime(pid),
        "directories": _get_watched_directories(),
    }
```

### Signal Handling

```python
import signal

def _run_watcher():
    """Main watcher loop with graceful shutdown."""
    shutdown_requested = False

    def handle_sigterm(signum, frame):
        nonlocal shutdown_requested
        shutdown_requested = True

    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)

    observer = Observer()
    handler = IndexEventHandler(indexer, debounce_seconds=5)

    for directory in config.watch.directories:
        observer.schedule(handler, directory, recursive=True)

    observer.start()

    try:
        while not shutdown_requested:
            handler.process_pending()
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()
        PID_FILE.unlink(missing_ok=True)
```

### CLI Interface

```bash
ragd watch ~/Documents ~/Projects   # Start watching directories
ragd watch --status                 # Show daemon status
ragd watch --stop                   # Stop daemon
ragd watch --logs                   # Tail log file
ragd watch --logs --follow          # Follow log output
```

### File System Events

Using the `watchdog` library:

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class IndexEventHandler(FileSystemEventHandler):
    def __init__(self, indexer, debounce_seconds=5):
        self.indexer = indexer
        self.debounce = debounce_seconds
        self.pending = {}  # path -> timestamp

    def on_created(self, event):
        if not event.is_directory:
            self._queue_index(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._queue_index(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self.indexer.remove(event.src_path)

    def _queue_index(self, path):
        if self._should_index(path):
            self.pending[path] = time.time()

    def process_pending(self):
        now = time.time()
        ready = [p for p, ts in self.pending.items()
                 if now - ts >= self.debounce]
        for path in ready:
            del self.pending[path]
            self.indexer.index(path)
```

## Consequences

### Positive

- Simple, proven Unix pattern
- No external dependencies (systemd, supervisor)
- Works on macOS and Linux
- Easy to debug (log file, PID file)
- Graceful shutdown preserves index integrity

### Negative

- Unix-only (`os.fork()` not available on Windows)
- Single daemon instance per system
- Manual log rotation needed
- No automatic restart on crash

### Windows Considerations (Future)

Windows support requires different approach:
- Windows Services API
- Or: `pythonw.exe` background process with Task Scheduler
- Or: Third-party like `pywin32` service wrapper

This is explicitly deferred to post-v0.2.

## Alternatives Considered

### systemd Service

- **Pros:** Auto-restart, logging, system integration
- **Cons:** Linux-only, requires root for install
- **Rejected:** Not portable to macOS

### supervisor/pm2

- **Pros:** Feature-rich, cross-platform
- **Cons:** External dependency, complex setup
- **Rejected:** Too heavy for personal tool

### In-Process Background Thread

- **Pros:** Simple, no daemon management
- **Cons:** Dies when CLI exits
- **Rejected:** Doesn't survive terminal close

### launchd (macOS) + systemd (Linux)

- **Pros:** Native, auto-restart, proper integration
- **Cons:** Platform-specific code, complex configuration
- **Rejected:** Maintenance burden for two systems

### Socket-Based IPC

- **Pros:** Rich status queries, remote control
- **Cons:** Complexity, port management
- **Rejected:** Overkill for single-user daemon

## Related Documentation

- [F-037: Watch Folder](../../features/planned/F-037-watch-folder.md)
- [ADR-0013: Configuration Schema](./0013-configuration-schema.md)
- [State-of-the-Art RAG Landscape](../../research/state-of-the-art-rag-landscape.md)
