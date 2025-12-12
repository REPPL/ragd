# F-085: Test Coverage Boost

## Problem Statement

Current test coverage is 56%. For a security-focused release, we need higher confidence in code correctness. Target: 85% coverage.

## Design Approach

### 1. Coverage Analysis

Identify untested code paths using pytest-cov:

```bash
pytest tests/ --cov=src/ragd --cov-report=html
```

### 2. Priority Areas

Focus on high-risk areas:
- Security modules (encryption, validation, secrets)
- CLI commands (user-facing functionality)
- Storage operations (data integrity)
- Error handling paths

### 3. Test Types

- Unit tests for individual functions
- Integration tests for CLI commands
- Edge case tests for error conditions

## Implementation Tasks

- [x] Analyse current coverage gaps
- [x] Add tests for security modules
- [x] Add tests for CLI commands
- [x] Add tests for error handling
- [x] Add tests for edge cases
- [x] Verify 85% coverage achieved

## Success Criteria

- [x] Test coverage ≥85%
- [x] All security-critical code paths tested
- [x] All CLI commands have at least basic tests
- [x] Edge cases documented and tested

## Dependencies

- v0.8.5 (Knowledge Graph Foundation)
- pytest-cov installed

