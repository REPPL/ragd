# F-111: Error Logging & Recovery

## Overview

**Milestone**: v0.9.6
**Priority**: P1 - High
**Deferred From**: v0.9.5

## Problem Statement

When indexing operations fail, users need detailed information about what went wrong, which documents succeeded or failed, and what remediation steps are available. Current error handling provides basic messages but lacks:

- Per-document success/failure tracking
- Categorised failure reasons
- Remediation hints for common errors
- Recovery options for partial failures

## Design Approach

### Error Categories

Define standard error categories:

```python
class IndexingErrorCategory(Enum):
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_DENIED = "permission_denied"
    UNSUPPORTED_FORMAT = "unsupported_format"
    EXTRACTION_FAILED = "extraction_failed"
    ENCODING_ERROR = "encoding_error"
    SIZE_EXCEEDED = "size_exceeded"
    CORRUPT_FILE = "corrupt_file"
    DEPENDENCY_MISSING = "dependency_missing"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"
```

### Per-Document Tracking

Track outcomes for each document:

```python
@dataclass
class DocumentResult:
    path: Path
    status: Literal["success", "failed", "skipped"]
    category: IndexingErrorCategory | None
    message: str | None
    duration_ms: int
    chunks_created: int
```

### Remediation Hints

Map error categories to actionable hints:

```python
REMEDIATION_HINTS = {
    IndexingErrorCategory.PERMISSION_DENIED: "Check file permissions with 'ls -l'",
    IndexingErrorCategory.UNSUPPORTED_FORMAT: "Convert to supported format or add extractor",
    IndexingErrorCategory.DEPENDENCY_MISSING: "Install missing dependency with 'pip install ragd[all]'",
    # ...
}
```

## Implementation Tasks

- [ ] Define IndexingErrorCategory enum
- [ ] Create DocumentResult dataclass
- [ ] Implement per-document result tracking in indexer
- [ ] Create remediation hint mapping
- [ ] Add error summary to CLI output
- [ ] Create `ragd index --report` option for detailed report
- [ ] Write unit tests for error categorisation
- [ ] Write integration tests for failure scenarios

## Success Criteria

- [ ] All indexing errors categorised
- [ ] Per-document results available after indexing
- [ ] Remediation hints shown for all error categories
- [ ] Error summary shows counts by category
- [ ] Tests cover all error categories

## Dependencies

- F-110: Structured Logging (completed)
- F-113: Exit Codes (completed)

## Technical Notes

### Report Format

The error report should be available in multiple formats:
- Rich console table (default)
- JSON for scripting
- Plain text for logging

### Integration with Doctor

Failed documents should be detectable by `ragd doctor` for later remediation attempts.

## Related Documentation

- [F-110 Structured Logging](../completed/F-110-structured-logging.md)
- [F-113 Exit Codes](../completed/F-113-exit-codes.md)
- [v0.9.6 Milestone](../../milestones/v0.9.6.md)

