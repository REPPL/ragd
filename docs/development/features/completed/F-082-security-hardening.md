# F-082: Security Hardening

## Problem Statement

As ragd prepares for wider release, it needs comprehensive input validation and security hardening to prevent common vulnerabilities like path traversal, command injection, and malformed input attacks. Current code paths may accept user input without sufficient sanitisation.

## Design Approach

### 1. Path Validation Module

Create `src/ragd/security/validation.py` with secure path handling:

```python
from pathlib import Path

def validate_path(path: Path, base_dir: Path | None = None) -> Path:
    """Validate path is safe and optionally within base_dir."""
    resolved = path.resolve()

    # Check for path traversal
    if base_dir:
        base_resolved = base_dir.resolve()
        if not str(resolved).startswith(str(base_resolved)):
            raise ValueError(f"Path traversal detected: {path}")

    return resolved
```

### 2. Input Sanitisation

- Validate document IDs (alphanumeric, hyphens, underscores only)
- Validate tag names (no special characters that could cause injection)
- Validate search queries (escape dangerous patterns)
- Limit input lengths to prevent DoS

### 3. File Operation Safety

- Use `Path.resolve()` for all file operations
- Check file existence before operations
- Handle symlinks safely
- Limit file sizes during indexing

## Implementation Tasks

- [x] Create `src/ragd/security/validation.py` module
- [x] Implement `validate_path()` function with traversal prevention
- [x] Implement `validate_document_id()` function
- [x] Implement `validate_tag_name()` function
- [x] Implement `sanitise_search_query()` function
- [x] Add input length limits
- [x] Integrate validation into CLI commands
- [x] Add comprehensive unit tests

## Success Criteria

- [x] No path traversal vulnerabilities in file operations
- [x] All user inputs validated before use
- [x] Clear error messages for invalid input
- [x] Tests cover edge cases (../../../etc/passwd, null bytes, etc.)

## Dependencies

- v0.8.5 (Knowledge Graph Foundation)

## Related Documentation

- [ADR-0009: Security Architecture](../../decisions/adrs/0009-security-architecture.md)
- [F-083: Secrets Management](./F-083-secrets-management.md)
- [v0.8.5 Milestone](../../milestones/v0.8.5.md)
