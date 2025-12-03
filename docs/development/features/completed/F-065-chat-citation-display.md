# F-065: Chat Citation Display

**Status**: Completed
**Version**: v0.7.0
**Priority**: High

---

## Problem Statement

The chat system retrieves relevant context using the RAG pipeline and computes citations for each response, but citations are never displayed to the user. This makes it impossible to verify sources or understand where information came from.

Users reported "generic answers without citations" when using the chat interface, despite the underlying system correctly computing citation data.

---

## Design Approach

### Root Cause Analysis

1. **Missing CLI flag**: `chat_command()` had no `--cite` option
2. **No display logic**: After streaming response, citations were discarded
3. **Hidden data**: `CitedAnswer` contains citations but they weren't surfaced

### Solution

1. Add `--cite` / `-c` option to chat command
2. Default citation mode configurable via `config.chat.default_cite_mode`
3. Display citations after streaming completes in numbered format

---

## Implementation

### Files Modified

- `src/ragd/ui/cli/commands.py` - Added citation display logic
- `src/ragd/cli.py` - Added `--cite` option to chat command registration

### Citation Display Format

```
Sources:
  [1] document.pdf, p. 5
  [2] notes.md
  [3] report.pdf, p. 12
```

### Citation Modes

| Mode | Description |
|------|-------------|
| `numbered` | Display numbered source list (default) |
| `none` | Suppress citation display |

---

## Success Criteria

- [x] Citations display after chat responses
- [x] `--cite` flag controls display mode
- [x] Default mode configurable in `config.yaml`
- [x] Page numbers shown when available
- [x] All tests pass

---

## Dependencies

- F-066: Configurable Chat Prompts (implemented together)
- Existing `ChatSession` and `Citation` infrastructure

---

## Related Documentation

- [F-066: Configurable Chat Prompts](./F-066-configurable-chat-prompts.md)
- [F-009: Citation Output](./F-009-citation-output.md)

---

**Status**: Completed
