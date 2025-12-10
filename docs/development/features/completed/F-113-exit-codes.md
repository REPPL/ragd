# F-113: Exit Codes & Status

**Status:** Completed
**Milestone:** v0.9.5

## Problem Statement

Inconsistent exit codes make scripting difficult. Need standard codes for automation.

## Design Approach

Define standard exit codes matching Unix conventions and common CLI tools.

## Implementation

### Files Created
- `src/ragd/ui/cli/exit_codes.py` - Exit code definitions

### Exit Codes

| Code | Name | Description |
|------|------|-------------|
| 0 | SUCCESS | Operation completed successfully |
| 1 | GENERAL_ERROR | General/unknown error |
| 2 | USAGE_ERROR | Invalid command usage |
| 3 | CONFIG_ERROR | Configuration error |
| 4 | DEPENDENCY_ERROR | Missing dependency |
| 5 | PARTIAL_SUCCESS | Some items failed |
| 6 | NOT_FOUND | Resource not found |
| 7 | PERMISSION_ERROR | Permission denied |
| 8 | TIMEOUT_ERROR | Operation timed out |
| 130 | INTERRUPTED | Ctrl+C / SIGINT |

### Functions
- `get_exit_code_description(code)` - Human-readable description
- `exit_code_from_exception(exc)` - Determine code from exception type

## Implementation Tasks

- [x] Define ExitCode enum
- [x] Define all standard codes
- [x] Implement description function
- [x] Implement exception-to-code mapping

## Success Criteria

- [x] All codes defined
- [x] Descriptions available
- [x] Exception mapping works

## Testing

- 3 tests in `tests/test_stability.py`
- All tests passing

## Related Documentation

- [F-110: Structured Logging](./F-110-structured-logging.md)
- [v0.9.5 Implementation](../../implementation/v0.9.5.md)

---

**Status**: Completed
