# F-117: Self-Healing Index

**Status:** Completed
**Milestone:** v0.9.5

## Problem Statement

Common index issues require manual intervention. Need automatic repair capability.

## Design Approach

Extend doctor command with --fix option to auto-repair fixable issues.

## Implementation

### Implemented in
- `src/ragd/ui/cli/doctor.py`

### Auto-Fix Capabilities

1. **Orphaned Chunks**
   - Detects chunks without valid documents
   - Removes orphaned records from database
   - Reports number removed

2. **Missing Directories**
   - Creates chroma directory if missing
   - Ensures proper structure

### Usage
```bash
# Check what can be fixed
ragd doctor

# Run auto-fix
ragd doctor --fix
```

### Functions
- `fix_orphaned_chunks(data_dir)` - Remove orphan chunks
- `run_auto_fix(data_dir, console)` - Run all auto-fixes

## Implementation Tasks

- [x] Implement orphan chunk removal
- [x] Implement directory creation
- [x] Integrate with doctor command

## Success Criteria

- [x] Orphaned chunks removed
- [x] Missing directories created
- [x] Fix count reported

## Testing

- 2 tests in `tests/test_stability.py`
- All tests passing

---

**Status**: Completed
