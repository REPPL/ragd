# F-116: Index Integrity Checks

**Status:** Completed
**Milestone:** v0.9.5

## Problem Statement

No way to verify index health. Need diagnostic command for integrity checking.

## Design Approach

Implement `ragd doctor` command with multiple health checks and fix capabilities.

## Implementation

### Files Created
- `src/ragd/ui/cli/doctor.py` - Health check implementation

### Key Components

**HealthCheckResult** (dataclass):
- `name` - Check name
- `status` - "ok", "warning", "error"
- `message` - Description
- `details` - Additional info
- `fixable` - Can be auto-fixed

**HealthReport** (dataclass):
- `checks` - List of results
- `has_errors` - Property
- `has_warnings` - Property
- `is_healthy` - Property
- `fixable_issues` - Property

### Health Checks
1. **Database** - Verify ragd.db exists
2. **Vector Store** - Verify chroma directory
3. **Document Integrity** - Check for orphaned chunks
4. **Configuration** - Verify config.yaml

### Functions
- `run_health_checks(data_dir)` - Run all checks
- `format_health_report(report, console)` - Display report
- `fix_orphaned_chunks(data_dir)` - Remove orphans

### CLI Usage
```bash
# Run health check
ragd doctor

# Auto-fix issues
ragd doctor --fix
```

## Implementation Tasks

- [x] Create HealthCheckResult dataclass
- [x] Create HealthReport dataclass
- [x] Implement database check
- [x] Implement vector store check
- [x] Implement integrity check
- [x] Implement config check
- [x] Create report formatter

## Success Criteria

- [x] Health checks run
- [x] Issues identified
- [x] Report displayed

## Testing

- 10 tests in `tests/test_stability.py`
- All tests passing

---

**Status**: Completed
