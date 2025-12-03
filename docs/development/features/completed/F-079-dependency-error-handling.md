# F-079: Dependency Error Handling

## Overview

**Milestone**: v0.6.5
**Priority**: P2
**Depends On**: None

## Problem Statement

When optional dependencies are missing, users see raw Python tracebacks. They need clear, user-friendly error messages with installation instructions.

## Design Approach

### Error Display Format

```
+-- Missing Optional Dependency ------------------------------+
|                                                            |
|  The 'pdf' feature is required for this operation.         |
|                                                            |
|  To install:                                               |
|    pip install ragd[pdf]                                   |
|                                                            |
|  Then run:                                                 |
|    ragd index --reprocess                                  |
|                                                            |
+------------------------------------------------------------+
```

### Error Handling Hierarchy

1. **CLI Error Formatter** - Catches known exceptions
2. **Dependency Check** - Validates before operations
3. **Graceful Fallback** - Skip feature if non-critical

### Error Types

| Error Type | Message | Suggestion |
|------------|---------|------------|
| `MissingPDFDependency` | PDF processing unavailable | `pip install ragd[pdf]` |
| `MissingOCRDependency` | OCR processing unavailable | `pip install ragd[ocr]` |
| `MissingHTMLDependency` | HTML parsing unavailable | `pip install ragd[html]` |
| `OllamaUnavailable` | Cannot connect to Ollama | `ollama serve` |

## Implementation Tasks

- [x] Create `src/ragd/ui/cli/errors.py` module
- [x] Add `print_dependency_error()` function to styles
- [x] Create error handler for CLI commands
- [x] Add ASCII-boxed error display
- [x] Include install commands in error messages
- [x] Add optional "then run" step for post-install
- [x] Write unit tests

## Success Criteria

- [x] Missing dependencies show user-friendly message
- [x] Install commands are copy-paste ready
- [x] ASCII boxes provide visual structure
- [x] Post-install steps shown when relevant
- [x] Raw tracebacks hidden from users

## Files Changed

- `src/ragd/ui/cli/errors.py` - New error handling module
- `src/ragd/ui/styles.py` - `print_dependency_error()` function
- `src/ragd/ui/cli/__init__.py` - Error handler exports

## Related Documentation

- [Installation Guide](../../../tutorials/getting-started.md)

---

**Status**: Complete
