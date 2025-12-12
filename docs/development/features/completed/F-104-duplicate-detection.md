# F-104: Duplicate Detection

**Status:** Completed
**Milestone:** v0.9.0

## Problem Statement

Duplicate documents waste storage and can skew search results. Need to detect and handle duplicates during indexing.

## Design Approach

Content-based duplicate detection using SHA-256 hashes with configurable handling policies.

### Components

**DuplicateInfo** - Record of detected duplicate:
```python
@dataclass
class DuplicateInfo:
    original_path: str
    duplicate_path: str
    hash_digest: str
    similarity: float = 1.0
```

**DuplicateTracker** - Registry for detecting duplicates:
```python
class DuplicateTracker:
    def check_and_register(content, path) -> (is_dup, original_path)
    def get_duplicates_for(path) -> list[str]
```

**DuplicateHandler** - Policy-based handling:
```python
class DuplicateHandler:
    policy: "skip" | "index_all" | "link"
    def should_index(content, path) -> bool
```

### Policies
- **skip** - Index only first occurrence (default)
- **index_all** - Index all occurrences
- **link** - Index once, link duplicates to original

## Implementation

### Files Created
- `src/ragd/ingestion/duplicate.py` - Duplicate detection module

### Key Components

**DuplicateInfo** (lines 14-21):
- Data class for duplicate records
- Stores original path, duplicate path, hash
- Similarity score (1.0 = exact match)

**DuplicateTracker** (lines 24-87):
- Maintains hash-to-path registry
- `check_and_register()` - Check and track content
- `unique_count` / `duplicate_count` - Statistics
- `get_duplicates_for()` - Find all duplicates of a document
- `clear()` - Reset tracker

**DuplicatePolicy** (lines 90-94):
- SKIP - Skip duplicates (default)
- INDEX_ALL - Index everything
- LINK - Index once, link others

**DuplicateHandler** (lines 97-140):
- Policy-based duplicate handling
- Optional callback on duplicate detection
- `should_index()` - Main decision point
- `get_stats()` - Return tracking statistics

**find_duplicates()** (lines 143-161):
- Convenience function for batch duplicate detection
- Takes dict of path -> content
- Returns list of DuplicateInfo

## Implementation Tasks

- [x] Create DuplicateInfo data class
- [x] Implement DuplicateTracker
- [x] Implement duplicate policies
- [x] Create DuplicateHandler with callbacks
- [x] Add find_duplicates convenience function
- [x] Add comprehensive tests

## Success Criteria

- [x] Duplicates detected via content hash
- [x] Multiple handling policies supported
- [x] Callback mechanism for notifications
- [x] Statistics tracking (unique/duplicate counts)

## Testing

- 11 tests in `tests/test_ingestion_enhanced.py`
- Tests tracker registration, duplicate detection
- Tests all policies (skip, index_all, link)
- Tests callbacks and statistics
- All tests passing

## Dependencies

- F-103: Content Hashing (uses ContentHash)

## Related Documentation

- [F-103: Content Hashing](./F-103-content-hashing.md)
- [v0.9.0 Implementation](../../implementation/v0.9.0.md)

