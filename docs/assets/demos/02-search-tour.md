# Search Tour Demo

A 2-3 minute video walkthrough of ragd's search capabilities.

## Demo Script

### Scene 1: Introduction (15s)

"Let's explore ragd's powerful search features..."

### Scene 2: Basic Search (30s)

```bash
# Natural language search
ragd search "how to configure database connections"
```

Show results with citations and relevance scores.

### Scene 3: Search Modes (45s)

```bash
# Semantic search - conceptual matching
ragd search "user authentication" --mode semantic

# Keyword search - exact terms
ragd search "OAuth2" --mode keyword

# Hybrid search - best of both
ragd search "OAuth authentication flow" --mode hybrid
```

### Scene 4: Filters (30s)

```bash
# Filter by tag
ragd search "config" --tag "project:alpha"

# Filter by date
ragd search "meeting" --after 2024-01-01

# Limit results
ragd search "error" --limit 3
```

### Scene 5: Wrap-up (15s)

"With semantic, keyword, and hybrid modes, ragd helps you find exactly what you need."

## Recording Notes

- **Duration:** 2-3 minutes
- **Terminal size:** 100x30
- **Pause:** 2s after each command
- **Highlight:** Result citations

---

## Related Documentation

- [Quick Start Demo](01-quick-start.md)
- [Tutorial: Powerful Searching](../../tutorials/powerful-searching.md)

---

**Status**: Stub - recording planned
