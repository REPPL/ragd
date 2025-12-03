# F-071: Metadata Proxy Layer

## Overview

**Milestone**: v0.6.0
**Priority**: P1
**Depends On**: [F-021](./F-021-vector-store-abstraction.md)

## Problem Statement

FAISS does not natively support metadata storage or filtering. To enable ChromaDB-style `where` filters with FAISS, ragd needs a metadata proxy layer that stores metadata separately (SQLite) and translates filter queries.

## Design Approach

### Architecture

```
FAISS Query Flow:
┌─────────────────────────────────────────────┐
│  HybridSearcher                             │
│    where={"document_id": "doc123"}          │
└────────────────┬────────────────────────────┘
                 ↓
┌────────────────────────────────────────────┐
│  MetadataProxy                              │
│    1. Translate where → SQL                 │
│    2. Query SQLite for matching IDs         │
│    3. Pass ID filter to FAISS               │
└────────────────┬────────────────────────────┘
                 ↓
┌────────────────────────────────────────────┐
│  FAISSAdapter                               │
│    Search with ID pre-filter                │
└────────────────────────────────────────────┘
```

### SQLite Schema

```sql
CREATE TABLE faiss_vectors (
    faiss_id INTEGER PRIMARY KEY,
    chunk_id TEXT UNIQUE NOT NULL,
    document_id TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSON,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_chunk_id ON faiss_vectors(chunk_id);
CREATE INDEX idx_document_id ON faiss_vectors(document_id);
```

### MetadataProxy Protocol

```python
@runtime_checkable
class MetadataProxy(Protocol):
    def add(self, chunk_id: str, document_id: str, content: str, metadata: dict) -> int:
        """Add metadata, return faiss_id."""
        ...

    def get(self, chunk_id: str) -> dict | None:
        """Get metadata by chunk ID."""
        ...

    def filter(self, where: dict) -> list[int]:
        """Return faiss_ids matching filter."""
        ...

    def delete(self, chunk_ids: list[str]) -> int:
        """Delete by chunk IDs, return count."""
        ...
```

## Implementation Tasks

- [ ] Create `src/ragd/storage/metadata/` module
- [ ] Define `MetadataProxy` protocol
- [ ] Implement `SQLiteMetadataStore`
- [ ] Implement ChromaDB filter → SQL translation
- [ ] Add batch operations for performance
- [ ] Write unit tests for CRUD
- [ ] Write filter translation tests

## Success Criteria

- [ ] FAISS can filter by document_id, tags, etc.
- [ ] Filter translation handles common ChromaDB patterns
- [ ] Batch operations are memory-efficient
- [ ] SQLite database is co-located with FAISS index

## Related Documentation

- [F-021: Vector Store Abstraction](./F-021-vector-store-abstraction.md)

---
