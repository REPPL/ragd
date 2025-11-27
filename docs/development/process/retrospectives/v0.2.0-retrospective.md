# v0.2.0 Retrospective

## Summary

v0.2.0 delivered 12 features across 4 minor releases (v0.2.0-v0.2.3), adding PDF processing, metadata management, archive export/import, and web support to ragd.

**Duration:** 2 sessions (26-27 November 2025)
**Outcome:** Success - all planned features implemented

## What Happened vs Plan

### Planned Features

| Release | Features | Status |
|---------|----------|--------|
| v0.2.0 | F-025, F-026, F-029, F-030 | Completed |
| v0.2.1 | F-027, F-028, F-031 | Completed |
| v0.2.2 | F-032, F-033, F-034 | Completed |
| v0.2.3 | F-037, F-038 | Completed |

### Actual Execution

Implementation followed the plan closely:

1. **Foundation first** - PDF quality detection and metadata storage provided base for later features
2. **Protocol-based design** - All modules use Python Protocols for extensibility
3. **Lazy loading** - Heavy dependencies (Docling, OCR engines) load on demand
4. **Graceful degradation** - Features work without optional dependencies

## Manual Interventions Required

1. **Manual test script creation** - User requested tests as executable script rather than copy-paste due to indentation issues
2. **Security audit fix** - CRITICAL tarfile path traversal vulnerability required immediate fix
3. **Documentation audit fix** - Duplicate feature specs (F-008/F-035), broken links, status inconsistencies

## Issues Found and Fixed

### Security (CRITICAL)

- **Tarfile path traversal** in `import_.py` - Could allow arbitrary file writes via malicious archive
- **Fix:** Added `_safe_extract()` function with member validation
- **Tests:** Added 4 security tests for path traversal, absolute paths, and symlinks

### Documentation

- **Duplicate specs** - F-008 and F-035 both described health checks
- **Fix:** Removed F-008, kept F-035 (the implemented version)
- **Status inconsistency** - Features in `completed/` still had "Planned" status
- **Fix:** Updated status in F-035, F-036, and all v0.2 features

### Dependencies

- **urllib3 vulnerability** - Transitive dependency had known CVEs
- **Fix:** Added `urllib3>=2.5.0` constraint to pyproject.toml

## Documentation Drift Discovered

1. **Feature location drift** - 12 feature specs remained in `planned/` after implementation
2. **Broken cross-references** - Research docs linked to moved feature files
3. **Missing README** - `planning/` directory lacked README.md

## What Worked Well

1. **Protocol-based architecture** - Made adding new processors (OCR, PDF) straightforward
2. **Lazy loading pattern** - Kept startup fast despite heavy optional deps
3. **Feature flag pattern** - `DOCLING_AVAILABLE`, `WATCHDOG_AVAILABLE` made graceful degradation easy
4. **Comprehensive test suite** - 315 tests caught integration issues early
5. **Manual UAT script** - Executable test script validated end-to-end behaviour

## Lessons Learned

1. **Security audits matter** - Tarfile vulnerability would have been a significant risk
2. **Documentation audits catch drift** - SSOT violations and broken links accumulate
3. **Auto-generate UAT scripts** - Should be part of milestone completion workflow
4. **Test with real archives** - Need malicious archive test fixtures

## Action Items for v0.3

1. **Add CI security checks** - pip-audit, bandit in GitHub Actions
2. **Link validation** - Add pre-commit hook for markdown link checking
3. **Status automation** - Consider making feature status derive from folder location only
4. **Milestone directory** - Create `milestones/` with per-version release notes

## Metrics

| Metric | Value |
|--------|-------|
| Features implemented | 12 |
| Test count | 315 (passing) |
| Test coverage | ~68% |
| Security fixes | 1 CRITICAL, 1 HIGH |
| Documentation fixes | 3 HIGH, 2 MEDIUM |

---

**Status**: Completed
