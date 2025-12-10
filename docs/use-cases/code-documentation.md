# Use Case: Code Documentation

Code and technical documentation search with ragd.

## Scenario

You're a developer with extensive documentation. You want to:
- Search across API docs, READMEs, and wikis
- Find code examples quickly
- Understand legacy systems

## Setup

### Configuration

Edit `~/.ragd/config.yaml`:

```yaml
storage:
  data_dir: ~/.ragd/docs

chunking:
  strategy: recursive
  chunk_size: 512
  overlap: 50

search:
  mode: hybrid
  semantic_weight: 0.5  # Balance semantic and keyword
  keyword_weight: 0.5   # Important for code terms
```

### Initial Indexing

```bash
# Index project documentation
ragd index ~/projects/myapp/docs

# Index multiple projects
ragd index ~/projects/*/README.md
ragd index ~/projects/*/docs
```

## Workflow

### Finding API Details

```bash
ragd search "how to authenticate API requests"
```

### Understanding Errors

```bash
ragd search "ConnectionRefusedError handling" --mode keyword
```

### Code Examples

```bash
ragd search "example of using the database client"
```

### Onboarding New Codebase

```bash
ragd chat
> Explain the architecture of this system
```

## Example Queries

| Query | Purpose |
|-------|---------|
| "how to configure logging" | Config details |
| "API rate limiting implementation" | Feature docs |
| "error handling best practices" | Guidelines |
| "database migration steps" | Procedures |
| "authentication flow diagram" | Architecture |

## Tips

1. **Balanced weights** - Code terms need keyword matching
2. **Index READMEs** - Often the best overview
3. **Tag by project** - `project:api`, `project:frontend`
4. **Keyword for errors** - Use `--mode keyword` for error messages
5. **Regular updates** - Re-index when docs change

## Sample Session

```bash
# Find configuration docs
ragd search "environment variable configuration"

# Find specific error handling
ragd search "NotFoundException handler" --mode keyword

# Understand architecture
ragd chat
> How does the authentication service work?

# Find examples
ragd search "code example for pagination"
```

---

## Related Documentation

- [Tutorial: Getting Started](../tutorials/01-getting-started.md)
- [Tutorial: Powerful Searching](../tutorials/powerful-searching.md)
- [F-012: Hybrid Search](../development/features/completed/F-012-hybrid-search.md)

## Related Use Cases

- [Research Papers](research-papers.md) - Academic research
- [Meeting Notes](meeting-notes.md) - Work meetings
