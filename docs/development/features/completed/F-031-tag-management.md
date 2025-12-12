# F-031: Tag Management

## Overview

**Use Case**: [UC-005](../../../use-cases/briefs/UC-005-manage-metadata.md)
**Milestone**: v0.2
**Priority**: P1

## Problem Statement

Users need to organise their knowledge base by topic, project, or custom categories. While automatic keyword extraction provides some organisation, user-defined tags enable personal taxonomies that match individual workflows.

## Design Approach

Implement a flexible tagging system supporting user-defined tags, tag hierarchies, and bulk operations.

**Tag Model:**
```python
@dataclass
class Tag:
    name: str           # Tag identifier (lowercase, no spaces)
    display_name: str   # Human-readable name
    colour: str         # Optional colour for UI
    parent: str | None  # For hierarchical tags
    created_at: datetime
    document_count: int # Cached count

# Example hierarchy:
# work/
#   work/project-alpha
#   work/project-beta
# personal/
#   personal/health
#   personal/finance
```

**CLI Interface:**
```bash
# Add tags to document
ragd meta tag <doc-id> work project-alpha

# Remove tags
ragd meta untag <doc-id> old-tag

# List all tags
ragd meta tags

# Bulk tagging
ragd meta tag --query "finance reports" quarterly

# Search by tag
ragd search "revenue" --tag work/project-alpha
```

## Implementation Tasks

- [ ] Create Tag model and storage schema
- [ ] Implement tag CRUD operations
- [ ] Add `ragd meta tag` command
- [ ] Add `ragd meta untag` command
- [ ] Add `ragd meta tags` listing command
- [ ] Implement bulk tagging by query
- [ ] Add tag filtering to search command
- [ ] Implement tag hierarchy (optional parent)
- [ ] Add tag auto-completion for CLI
- [ ] Sync tags to ChromaDB metadata

## Success Criteria

- [ ] Users can add/remove tags from documents
- [ ] Tags filterable in search results
- [ ] Bulk tagging supported
- [ ] Tag listing shows document counts
- [ ] Tag names validated (no spaces, lowercase)
- [ ] Tags persisted in metadata storage

## Dependencies

- [F-029: Metadata Storage](./F-029-metadata-storage.md) - Stores tags
- [F-005: Semantic Search](./F-005-semantic-search.md) - Tag filtering

## Technical Notes

**Tag Storage in SQLite:**
```sql
CREATE TABLE tags (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    display_name TEXT,
    colour TEXT,
    parent_id INTEGER REFERENCES tags(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE document_tags (
    document_id TEXT NOT NULL,
    tag_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (document_id, tag_id),
    FOREIGN KEY (tag_id) REFERENCES tags(id)
);
```

**ChromaDB Metadata Sync:**
```python
# When tags change, update ChromaDB metadata
def sync_tags_to_chromadb(doc_id: str, tags: list[str]):
    # Get all chunks for document
    chunks = collection.get(where={"doc_id": doc_id})

    # Update each chunk's metadata
    for chunk_id in chunks['ids']:
        collection.update(
            ids=[chunk_id],
            metadatas=[{"ragd_tags": tags}]
        )
```

**Tag Validation:**
```python
def validate_tag_name(name: str) -> str:
    """Normalise and validate tag name."""
    # Lowercase, replace spaces with hyphens
    normalised = name.lower().strip().replace(" ", "-")

    # Only allow alphanumeric, hyphens, slashes (for hierarchy)
    if not re.match(r'^[a-z0-9\-/]+$', normalised):
        raise ValueError(f"Invalid tag name: {name}")

    return normalised
```

## Related Documentation

- [State-of-the-Art Metadata](../../research/state-of-the-art-metadata.md)
- [F-029: Metadata Storage](./F-029-metadata-storage.md)
- [UC-005: Manage Metadata](../../../use-cases/briefs/UC-005-manage-metadata.md)

