# F-077: CLI Visual Polish

## Overview

**Milestone**: v0.6.5
**Priority**: P2
**Depends On**: None

## Problem Statement

The CLI output lacks visual consistency and polish. Progress bars show filenames at the start (truncating important info), there's no feedback during LLM thinking time, and status output lacks structure.

## Design Approach

### Progress Bar Enhancement

Before:
```
filename.pdf: Indexing... ━━━━━ 17/19
```

After:
```
Indexing... ━━━━━ 17/19 (filename.pdf)
```

### Chat Thinking Spinner

When waiting for LLM response:
```
⠹ Thinking...
```

Transitions to "Assistant:" when response starts streaming.

### ASCII Art Banners

Standardised header format for major commands:

```
+----------------------------------------------------------+
|  ragd Setup                                              |
|  Local RAG for personal knowledge management             |
+----------------------------------------------------------+
```

### Doctor Output Enhancement

Categorised health checks with clear status indicators:

```
+-- System Health -------------------------------------------+
|  Overall: HEALTHY                                          |
+------------------------------------------------------------+

  [OK] Ollama             Running
  [OK] Embedding model    all-mpnet-base-v2 loaded
  [!!] ChromaDB           3 orphaned documents
```

## Implementation Tasks

- [x] Create `src/ragd/ui/styles.py` module
- [x] Add `Icons` class with ASCII status indicators
- [x] Add `print_banner()` function
- [x] Add `print_chat_header()` function
- [x] Add `print_init_header()` function
- [x] Add `print_doctor_header()` function
- [x] Add `format_health_check()` function
- [x] Update progress bar description format
- [x] Add thinking spinner to chat command
- [x] Integrate styles into CLI commands

## Success Criteria

- [x] Progress bar shows filename at end in parentheses
- [x] Chat shows "Thinking..." spinner during LLM wait
- [x] ASCII banners display for chat, init, doctor
- [x] Health checks display with categorised icons
- [x] Visual output consistent across commands

## Files Changed

- `src/ragd/ui/styles.py` - New visual standards module
- `src/ragd/ui/cli/commands.py` - Banner and spinner integration
- `src/ragd/ui/formatters.py` - Progress bar format

## Related Documentation

- [CLI Reference](../../../guides/cli/reference.md)
