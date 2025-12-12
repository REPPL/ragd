# F-103: Content Hashing

**Status:** Completed
**Milestone:** v0.9.0

## Problem Statement

Re-indexing unchanged files wastes resources. Need to detect file changes efficiently.

## Design Approach

Store content hash for each indexed document. Compare hash before re-indexing.

### Hash Types

**FileHash** - Fast change detection using file metadata:
```python
@dataclass(frozen=True, slots=True)
class FileHash:
    path: str       # Absolute path
    size: int       # File size in bytes
    mtime: float    # Modification time
```

**ContentHash** - Accurate change detection using content:
```python
@dataclass(frozen=True, slots=True)
class ContentHash:
    algorithm: str  # Hash algorithm (sha256, md5, etc.)
    digest: str     # Hex digest
```

### Algorithm
1. Calculate file hash (mtime + size for speed)
2. Check stored hash
3. If different, calculate content hash
4. Re-index only if content changed

## Implementation

### Files Created
- `src/ragd/ingestion/hashing.py` - Content hashing module

### Key Components

**FileHash** (lines 13-40):
- Frozen dataclass for immutability
- `from_path(path)` - Create from file
- `to_string()` - Create comparison string

**ContentHash** (lines 43-86):
- Frozen dataclass for immutability
- `from_content(content, algorithm)` - Hash string or bytes
- `from_file(path, algorithm)` - Hash file contents
- Default algorithm: SHA-256

**Change Detection Functions** (lines 89-139):
- `file_changed(path, stored_hash)` - Fast check using metadata
- `content_changed(content, stored_hash)` - Accurate check using content
- `is_duplicate(content, existing_hashes)` - Check against hash set

## Implementation Tasks

- [x] Implement file hash calculation
- [x] Implement content hash calculation
- [x] Add hash comparison functions
- [x] Duplicate detection function
- [x] Support multiple hash algorithms

## Success Criteria

- [x] Unchanged files detected via file hash
- [x] Content changes detected via content hash
- [x] Duplicate content identified
- [x] Multiple algorithms supported (SHA-256, MD5, etc.)

## Testing

- 16 tests in `tests/test_ingestion_enhanced.py`
- Tests FileHash creation, immutability
- Tests ContentHash with strings, bytes, files
- Tests deterministic hashing, change detection
- Tests duplicate detection
- All tests passing

## Dependencies

- v0.8.7 (CLI Polish)

## Related Documentation

- [F-102: Indexing Resume](./F-102-indexing-resume.md)
- [F-104: Duplicate Detection](./F-104-duplicate-detection.md)
- [v0.9.0 Implementation](../../implementation/v0.9.0.md)

