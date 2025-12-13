# F-126: Final Bug Fixes

## Overview

**Milestone**: v1.1.0
**Priority**: P0
**Deferred From**: v1.0.0
**Approach**: Audit first, then fix

## Problem Statement

Production release requires zero critical bugs:
- All existing tests must pass
- No security vulnerabilities
- No type errors or linting issues
- No known crashes or data loss scenarios

## Design Approach

**Systematic bug audit:**
1. Run all automated quality tools
2. Categorise findings by severity
3. Fix in priority order (P0 → P1 → P2)
4. Add regression tests for each fix
5. Verify clean state before release

**Priority categories:**
- **P0**: Security vulnerabilities, data loss, crashes
- **P1**: Test failures, incorrect behaviour
- **P2**: Type errors, linting violations
- **P3**: Style issues, warnings (best effort)

## Implementation Tasks

- [ ] Run pytest suite and fix any failures
- [ ] Run ruff check and fix all errors
- [ ] Run mypy --strict and fix type errors
- [ ] Run bandit security scan and address findings
- [ ] Run pip-audit for dependency vulnerabilities
- [ ] Run safety check for known vulnerabilities
- [ ] Review open GitHub issues for unreported bugs
- [ ] Add regression tests for each bug fixed
- [ ] Update CHANGELOG with bug fixes
- [ ] Verify clean state with all tools passing

## Success Criteria

- [ ] `pytest tests/ -v` passes 100%
- [ ] `ruff check src/ragd/` shows no errors
- [ ] `mypy src/ragd/ --strict` shows no errors
- [ ] `bandit -r src/ragd/` shows no high/critical issues
- [ ] `pip-audit` shows no known vulnerabilities
- [ ] `safety check` passes
- [ ] All P0 and P1 bugs fixed
- [ ] Regression test added for each fix
- [ ] CHANGELOG updated

## Dependencies

- All other v1.0 features should be complete first
- Run audit after F-119, F-123-125, F-075, F-057

## Technical Notes

### Audit Commands

```bash
# Test suite
pytest tests/ -v --tb=short

# Linting
ruff check src/ragd/ --show-fixes
ruff format src/ragd/ --check

# Type checking
mypy src/ragd/ --strict

# Security
bandit -r src/ragd/ -f json -o bandit_report.json
pip-audit --format json > pip_audit.json
safety check --json > safety_report.json

# All in one (CI-style)
./scripts/audit.sh
```

### Finding Categorisation

```markdown
## P0 - Critical (Block Release)
- [ ] <finding description> (security/data-loss/crash)

## P1 - High (Must Fix)
- [ ] <finding description> (test failure/incorrect behaviour)

## P2 - Medium (Should Fix)
- [ ] <finding description> (type error/lint violation)

## P3 - Low (Best Effort)
- [ ] <finding description> (style/warning)
```

### Regression Test Pattern

```python
# tests/regression/test_bug_XXX.py
"""Regression test for bug XXX.

Issue: <description>
Root cause: <explanation>
Fix: <what was changed>
"""

def test_bug_XXX_does_not_regress():
    """Verify bug XXX stays fixed."""
    # Reproduce the conditions that caused the bug
    # Assert the correct behaviour
    pass
```

### CHANGELOG Format

```markdown
## [1.0.0] - YYYY-MM-DD

### Fixed
- Fixed crash when indexing empty PDF files (#123)
- Fixed incorrect search ranking for multi-word queries (#124)
- Fixed memory leak in chat session cleanup (#125)
```

## Related Documentation

- [v1.1.0 Milestone](../../milestones/v1.1.0.md)
- [F-127: Performance Benchmarks](../completed/F-127-performance-benchmarks.md) - Run after bugs fixed

---

**Status**: Planned
