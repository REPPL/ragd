# F-037: Watch Folder Auto-Indexing

## Overview

**Use Case**: Automatic document indexing
**Milestone**: v0.2
**Priority**: P1

## Problem Statement

Users must manually run `ragd index` whenever documents change. For active document collections, this creates friction and leads to stale indexes. GPT4All's "LocalDocs" feature demonstrates that watch-folder functionality significantly improves user experience.

## Design Approach

Implement a daemon that monitors configured directories and automatically indexes new or modified documents.

**Command Interface:**

```bash
ragd watch ~/Documents              # Watch single directory
ragd watch ~/Documents ~/Projects   # Watch multiple directories
ragd watch --status                 # Show watched directories and status
ragd watch --stop                   # Stop the watch daemon
```

**Configuration:**

```yaml
# ~/.ragd/config.yaml
watch:
  enabled: true
  directories:
    - ~/Documents
    - ~/Projects/notes
  patterns:
    - "*.pdf"
    - "*.md"
    - "*.txt"
    - "*.docx"
  exclude:
    - "**/node_modules/**"
    - "**/.git/**"
    - "**/venv/**"
  debounce_seconds: 5      # Wait before indexing after change
  max_file_size_mb: 100    # Skip files larger than this
```

**Status Output:**

```
ragd watch --status

Watch Daemon Status
───────────────────────────────────────────────────────

Status: Running (PID 12345)
Uptime: 2 hours 34 minutes

Watched Directories:
  ~/Documents         1,234 files indexed
  ~/Projects/notes      456 files indexed

Recent Activity:
  14:32:01  Indexed: ~/Documents/meeting-notes.md (new)
  14:28:45  Indexed: ~/Documents/report.pdf (modified)
  14:15:22  Skipped: ~/Documents/video.mp4 (unsupported type)

Queue: 0 files pending
```

## Implementation Tasks

- [ ] Create `ragd watch` command in CLI
- [ ] Implement file system watcher (watchdog library)
- [ ] Implement debouncing for rapid file changes
- [ ] Implement pattern matching for file types
- [ ] Implement exclusion patterns
- [ ] Implement daemon mode (background process)
- [ ] Implement `--status` command
- [ ] Implement `--stop` command
- [ ] Add configuration file support
- [ ] Implement logging for watch events
- [ ] Handle large file skipping
- [ ] Implement graceful shutdown

## Success Criteria

- [ ] New files indexed within 10 seconds of creation
- [ ] Modified files re-indexed automatically
- [ ] Deleted files removed from index
- [ ] Daemon survives terminal close
- [ ] Low CPU usage when idle (<1%)
- [ ] Graceful handling of permission errors

## Dependencies

- [F-001: Document Ingestion](./F-001-document-ingestion.md) - Indexing pipeline
- Python watchdog library

## Technical Notes

**File System Watcher:**

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

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
        # Debounce: wait for file to stabilise
        self.pending[path] = time.time()

    def process_pending(self):
        now = time.time()
        ready = [
            path for path, ts in self.pending.items()
            if now - ts >= self.debounce
        ]
        for path in ready:
            del self.pending[path]
            self.indexer.index(path)
```

**Daemon Management:**

```python
import os
import signal
from pathlib import Path

PID_FILE = Path.home() / ".ragd" / "watch.pid"

def start_daemon():
    """Start watch daemon in background."""
    pid = os.fork()
    if pid > 0:
        # Parent: save PID and exit
        PID_FILE.write_text(str(pid))
        print(f"Watch daemon started (PID {pid})")
        return

    # Child: become daemon
    os.setsid()
    # ... run watcher loop

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

**Pattern Matching:**

```python
from fnmatch import fnmatch

def should_index(path: str, patterns: list[str], excludes: list[str]) -> bool:
    """Check if file should be indexed based on patterns."""
    # Check exclusions first
    for exclude in excludes:
        if fnmatch(path, exclude):
            return False

    # Check if matches any pattern
    for pattern in patterns:
        if fnmatch(path, pattern):
            return True

    return False
```

## Competitive Analysis

**GPT4All LocalDocs:**
- Drag-and-drop folder interface
- Automatic file watching
- Progress indicator during indexing
- ~0.1s latency overhead for RAG queries

**ragd Advantages:**
- CLI-native (scriptable)
- Multiple directory support
- Pattern-based filtering
- Daemon status monitoring

## Related Documentation

- [State-of-the-Art RAG Landscape](../../research/state-of-the-art-rag-landscape.md) - GPT4All analysis
- [F-001: Document Ingestion](./F-001-document-ingestion.md)
- [UC-001: Index Documents](../../../use-cases/briefs/UC-001-index-documents.md)

---

**Status**: Completed
