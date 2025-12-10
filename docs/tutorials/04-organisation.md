# Organising Your Knowledge Base

Learn how to use tags, collections, and metadata to organise your documents.

**Time:** 20 minutes
**Level:** Intermediate
**Prerequisites:** Completed Getting Started tutorial, indexed documents

## What You'll Learn

- Adding and managing tags
- Creating smart collections
- Editing document metadata
- Building a tag taxonomy
- Finding documents by organisation

## Tags: The Foundation

Tags are labels you attach to documents. They're the building blocks of organisation.

### Adding Tags

```bash
# Add a single tag
ragd tag add doc-123 important

# Add multiple tags at once
ragd tag add doc-123 "topic:machine-learning" "status:reading" urgent
```

**Tip:** Use `namespace:value` format for structured tags (e.g., `topic:nlp`, `project:alpha`).

### Viewing Tags

```bash
# List all tags in your knowledge base
ragd tag list

# Show tags with document counts
ragd tag list --counts

# Show tags for a specific document
ragd tag list doc-123
```

### Removing Tags

```bash
# Remove a tag from a document
ragd tag remove doc-123 urgent

# Remove multiple tags
ragd tag remove doc-123 draft "status:reading"
```

### Finding Documents by Tag

```bash
# Search within tagged documents
ragd search "neural networks" --tag "topic:ml"

# List documents with a specific tag
ragd list --tag "project:alpha"
```

## Smart Collections

Collections are saved queries that automatically include matching documents. When you tag a document, it automatically appears in relevant collections.

### Creating Collections

```bash
# Simple collection: all documents with a tag
ragd collection create "Machine Learning" --include-all "topic:ml"

# AND logic: must have ALL tags
ragd collection create "Active ML Projects" \
  --include-all "topic:ml" "status:active"

# OR logic: must have at least ONE tag
ragd collection create "Research" \
  --include-any "topic:ml" "topic:nlp" "topic:cv"

# Exclusion: must NOT have these tags
ragd collection create "Active Projects" \
  --include-all "project:*" \
  --exclude "status:archived" "status:draft"
```

### Collection Logic

| Option | Logic | Example |
|--------|-------|---------|
| `--include-all` | AND | All listed tags must be present |
| `--include-any` | OR | At least one tag must be present |
| `--exclude` | NOT | None of the listed tags may be present |

### Viewing Collections

```bash
# List all collections
ragd collection list

# Show collection contents
ragd collection show "Machine Learning"

# Show more results
ragd collection show "Research" --limit 50
```

### Updating Collections

```bash
# Add exclusion to existing collection
ragd collection update "Active Projects" --exclude draft

# Change description
ragd collection update "Research" --description "Academic papers and notes"
```

### Nested Collections

Create hierarchies with parent collections:

```bash
# Create parent collection
ragd collection create "Finance" --include-all "topic:finance"

# Create child collections
ragd collection create "Q3 Reports" \
  --include-all "quarter:q3" \
  --parent "Finance"

ragd collection create "Q4 Reports" \
  --include-all "quarter:q4" \
  --parent "Finance"

# List children of a parent
ragd collection list --parent "Finance"
```

## Document Metadata

Beyond tags, documents have structured metadata you can edit.

### Viewing Metadata

```bash
# Show document metadata
ragd meta show doc-123
```

### Editing Metadata

```bash
# Set document title
ragd meta edit doc-123 --title "Q3 Financial Report"

# Set multiple fields
ragd meta edit doc-123 \
  --title "Research Notes" \
  --creator "Smith, J." \
  --project "Alpha"

# Multiple creators (semicolon-separated)
ragd meta edit doc-123 --creator "Smith, J.; Doe, A.; Chen, L."
```

### Available Metadata Fields

| Field | Description | Example |
|-------|-------------|---------|
| `--title` | Document title | "Meeting Notes 2024-01-15" |
| `--creator` | Author(s) | "Smith, J.; Doe, A." |
| `--description` | Summary | "Weekly planning meeting" |
| `--type` | Document type | "report", "notes", "article" |
| `--project` | Project name | "Project Alpha" |

## Building a Tag Taxonomy

A consistent tagging system makes organisation easier. Here's a recommended approach:

### Namespace Convention

Use `namespace:value` format:

```bash
# Topic tags
ragd tag add doc-123 "topic:machine-learning"
ragd tag add doc-123 "topic:python"

# Status tags
ragd tag add doc-123 "status:reading"
ragd tag add doc-123 "status:reviewed"

# Project tags
ragd tag add doc-123 "project:thesis"

# Priority tags
ragd tag add doc-123 "priority:high"
```

### Suggested Namespaces

| Namespace | Values | Purpose |
|-----------|--------|---------|
| `topic:` | ml, nlp, cv, finance | Subject matter |
| `status:` | draft, reading, reviewed, archived | Workflow state |
| `project:` | alpha, thesis, client-x | Project association |
| `type:` | article, book, notes, code | Document type |
| `priority:` | high, medium, low | Importance |
| `year:` | 2024, 2023 | Publication year |

### Example Taxonomy Setup

```bash
# Index documents
ragd index ~/Papers/

# Apply consistent tags
ragd tag add paper-001 "topic:nlp" "status:reading" "year:2024"
ragd tag add paper-002 "topic:nlp" "status:reviewed" "year:2023"
ragd tag add paper-003 "topic:ml" "status:reading" "year:2024"

# Create collections based on taxonomy
ragd collection create "NLP Papers" --include-all "topic:nlp"
ragd collection create "To Read" --include-all "status:reading"
ragd collection create "2024 Papers" --include-all "year:2024"
```

## Verification

You've succeeded if:
- [ ] `ragd tag list --counts` shows your tags
- [ ] `ragd collection list` shows your collections
- [ ] `ragd collection show "Collection Name"` shows matching documents
- [ ] Documents automatically appear in collections when tagged

## Example Workflow

```bash
# 1. Index new documents
ragd index ~/Downloads/new-papers/

# 2. Review and tag each document
ragd meta show doc-456
ragd tag add doc-456 "topic:transformers" "status:reading" "priority:high"

# 3. Create a collection for your current focus
ragd collection create "Transformer Research" \
  --include-all "topic:transformers" \
  --exclude "status:archived"

# 4. Search within your collection
ragd search "attention mechanism" --tag "topic:transformers"

# 5. When done reading, update status
ragd tag remove doc-456 "status:reading"
ragd tag add doc-456 "status:reviewed"
```

## Next Steps

- [Backing Up Your Data](backing-up-data.md) - Export and backup
- [Powerful Searching](powerful-searching.md) - Advanced search techniques

---

## Tips

1. **Start simple** - Begin with a few tags, add more as needed
2. **Be consistent** - Use the same tag format throughout
3. **Use namespaces** - `topic:x` is clearer than just `x`
4. **Collections auto-update** - Tag documents, they appear automatically
5. **Review regularly** - Prune unused tags with `ragd tag list --counts`

---

## Related Documentation

- [Tutorial: Getting Started](01-getting-started.md)
- [F-031: Tag Management](../development/features/completed/F-031-tag-management.md)
- [F-063: Smart Collections](../development/features/completed/F-063-smart-collections.md)
