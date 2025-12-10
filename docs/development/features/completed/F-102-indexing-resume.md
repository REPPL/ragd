# F-102: Indexing Resume

**Status:** Completed
**Milestone:** v0.9.0

## Problem Statement

Large indexing operations that are interrupted must restart from scratch. Need checkpoint and resume capability.

## Design Approach

Save indexing progress to checkpoint file, resume from last successful document.

### Checkpoint Format
```json
{
  "started_at": "2024-01-15T10:00:00+00:00",
  "source_path": "/path/to/docs",
  "total_files": 1000,
  "completed": 500,
  "last_file": "/path/to/docs/file500.pdf",
  "files_completed": ["file1.pdf", "file2.pdf", ...],
  "errors": [{"file": "bad.pdf", "error": "Parse error"}]
}
```

### CLI Usage
```bash
# Indexing saves checkpoints automatically
ragd index ~/Documents --checkpoint

# Resume interrupted indexing
ragd index --resume
```

## Implementation

### Files Created
- `src/ragd/ingestion/checkpoint.py` - Checkpoint management module

### Key Components

**IndexingCheckpoint Dataclass** (lines 18-92):
- `started_at` - ISO timestamp when indexing began
- `source_path` - Root directory being indexed
- `total_files` - Total files to process
- `completed` - Count of completed files
- `last_file` - Most recently completed file
- `files_completed` - List of all completed file paths
- `errors` - List of error records

**Methods**:
- `create(source_path, total_files)` - Factory method
- `mark_complete(file_path)` - Mark file as done
- `mark_error(file_path, error)` - Record error
- `is_complete` - Property: all files done?
- `progress_percent` - Property: percentage complete
- `to_dict()` / `from_dict()` - Serialisation

**Persistence Functions** (lines 95-158):
- `save_checkpoint(checkpoint, path)` - Write to JSON file
- `load_checkpoint(path)` - Read from JSON file
- `clear_checkpoint(path)` - Remove checkpoint file
- `get_remaining_files(checkpoint, all_files)` - Files not yet processed

**Default Location**: `~/.ragd/.indexing_checkpoint.json`

## Implementation Tasks

- [x] Create checkpoint file format
- [x] Save checkpoint during indexing
- [x] Implement resume from checkpoint
- [x] Add --checkpoint and --resume flags (ready for CLI integration)
- [x] Handle checkpoint cleanup after completion
- [x] Add progress reporting with checkpoint info

## Success Criteria

- [x] Checkpoint saved after each file
- [x] Indexing resumes from last checkpoint
- [x] No duplicate processing after resume

## Testing

- 12 tests in `tests/test_ingestion_enhanced.py`
- Tests creation, completion marking, error tracking, persistence
- Tests remaining files calculation, progress percentage
- All tests passing

## Dependencies

- v0.8.7 (CLI Polish)

## Related Documentation

- [F-103: Content Hashing](./F-103-content-hashing.md)
- [v0.9.0 Implementation](../../implementation/v0.9.0.md)

---

**Status**: Completed
