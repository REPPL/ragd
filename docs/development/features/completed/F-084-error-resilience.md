# F-084: Error Resilience

## Problem Statement

When errors occur, ragd may expose internal details (stack traces, file paths, system information) that could aid attackers. Error messages should be helpful to users without revealing sensitive implementation details.

## Design Approach

### 1. User-Facing Error Messages

Replace stack traces with actionable messages:

```
# Bad
Traceback (most recent call last):
  File "/Users/username/.../ragd/storage/chromadb.py", line 42
    ...
ConnectionError: [Errno 61] Connection refused

# Good
Error: Cannot connect to vector database.
Hint: Ensure ragd is initialised with `ragd init`
```

### 2. Error Categories

Define error categories with user-friendly messages:

```python
class RagdError(Exception):
    """Base error with user message and internal details."""

    def __init__(self, message: str, hint: str | None = None, internal: str | None = None):
        self.message = message
        self.hint = hint
        self.internal = internal  # Only logged, never shown
```

### 3. Graceful Degradation

When optional features fail, continue with reduced functionality rather than crashing.

## Implementation Tasks

- [x] Create `src/ragd/errors.py` with error hierarchy
- [x] Implement `RagdError` base class with user/internal separation
- [x] Add error handler in CLI that shows user message, logs internal
- [x] Update existing error handling to use new patterns
- [x] Add tests for error message safety

## Success Criteria

- [x] No stack traces shown to users (unless --debug)
- [x] All errors include actionable hints
- [x] Internal details logged but not displayed
- [x] Graceful degradation for optional features

## Dependencies

- v0.8.5 (Knowledge Graph Foundation)

---

## Related Documentation

- [v0.8.6 Milestone](../../milestones/v0.8.6.md)
- [F-082 Security Hardening](./F-082-security-hardening.md)

---

**Status**: Completed
