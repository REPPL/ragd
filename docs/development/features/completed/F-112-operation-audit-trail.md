# F-112: Operation Audit Trail

## Overview

**Milestone**: v0.9.6
**Priority**: P2 - Medium
**Deferred From**: v0.9.5

## Problem Statement

Users need visibility into what operations have been performed on their index over time. This is valuable for:

- Debugging issues ("when was this indexed?")
- Understanding index state ("what changed recently?")
- Compliance ("who did what when?")
- Recovery ("what was the state before X?")

## Design Approach

### Audit Log Schema

```python
@dataclass
class AuditEntry:
    id: str  # UUID
    timestamp: datetime
    operation: str  # "index", "delete", "search", "doctor", etc.
    target: str | None  # File path or query
    result: str  # "success", "partial", "failed"
    duration_ms: int
    details: dict[str, Any]  # Operation-specific metadata
```

### Storage

Store audit log in SQLite alongside the index database:

```sql
CREATE TABLE audit_log (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    operation TEXT NOT NULL,
    target TEXT,
    result TEXT NOT NULL,
    duration_ms INTEGER,
    details TEXT  -- JSON
);

CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_operation ON audit_log(operation);
```

### Query Interface

```bash
# View recent operations
ragd audit list

# Filter by operation type
ragd audit list --operation index

# Filter by time range
ragd audit list --since "2024-01-01" --until "2024-01-31"

# View specific entry
ragd audit show <id>
```

## Implementation Tasks

- [ ] Define AuditEntry dataclass
- [ ] Create audit_log table in database
- [ ] Implement audit logging decorator/context manager
- [ ] Add audit logging to index, delete, search commands
- [ ] Create `ragd audit list` command
- [ ] Create `ragd audit show` command
- [ ] Add JSON and plain output modes
- [ ] Write unit tests
- [ ] Write integration tests

## Success Criteria

- [ ] All major operations logged
- [ ] Audit log queryable by time, operation, result
- [ ] Audit entries include relevant details
- [ ] Performance impact < 1% on operations
- [ ] Tests cover all audit scenarios

## Dependencies

- F-110: Structured Logging (completed)
- F-113: Exit Codes (completed)

## Technical Notes

### Log Rotation

Consider log rotation policy:
- Maximum entries (e.g., 10,000)
- Maximum age (e.g., 90 days)
- User-configurable via config.yaml

### Privacy Considerations

Audit log may contain file paths and search queries. Consider:
- Option to disable audit logging
- Option to exclude sensitive operations
- Clear documentation of what's logged

## Related Documentation

- [F-110 Structured Logging](../completed/F-110-structured-logging.md)
- [F-113 Exit Codes](../completed/F-113-exit-codes.md)
- [v0.9.6 Milestone](../../milestones/v0.9.6.md)

---

**Status**: Planned
