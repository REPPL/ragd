# F-063: Smart Collections

## Overview

**Use Case**: Virtual document organisation without folder hierarchies
**Milestone**: v0.7.0 (stretch goal)
**Priority**: P2
**Depends On**: [F-031](../completed/F-031-tag-management.md)

## Problem Statement

Traditional folder hierarchies force documents into a single location, but documents often belong to multiple categories. Copying creates duplication; symlinks are fragile. Users need **virtual folders** based on tag queries that automatically include matching documents without moving or duplicating files.

## Design Approach

Implement **smart collections** as saved tag queries with boolean logic (AND, OR, NOT). Collections auto-update as documents are tagged—no manual membership management needed. Collections can be nested for hierarchical organisation.

**Smart Collection Concept:**
```
Collection: "Q3 Finance Reports"
Query: finance AND q3-2024 AND NOT draft
Result: All documents tagged with both "finance" and "q3-2024", excluding drafts
Auto-updates: New matching documents automatically appear
```

**CLI Interface:**
```bash
# Create a collection
ragd collection create "Q3 Finance" \
  --include-all finance q3-2024 \
  --exclude draft

# Create with OR logic
ragd collection create "Research" \
  --include-any academic research papers

# Create with complex query
ragd collection create "Active Projects" \
  --include-any project/alpha project/beta project/gamma \
  --exclude archived status/draft

# List all collections
ragd collection list
# Output:
#   Q3 Finance         12 docs   finance AND q3-2024 NOT draft
#   Research           45 docs   academic OR research OR papers
#   Active Projects    23 docs   project/* NOT archived NOT status/draft

# View collection contents
ragd collection show "Q3 Finance"
# Output:
#   Q3 Finance (12 documents)
#   Query: finance AND q3-2024 NOT draft
#
#   doc-001  Q3 Revenue Analysis.pdf       [finance, q3-2024, approved]
#   doc-015  Quarterly Budget Review.pdf   [finance, q3-2024, review]
#   ...

# Search within collection
ragd search "revenue growth" --collection "Q3 Finance"

# Update collection query
ragd collection update "Q3 Finance" --exclude draft review

# Delete collection (not the documents)
ragd collection delete "Q3 Finance"

# Export collection as document list
ragd collection export "Q3 Finance" --format json > q3_docs.json

# Nested collections
ragd collection create "Finance" --include-all finance
ragd collection create "Finance/Q3" --parent "Finance" --include-all q3-2024
ragd collection create "Finance/Q4" --parent "Finance" --include-all q4-2024
```

## Implementation Tasks

- [ ] Create `Collection` dataclass with `TagQuery`
- [ ] Implement `TagQuery` with AND/OR/NOT logic
- [ ] Add collection storage to metadata database
- [ ] Implement `ragd collection create` command
- [ ] Implement `ragd collection list` command
- [ ] Implement `ragd collection show` command
- [ ] Implement `ragd collection update` command
- [ ] Implement `ragd collection delete` command
- [ ] Add `--collection` filter to `ragd search`
- [ ] Implement collection nesting (parent/child)
- [ ] Add collection export functionality
- [ ] Integrate with existing `find_by_tags()` method

## Success Criteria

- [ ] Collections created with tag queries
- [ ] AND, OR, NOT logic works correctly
- [ ] Collections auto-update when documents tagged
- [ ] Search can be scoped to collection
- [ ] Nested collections supported
- [ ] Collections persist across sessions
- [ ] Collection deletion doesn't affect documents
- [ ] Wildcard patterns supported (e.g., `project/*`)

## Dependencies

- [F-031: Tag Management](../completed/F-031-tag-management.md) - Tag queries build on `find_by_tags()`
- [F-005: Semantic Search](../completed/F-005-semantic-search.md) - Collection-scoped search

## Technical Notes

**TagQuery Schema:**
```python
@dataclass
class TagQuery:
    """Boolean combination of tags for collection membership."""

    include_all: list[str] = field(default_factory=list)  # AND logic
    include_any: list[str] = field(default_factory=list)  # OR logic
    exclude: list[str] = field(default_factory=list)      # NOT logic

    def matches(self, doc_tags: list[str]) -> bool:
        """Check if document tags match this query."""
        doc_set = set(doc_tags)

        # Must have ALL include_all tags
        if self.include_all:
            # Support wildcards like "project/*"
            for tag in self.include_all:
                if tag.endswith("/*"):
                    prefix = tag[:-1]  # "project/"
                    if not any(t.startswith(prefix) for t in doc_set):
                        return False
                elif tag not in doc_set:
                    return False

        # Must have at least ONE include_any tag (if specified)
        if self.include_any:
            matched = False
            for tag in self.include_any:
                if tag.endswith("/*"):
                    prefix = tag[:-1]
                    if any(t.startswith(prefix) for t in doc_set):
                        matched = True
                        break
                elif tag in doc_set:
                    matched = True
                    break
            if not matched:
                return False

        # Must NOT have any exclude tags
        if self.exclude:
            for tag in self.exclude:
                if tag.endswith("/*"):
                    prefix = tag[:-1]
                    if any(t.startswith(prefix) for t in doc_set):
                        return False
                elif tag in doc_set:
                    return False

        return True

    def to_string(self) -> str:
        """Human-readable query representation."""
        parts = []
        if self.include_all:
            parts.append(" AND ".join(self.include_all))
        if self.include_any:
            parts.append(f"({' OR '.join(self.include_any)})")
        if self.exclude:
            parts.append(f"NOT ({' OR '.join(self.exclude)})")
        return " AND ".join(parts) if parts else "*"


@dataclass
class Collection:
    """A saved tag query that auto-collects matching documents."""

    id: str
    name: str
    query: TagQuery
    description: str = ""
    parent_id: str | None = None  # For nested collections
    created_at: datetime = field(default_factory=datetime.now)

    def get_documents(self, tag_manager: TagManager) -> list[str]:
        """Get all document IDs matching this collection's query."""
        # This is a live query - results update automatically
        all_docs = tag_manager._store.list_ids()
        return [
            doc_id for doc_id in all_docs
            if self.query.matches(tag_manager.get(doc_id))
        ]
```

**Storage:**
```sql
CREATE TABLE collections (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    parent_id TEXT REFERENCES collections(id),
    include_all TEXT,  -- JSON array
    include_any TEXT,  -- JSON array
    exclude TEXT,      -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_collections_parent ON collections(parent_id);
```

**Performance Consideration:**

For large knowledge bases, collection membership can be cached:
```python
# Optional: materialised collection membership
CREATE TABLE collection_members (
    collection_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    PRIMARY KEY (collection_id, document_id)
);

# Rebuild on tag changes (trigger or explicit refresh)
```

## WebUI Integration (v1.0)

Smart collections enable powerful UI features:
- **Sidebar navigation** with collection hierarchy
- **Collection-scoped search** via dropdown
- **Drag-and-drop** documents to collections (adds required tags)
- **Collection badges** showing document counts
- **Quick filters** for common collections

## Related Documentation

- [State-of-the-Art Tagging](../../research/state-of-the-art-tagging.md)
- [F-031: Tag Management](../completed/F-031-tag-management.md)
- [F-061: Auto-Tag Suggestions](./F-061-auto-tag-suggestions.md)
- [F-062: Tag Library](./F-062-tag-library.md)

