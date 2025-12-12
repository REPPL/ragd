# F-118: Dry-Run Mode

## Overview

**Milestone**: v0.9.6
**Priority**: P1 - High
**Deferred From**: v0.9.5

## Problem Statement

Destructive operations (delete, re-index, doctor --fix) can have significant consequences. Users need a way to preview what would happen before committing to changes:

- See what files would be indexed/deleted
- Preview doctor repairs before applying
- Validate configuration changes safely

## Design Approach

### Global Flag

Add `--dry-run` flag to all destructive commands:

```bash
# Preview indexing
ragd index /path/to/docs --dry-run

# Preview deletion
ragd delete --all --dry-run

# Preview doctor repairs
ragd doctor --fix --dry-run
```

### Output Format

Dry-run output should clearly indicate:

```
[DRY RUN] Would index 42 documents:
  - /path/to/doc1.pdf (new)
  - /path/to/doc2.md (modified)
  - /path/to/doc3.txt (unchanged, skip)

No changes made. Remove --dry-run to proceed.
```

### Implementation Pattern

```python
def index_command(paths: list[Path], dry_run: bool = False):
    plan = create_indexing_plan(paths)

    if dry_run:
        display_plan(plan)
        console.print("[yellow]No changes made. Remove --dry-run to proceed.[/yellow]")
        return

    execute_plan(plan)
```

## Implementation Tasks

- [ ] Add `--dry-run` flag to `ragd index`
- [ ] Add `--dry-run` flag to `ragd delete`
- [ ] Add `--dry-run` flag to `ragd doctor --fix`
- [ ] Create plan display formatter
- [ ] Ensure consistent dry-run output format
- [ ] Add dry-run indicator to progress output
- [ ] Write unit tests for plan generation
- [ ] Write integration tests for dry-run mode

## Success Criteria

- [ ] All destructive commands support `--dry-run`
- [ ] Dry-run output clearly shows planned changes
- [ ] No changes made during dry-run
- [ ] Exit code indicates dry-run mode
- [ ] Tests verify no side effects in dry-run

## Dependencies

- F-113: Exit Codes (completed)
- F-114: CLI User Feedback (planned)

## Technical Notes

### Exit Codes

Define specific exit codes for dry-run:
- 0: Dry-run complete, no errors in plan
- 1: Dry-run complete, errors detected in plan
- 2: Usage error (invalid arguments)

### Atomicity

For complex operations, dry-run should show the complete plan:
- All files that would be affected
- Order of operations
- Estimated duration (if available)

### Configuration

Consider config option to require dry-run for dangerous operations:

```yaml
safety:
  require_dry_run_first: true  # Require --dry-run before destructive ops
```

## Related Documentation

- [F-113 Exit Codes](../completed/F-113-exit-codes.md)
- [F-114 CLI User Feedback](./F-114-cli-user-feedback.md)
- [v0.9.6 Milestone](../../milestones/v0.9.6.md)

