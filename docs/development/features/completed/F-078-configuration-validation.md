# F-078: Configuration Validation

## Overview

**Milestone**: v0.6.5
**Priority**: P1
**Depends On**: [F-036](../completed/F-036-guided-setup.md)

## Problem Statement

Runtime errors from misconfiguration (wrong model name, missing directories, unreachable Ollama) are confusing. Users need a way to validate their configuration BEFORE running commands, with actionable fix suggestions.

## Design Approach

### CLI Command

```bash
ragd config --validate
```

### Validation Checks

| Check | Severity | Description |
|-------|----------|-------------|
| `data_dir` | ERROR | Directory exists and is writable |
| `chroma_path` | ERROR | Parent directory exists |
| `llm.model` | ERROR | Model available in Ollama |
| `embedding.model` | WARNING | Valid model name format |
| `contextual` | WARNING | Ollama reachable if enabled |
| `search_weights` | WARNING | Weights sum to 1.0 |
| `permissions` | INFO | Config file permissions secure |

### Output Format

```
+----------------------------------------------------------+
|  Configuration Validation                                |
+----------------------------------------------------------+

  [OK] data_dir             Data directory exists and is writable
  [OK] chroma_path          ChromaDB path parent exists
  [XX] llm.model            LLM model 'llama3.1:70b' not found
      -> Edit ~/.ragd/config.yaml: change llm.model to 'llama3.1:8b'
  [OK] embedding.model      Embedding model 'all-mpnet-base-v2' is valid
  [OK] contextual           Contextual retrieval is disabled
  [OK] search_weights       Search weights valid (semantic=0.7, keyword=0.3)

1 error, 0 warnings
```

### Severity Levels

- **ERROR**: Will cause runtime failures
- **WARNING**: May cause issues
- **INFO**: Informational only

## Implementation Tasks

- [x] Create `src/ragd/config_validator.py` module
- [x] Create `ValidationResult` dataclass
- [x] Create `ValidationReport` dataclass
- [x] Implement `ConfigValidator` class
- [x] Add Ollama model checking (`_get_ollama_models()`)
- [x] Add permission checking
- [x] Add `--validate` flag to config command
- [x] Format validation output with styles
- [x] Write unit tests

## Success Criteria

- [x] Detects missing/invalid LLM models
- [x] Checks directory existence and permissions
- [x] Validates search weight configuration
- [x] Provides actionable fix suggestions
- [x] Non-blocking info-level notices

## Files Changed

- `src/ragd/config_validator.py` - New validation module
- `src/ragd/cli.py` - Config command `--validate` flag
- `src/ragd/ui/cli/commands.py` - Validation output formatting

## Related Documentation

- [F-036: Guided Setup](../completed/F-036-guided-setup.md)
- [Configuration Guide](../../../guides/configuration.md)

---

**Status**: Complete
