# F-006: Result Formatting

## Overview

**Use Case**: [UC-002: Search Knowledge](../../../use-cases/briefs/UC-002-search-knowledge.md)
**Milestone**: v0.1
**Priority**: P0

## Problem Statement

Search results must be displayed clearly and usefully. Users need to see the matching content, understand where it came from, and assess relevance at a glance.

## Design Approach

### Architecture

```
Search Results
    ↓
Result Formatter
    ├── TUI Navigator (default when TTY, interactive)
    ├── Rich Console (--no-interactive)
    ├── Plain Text (piping, scripts)
    └── JSON (programmatic access)
    ↓
Formatted Output
```

### Technologies

- **Textual**: Full-screen TUI with vim-style navigation (j/k)
- **Rich**: Beautiful terminal output with colours, panels, tables
- **Typer**: CLI integration with output format options

### Output Formats

| Format | Use Case | Features |
|--------|----------|----------|
| **TUI** | Interactive terminal (default) | Full-screen navigator, vim keys, status bar |
| **Rich** | Non-interactive terminal | Colours, panels, highlighting |
| **Plain** | Piping, scripts | Clean text, no ANSI codes |
| **JSON** | Programmatic | Structured data, machine-readable |

## Implementation Tasks

- [x] Create `ResultFormatter` base class
- [x] Implement `RichFormatter` with panels and highlighting
- [x] Implement `PlainFormatter` for script-friendly output
- [x] Implement `JSONFormatter` for programmatic access
- [x] Implement `SearchNavigator` TUI with Textual
- [x] Add relevance score visualisation (colour-coded)
- [x] Add source document path and chunk location
- [x] Write unit tests for formatters
- [x] Write integration tests with CLI

## Success Criteria

- [x] Results display clearly with source attribution
- [x] Relevance scores shown visually (red for score in status bar)
- [x] Content displayed in full-screen panel with navigation
- [x] JSON output is valid and complete
- [x] Plain output works correctly when piped
- [x] TUI activates when TTY detected; `--no-interactive` for non-TTY

## Dependencies

- Textual (TUI framework)
- Rich (console formatting)
- Typer (CLI integration)

## Technical Notes

### TUI Navigator (Default)

Full-screen interactive navigator with vim-style keybindings:

```
┌─────────────────────────────────────────────────────────────┐
│  Results for "authentication flow"                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────── auth-design.md ────────────────┐        │
│  │                                                 │        │
│  │  The authentication flow begins when the user   │        │
│  │  submits their credentials. The system          │        │
│  │  validates against the local database and       │        │
│  │  returns a session token...                     │        │
│  │                                                 │        │
│  └─────────────────────────────────────────────────┘        │
│  Chunk 3              [1/10]                    0.9200      │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  j Next  k Previous  q Quit                                 │
└─────────────────────────────────────────────────────────────┘
```

**Status bar:** Chunk number (left, blue), result count (centre, blue), score (right, red)

### Rich Output Example (--no-interactive)

```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 Search Results for: "authentication flow"                │
├─────────────────────────────────────────────────────────────┤
│ 1. auth-design.md (Score: 0.92)                             │
│    Chunk 3 of 12                                            │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ The authentication flow begins when the user submits    │ │
│ │ their credentials. The system validates against the     │ │
│ │ local database and returns a session token...           │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ 2. security-guide.pdf (Score: 0.87)                         │
│    Chunk 7 of 45                                            │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ JWT tokens are used for stateless authentication. Each  │ │
│ │ token contains the user ID and expiration timestamp...  │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### JSON Output Example

```json
{
  "query": "authentication flow",
  "results": [
    {
      "rank": 1,
      "score": 0.92,
      "document": "auth-design.md",
      "chunk_index": 3,
      "total_chunks": 12,
      "content": "The authentication flow begins when..."
    }
  ],
  "total_results": 2,
  "search_time_ms": 45
}
```

### Plain Output Example

```
Results for: authentication flow

1. [0.92] auth-design.md (chunk 3/12)
   The authentication flow begins when the user submits
   their credentials. The system validates against the
   local database and returns a session token...

2. [0.87] security-guide.pdf (chunk 7/45)
   JWT tokens are used for stateless authentication. Each
   token contains the user ID and expiration timestamp...
```

### CLI Integration

```bash
# Default: TUI navigator (when TTY detected)
ragd search "authentication"

# Non-interactive rich output
ragd search "authentication" --no-interactive

# Plain text for piping
ragd search "authentication" --format plain | head -20

# JSON for scripts
ragd search "authentication" --format json | jq '.results[0]'
```

## Related Documentation

- [State-of-the-Art CLI Modes](../../research/state-of-the-art-cli-modes.md) - Research basis for output format design
- [F-005: Semantic Search](./F-005-semantic-search.md) - Upstream provider
- [UC-002: Search Knowledge](../../../use-cases/briefs/UC-002-search-knowledge.md) - Parent use case

---
