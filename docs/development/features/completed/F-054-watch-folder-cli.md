# F-054: Watch Folder CLI

## Overview

**Use Case**: Command-line folder watching
**Milestone**: v0.2.9
**Priority**: P1

## Problem Statement

The watch folder backend (F-037) was implemented in v0.2.0, but users have no CLI interface to start, stop, or monitor the folder watcher. Users need command-line control over automatic document indexing.

## Design Approach

Expose existing watcher backend via CLI subcommands:

**Watch Commands:**

```bash
ragd watch start ~/Documents              # Watch single directory
ragd watch start ~/PDFs ~/Notes           # Watch multiple directories
ragd watch start ~/Research --pattern "*.pdf"  # Filter by pattern
ragd watch start ~/Docs --no-recursive    # Don't watch subdirectories
ragd watch stop                           # Stop the watcher
ragd watch status                         # Show watcher status
ragd watch status --format json           # JSON output for scripting
```

## Implementation Tasks

- [x] Add `watch_start_command()` wrapping FolderWatcher
- [x] Add `watch_stop_command()` for stopping daemon
- [x] Add `watch_status_command()` for status display
- [x] Support `--pattern` for file type filtering
- [x] Support `--recursive/--no-recursive` option
- [x] Create `watch` subcommand group in CLI
- [x] Handle watchdog dependency gracefully
- [x] Support JSON output format
- [x] Export commands from CLI module

## Success Criteria

- [x] Users can start watching directories via CLI
- [x] Users can stop the watcher via CLI
- [x] Users can check watcher status
- [x] Pattern filtering works
- [x] Recursive option works
- [x] Graceful error when watchdog not installed
- [x] All existing tests pass

## Dependencies

- [F-037: Watch Folder Auto-Indexing](./F-037-watch-folder.md) - FolderWatcher backend

## Technical Notes

**Subcommand Structure:**

```python
watch_app = typer.Typer(help="Watch folders for automatic indexing.")
app.add_typer(watch_app, name="watch")

@watch_app.command("start")
def watch_start(directories: list[Path], ...): ...

@watch_app.command("stop")
def watch_stop(...): ...

@watch_app.command("status")
def watch_status_cmd(...): ...
```

**Dependency Handling:**

```python
if not WATCHDOG_AVAILABLE:
    con.print("[red]Error: watchdog library not installed[/red]")
    con.print("Install with: [cyan]pip install watchdog[/cyan]")
    raise typer.Exit(1)
```

**Status Output:**

```
Watch Daemon Status
───────────────────────────────────────────────────────

Status: Running (PID 12345)
Uptime: 2 hours 34 minutes

Watched Directories:
  ~/Documents         1,234 files indexed
  ~/Projects/notes      456 files indexed

Queue: 0 files pending
```

## Related Documentation

- [F-037: Watch Folder Auto-Indexing](./F-037-watch-folder.md)
- [v0.2.6-v0.2.9 Milestone](../../milestones/v0.2.6-v0.2.9.md)

---

**Status**: Completed
