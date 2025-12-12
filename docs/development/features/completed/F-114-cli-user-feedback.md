# F-114: CLI User Feedback

## Overview

**Milestone**: v0.9.6
**Priority**: P1 - High
**Deferred From**: v0.9.5

## Problem Statement

The CLI needs polished user feedback to provide a professional experience for early adopters:

- Progress indicators for long operations
- Clear, descriptive error messages
- Actionable hints when things go wrong
- Summary statistics after operations

## Design Approach

### Progress Indicators

Use Rich progress bars and spinners:

```python
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
) as progress:
    task = progress.add_task("Indexing documents...", total=len(files))
    for file in files:
        process_file(file)
        progress.advance(task)
```

### Error Message Structure

```
Error: Could not index document
  Path: /path/to/file.pdf
  Reason: PDF is password-protected

Hint: Remove the password or skip protected files with --skip-protected
```

### Operation Summaries

After indexing:

```
Indexing Complete
  Documents: 42 indexed, 3 skipped, 1 failed
  Chunks: 1,234 created
  Duration: 2m 34s

Run 'ragd status' to see index details.
```

## Implementation Tasks

- [ ] Create progress indicator wrapper class
- [ ] Implement Rich progress for indexing
- [ ] Implement Rich progress for search
- [ ] Create ErrorMessage formatter with hints
- [ ] Create OperationSummary formatter
- [ ] Add `--quiet` flag to suppress progress
- [ ] Add `--verbose` flag for detailed output
- [ ] Write unit tests for formatters
- [ ] Write integration tests for CLI output

## Success Criteria

- [ ] All long operations show progress
- [ ] All errors include actionable hints
- [ ] Operation summaries shown for major commands
- [ ] `--quiet` suppresses all non-essential output
- [ ] `--verbose` shows detailed progress
- [ ] Tests verify output formatting

## Dependencies

- F-110: Structured Logging (completed)
- F-111: Error Logging & Recovery (planned)

## Technical Notes

### Terminal Detection

Detect terminal capabilities:
- Use progress bars only in interactive terminals
- Fall back to simple output in pipes/scripts
- Respect NO_COLOR environment variable

### Internationalisation

Consider future i18n:
- Use message keys instead of hardcoded strings
- Structure messages for easy translation
- Keep technical terms (file paths, etc.) unlocalized

## Related Documentation

- [F-110 Structured Logging](../completed/F-110-structured-logging.md)
- [F-111 Error Logging & Recovery](./F-111-error-logging-recovery.md)
- [v0.9.6 Milestone](../../milestones/v0.9.6.md)

