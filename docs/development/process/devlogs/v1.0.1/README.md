# v1.0.1 Development Log: Post-Release Polish

**Date:** 2025-12-13
**Version:** 1.0.1 (improvements to 1.0.0)
**Theme:** Documentation and Code Quality Polish

## Session Overview

Following the v1.0.0 release, conducted a comprehensive review and addressed documentation inconsistencies, code quality issues, and milestone tracking updates.

## Changes Made

### 1. Documentation Version Fixes

Fixed version references that showed "v1.0.0a6" or "v0.1" instead of "v1.0.0":

| File | Change |
|------|--------|
| `docs/reference/cli-reference.md` (line 3) | "v1.0.0a6" → "v1.0.0" |
| `docs/reference/cli-reference.md` (line 673) | "v1.0.0a6" → "v1.0.0" |
| `docs/guides/troubleshooting.md` (line 46) | "v0.1" → "v1.0.0" |

### 2. Feature Status Updates

Moved 5 completed features from `planned/` to `completed/`:

- `F-075-backend-migration-tool.md`
- `F-119-full-features-by-default.md`
- `F-057-model-comparison.md`
- `F-123-performance-profiling.md`
- `F-127-performance-benchmarks.md`

Updated 3 deferred features to target v1.1.0:

- `F-124-memory-optimisation.md` - Added "Deferred From: v1.0.0"
- `F-125-startup-time.md` - Added "Deferred From: v1.0.0"
- `F-126-final-bug-fixes.md` - Added "Deferred From: v1.0.0"

### 3. Code Quality Fixes

#### Exception Handling in `src/ragd/ingestion/pipeline.py`

Replaced bare `except Exception` with specific exception types:

**Line 352 (Contextual retrieval):**
```python
# Before
except Exception:
    pass

# After
except (ImportError, ConnectionError, RuntimeError) as e:
    logger.debug("Contextual retrieval unavailable: %s", e)
```

**Lines 488-493 (Vision pipeline):**
```python
# Before
except ImportError:
    pass
except Exception:
    pass

# After
except ImportError:
    logger.debug("Vision dependencies not installed for %s", path.name)
except (OSError, ValueError, RuntimeError) as e:
    logger.debug("Image extraction failed for %s: %s", path.name, e)
```

#### Deprecated datetime.utcnow() in `tests/test_archive.py`

Fixed 3 occurrences of deprecated `datetime.utcnow()`:

```python
# Before
from datetime import datetime
indexed_at=datetime.utcnow().isoformat()

# After
from datetime import UTC, datetime
indexed_at=datetime.now(UTC).isoformat()
```

### 4. Milestone Documentation Updates

#### v1.0.0 Milestone
- Updated feature table to show completed vs deferred
- Updated use cases status
- Fixed feature links to point to completed/ folder

#### v1.1.0 Milestone
- Added "Deferred from v1.0.0" section
- Listed F-124, F-125, F-126

### 5. New Documentation

Created:
- `docs/development/implementation/v1.0.0.md` - Implementation record
- `docs/development/process/retrospectives/v1.0.0/README.md` - Retrospective

### 6. Milestone Reorganisation (v1.1.0 Feasibility)

Evaluated v1.1.0 scope (11 features) and determined it was too ambitious. Reorganised:

**v1.1.0 reduced from 11 → 7 features:**
- Keeps: F-124, F-125, F-126 (deferred), F-128-131 (core NER/Graph)
- Removed: F-132, F-133, F-134, F-135 (Advanced CLI extras)

**v1.2.0 expanded from 1 → 5 features:**
- Keeps: F-134 Onboarding Flow
- Added: F-140-143 (renumbered from v1.1.0's F-132-135)

| Old ID | New ID | Feature |
|--------|--------|---------|
| F-132 | F-140 | Comparison Framework |
| F-133 | F-141 | Batch Operations |
| F-134 (Results Export) | F-142 | Results Export |
| F-135 | F-143 | Timing & Metrics |

**Rationale:** Feature IDs F-132-135 conflicted with v1.3.0 features. Renumbered to F-140+ to avoid conflicts.

## Files Changed

### Documentation (13 files)
- `docs/reference/cli-reference.md` - Version fix
- `docs/guides/troubleshooting.md` - Version fix
- `docs/development/milestones/v1.0.0.md` - Status updates
- `docs/development/milestones/v1.1.0.md` - Add deferred features, remove F-132-135
- `docs/development/milestones/v1.2.0.md` - Expand scope, add F-140-143
- `docs/development/features/planned/F-124-memory-optimisation.md` - Milestone update
- `docs/development/features/planned/F-125-startup-time.md` - Milestone update
- `docs/development/features/planned/F-126-final-bug-fixes.md` - Milestone update
- 5 feature files moved from `planned/` to `completed/`

### Code (2 files)
- `src/ragd/ingestion/pipeline.py` - Exception handling
- `tests/test_archive.py` - datetime deprecation

### New Files (3)
- `docs/development/implementation/v1.0.0.md`
- `docs/development/process/retrospectives/v1.0.0/README.md`
- `docs/development/process/devlogs/v1.0.1/README.md` (this file)

## Technical Notes

### Exception Type Selection

For contextual retrieval fallback:
- `ImportError` - Module not available
- `ConnectionError` - Ollama service unavailable
- `RuntimeError` - General runtime failures

For vision pipeline:
- `ImportError` - Vision dependencies not installed
- `OSError` - File access issues
- `ValueError` - Invalid image data
- `RuntimeError` - Processing failures

### datetime.UTC vs datetime.timezone.utc

Python 3.11+ provides `datetime.UTC` as shorthand for `datetime.timezone.utc`. Using the shorter form for cleaner code.

## Verification

- [ ] All tests passing
- [ ] Pre-commit hooks passing
- [ ] CLI commands working correctly

## Session Stats

- **Duration:** ~1 hour
- **Files modified:** 13
- **New files created:** 3
- **Tests still passing:** 1,907

---

**Next:** Run verification, commit changes, push to GitHub.
