# F-005: Semantic Search

## Overview

**Use Case**: [UC-002: Search Knowledge](../../../use-cases/briefs/UC-002-search-knowledge.md)
**Milestone**: v0.1
**Priority**: P0

## Problem Statement

Users need to find relevant information using natural language queries. The search must be semantic (understanding meaning, not just keywords) and return ranked results with source context.

## Design Approach

### Architecture

```
User Query
    ↓
Query Embedding (same model as indexing)
    ↓
Vector Similarity Search (ChromaDB)
    ↓
Ranked Results with Metadata
    ↓
[F-006: Result Formatting]
```

### Technologies

- **ChromaDB**: Vector similarity search with metadata filtering
- **sentence-transformers**: Query embedding (same model as indexing)

### Search Interface

```python
@dataclass
class SourceLocation:
    """Location within a document for citation."""
    page_number: int | None = None
    char_start: int | None = None
    char_end: int | None = None

@dataclass
class SearchResult:
    content: str
    score: float
    document_id: str
    document_name: str
    chunk_index: int
    metadata: dict[str, Any]
    # Citation support (v0.1)
    location: SourceLocation | None = None

class Searcher(Protocol):
    def search(
        self,
        query: str,
        limit: int = 10,
        filters: dict | None = None
    ) -> list[SearchResult]:
        """Search for relevant chunks."""
        ...
```

## Implementation Tasks

- [ ] Define `SearchResult` dataclass with `SourceLocation` for citations
- [ ] Define `Searcher` protocol
- [ ] Implement `SemanticSearcher` using ChromaDB
- [ ] Add query embedding using same model as indexing
- [ ] Implement result ranking by similarity score
- [ ] Add metadata filtering support
- [ ] Create `ragd search` CLI command
- [ ] Handle empty results gracefully
- [ ] Include source location (page number) in results
- [ ] Pass citation data to F-006 Result Formatting
- [ ] Write unit tests for search logic
- [ ] Write integration tests with indexed documents

## Success Criteria

- [ ] Natural language queries return relevant results
- [ ] Results ranked by semantic similarity
- [ ] Source document and location included in results
- [ ] Page numbers displayed for PDF sources (citation support)
- [ ] Search completes within 2 seconds
- [ ] Empty results handled with helpful message
- [ ] Configurable result limit (default 10)
- [ ] Citation data available in JSON output

## Dependencies

- ChromaDB
- sentence-transformers (same model as indexing)

## Technical Notes

### CLI Interface

```bash
# Basic search
ragd search "how does authentication work"

# With options
ragd search "authentication" --limit 5 --format json

# With metadata filter (future)
ragd search "authentication" --tag security
```

### ChromaDB Query

```python
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=limit,
    where=filters,
    include=["documents", "metadatas", "distances"]
)
```

### Similarity Scoring

ChromaDB returns distances. Convert to similarity scores:

```python
# For cosine distance
similarity = 1 - distance

# Normalise to 0-1 range for display
score = max(0, min(1, similarity))
```

### No Results Handling

```
No results found for "quantum mechanics"

Suggestions:
- Try different keywords
- Check if relevant documents are indexed (ragd status)
- Use broader search terms
```

## Related Documentation

- [F-004: Embedding Generation](./F-004-embedding-generation.md) - Query embedding
- [F-006: Result Formatting](./F-006-result-formatting.md) - Downstream display
- [F-009: Citation Output](./F-009-citation-output.md) - Citation formatting
- [ADR-0006: Citation System](../../decisions/adrs/0006-citation-system.md) - Citation architecture
- [UC-002: Search Knowledge](../../../use-cases/briefs/UC-002-search-knowledge.md) - Parent use case

---
