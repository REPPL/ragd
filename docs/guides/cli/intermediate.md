# CLI Intermediate Guide

Task-specific workflows for common ragd operations.

**Time:** 20 minutes
**Prerequisite:** [Essentials](./essentials.md)

---

## Workflow 1: Building Your Knowledge Base

### Index an entire folder

```bash
ragd index ~/Documents/research/
```

ragd will:
- Recursively find supported documents
- Skip already-indexed files
- Show progress as it processes

### Check what's indexed

```bash
ragd status
```

### Index specific file types only

```bash
# PDFs only
ragd index ~/Documents/ --include "*.pdf"

# Markdown only
ragd index ~/Notes/ --include "*.md"
```

---

## Workflow 2: Effective Searching

### Natural language queries

ragd understands meaning, not just keywords:

```bash
# These all work:
ragd search "what is machine learning"
ragd search "how does ML work"
ragd search "explain artificial intelligence basics"
```

### Limit results for focused reading

```bash
# Top 3 most relevant
ragd search "neural networks" --limit 3
```

### Get results for scripts

```bash
# JSON output
ragd search "authentication" --format json

# Plain text (no colours)
ragd search "authentication" --format plain
```

### Search with citations

```bash
# Show source with page numbers
ragd search "privacy regulations"

# Include direct quotes (v0.3+)
ragd search "privacy regulations" --quotes
```

---

## Workflow 3: Output Formats

### Rich output (default)

Best for interactive terminal use:

```bash
ragd search "machine learning"
```

### Plain output

For scripts, piping, or accessibility:

```bash
ragd search "machine learning" --format plain
# or
ragd search "machine learning" --plain
```

### JSON output

For programmatic integration:

```bash
ragd search "machine learning" --format json | jq '.results[0]'
```

---

## Workflow 4: Managing Your Index

### Check system health

```bash
ragd doctor
```

### View detailed statistics

```bash
ragd status --verbose
```

### Get JSON status for monitoring

```bash
ragd status --format json
```

---

## Workflow 5: Pipeline Integration

### Search and process results

```bash
# Extract just the content
ragd search "API endpoints" --format json | jq -r '.results[].content'

# Count results
ragd search "authentication" --format json | jq '.results | length'
```

### Conditional scripting

```bash
# Check if ragd is healthy
if ragd doctor --format json | jq -e '.status == "healthy"' > /dev/null; then
    echo "ragd is ready"
else
    echo "ragd needs attention"
fi
```

---

## Workflow 6: Citations and Sources

### View sources with results

Every search result shows its source:

```
1. paper.pdf (Score: 0.89)
   Page 5
   ┌────────────────────────────────┐
   │ The content...                 │
   └────────────────────────────────┘
```

### Academic citation formats (v0.3+)

```bash
# APA style
ragd search "climate change" --cite-style apa

# IEEE style
ragd search "neural networks" --cite-style ieee

# Export bibliography
ragd search "machine learning" --bibliography bibtex > refs.bib
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Index a folder | `ragd index ~/Documents/` |
| Search with limit | `ragd search "query" --limit 5` |
| JSON output | `ragd search "query" --format json` |
| Plain output | `ragd search "query" --plain` |
| Run health checks | `ragd doctor` |
| Detailed status | `ragd status --verbose` |

---

## What's Next?

- **[Advanced Guide](./advanced.md)** - Configuration, debugging, themes
- **[Reference](./reference.md)** - Complete flag specifications

---
