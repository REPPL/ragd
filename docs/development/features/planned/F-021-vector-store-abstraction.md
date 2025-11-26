# F-021: Vector Store Abstraction

## Overview

**Research**: Vector database comparison research (to be created)
**Milestone**: v0.6
**Priority**: P2

## Problem Statement

ragd currently couples tightly to ChromaDB. Users may want different backends based on their needs: FAISS for pure performance, Qdrant for advanced features, or experimental backends like LEANN. An abstraction layer enables backend choice without changing user workflows.

## Design Approach

### Architecture

```
ragd Application
    ↓
VectorStore Protocol
    ↓
┌────────────────────────────────────────┐
│              Adapters                   │
├──────────┬───────────┬────────┬────────┤
│ ChromaDB │   FAISS   │ Qdrant │ LEANN  │
│(default) │           │        │(exper.)|
└──────────┴───────────┴────────┴────────┘
```

### Technologies

- **Protocol-based design**: Type-safe abstraction
- **ChromaDB**: Current default (maintained)
- **FAISS**: High-performance alternative
- **LEANN**: Experimental learned index

### Backend Comparison

| Backend | Pros | Cons | Best For |
|---------|------|------|----------|
| **ChromaDB** | Easy, metadata-rich | Slower at scale | Default, small-medium |
| **FAISS** | Very fast, battle-tested | Less metadata | Large collections |
| **Qdrant** | Feature-rich, filtering | Heavier | Advanced queries |
| **LEANN** | Research, custom | Experimental | Experimentation |

## Implementation Tasks

- [ ] Define `VectorStore` protocol
- [ ] Create `VectorStoreFactory` with backend selection
- [ ] Refactor ChromaDB to adapter pattern
- [ ] Implement FAISS adapter
- [ ] Implement migration tool between backends
- [ ] Create LEANN experimental adapter
- [ ] Add backend health checks
- [ ] Update configuration for backend selection
- [ ] Write unit tests for each adapter
- [ ] Write integration tests for migration

## Success Criteria

- [ ] Backend swappable via configuration
- [ ] ChromaDB works unchanged (no regression)
- [ ] FAISS backend functional
- [ ] Migration preserves all data
- [ ] Consistent API across backends
- [ ] Performance benchmarks documented

## Dependencies

- chromadb (existing)
- faiss-cpu or faiss-gpu
- numpy (vector operations)

## Technical Notes

### VectorStore Protocol

```python
from typing import Protocol

@dataclass
class SearchResult:
    id: str
    score: float
    content: str
    metadata: dict[str, Any]

class VectorStore(Protocol):
    def add(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        contents: list[str],
        metadatas: list[dict[str, Any]]
    ) -> None:
        """Add vectors to the store."""
        ...

    def search(
        self,
        query_embedding: list[float],
        k: int = 10,
        filter: dict[str, Any] | None = None
    ) -> list[SearchResult]:
        """Search for similar vectors."""
        ...

    def delete(self, ids: list[str]) -> None:
        """Delete vectors by ID."""
        ...

    def count(self) -> int:
        """Return number of vectors stored."""
        ...

    def persist(self) -> None:
        """Persist changes to disk."""
        ...
```

### Configuration

```yaml
storage:
  backend: chromadb  # chromadb, faiss, qdrant, leann
  path: ~/.ragd/data

  chromadb:
    collection: documents
    distance_metric: cosine

  faiss:
    index_type: IVFFlat
    nlist: 100

  leann:
    model_path: ~/.ragd/leann_model
    training_epochs: 10
```

### ChromaDB Adapter

```python
class ChromaDBAdapter:
    def __init__(self, config: ChromaConfig):
        self.client = chromadb.PersistentClient(path=config.path)
        self.collection = self.client.get_or_create_collection(
            name=config.collection,
            metadata={"hnsw:space": config.distance_metric}
        )

    def add(self, ids, embeddings, contents, metadatas):
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=contents,
            metadatas=metadatas
        )

    def search(self, query_embedding, k=10, filter=None):
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=filter
        )
        return [
            SearchResult(
                id=results["ids"][0][i],
                score=results["distances"][0][i],
                content=results["documents"][0][i],
                metadata=results["metadatas"][0][i]
            )
            for i in range(len(results["ids"][0]))
        ]
```

### Migration Tool

```bash
# Migrate from ChromaDB to FAISS
ragd migrate --from chromadb --to faiss

# Export to portable format
ragd export --format vectors vectors.json

# Import to new backend
ragd import --backend faiss vectors.json
```

## Related Documentation

- [ADR-0002: ChromaDB Vector Store](../../decisions/adrs/0002-chromadb-vector-store.md) - Original decision
- [v0.6.0 Milestone](../../milestones/v0.6.0.md) - Release planning
- [Acknowledgements](../../lineage/acknowledgements.md) - LEANN citation

---
