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
    ├── Rich Console (default, interactive)
    ├── Plain Text (piping, scripts)
    └── JSON (programmatic access)
    ↓
Formatted Output
```

### Technologies

- **Rich**: Beautiful terminal output with colours, panels, tables
- **Typer**: CLI integration with output format options

### Output Formats

| Format | Use Case | Features |
|--------|----------|----------|
| **Rich** | Interactive terminal | Colours, panels, highlighting |
| **Plain** | Piping, scripts | Clean text, no ANSI codes |
| **JSON** | Programmatic | Structured data, machine-readable |

## Implementation Tasks

- [ ] Create `ResultFormatter` base class
- [ ] Implement `RichFormatter` with panels and highlighting
- [ ] Implement `PlainFormatter` for script-friendly output
- [ ] Implement `JSONFormatter` for programmatic access
- [ ] Add query term highlighting in results
- [ ] Add relevance score visualisation
- [ ] Add source document path and location
- [ ] Write unit tests for each formatter
- [ ] Write integration tests with CLI

## Success Criteria

- [ ] Results display clearly with source attribution
- [ ] Relevance scores shown visually
- [ ] Content snippets highlight matching context
- [ ] JSON output is valid and complete
- [ ] Plain output works correctly when piped
- [ ] Rich output degrades gracefully in non-TTY

## Dependencies

- Rich
- Typer

## Technical Notes

### Rich Output Example

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
# Default rich output
ragd search "authentication"

# Plain text for piping
ragd search "authentication" --format plain | head -20

# JSON for scripts
ragd search "authentication" --format json | jq '.results[0]'
```

## Related Documentation

- [F-005: Semantic Search](./F-005-semantic-search.md) - Upstream provider
- [UC-002: Search Knowledge](../../../use-cases/briefs/UC-002-search-knowledge.md) - Parent use case

---
