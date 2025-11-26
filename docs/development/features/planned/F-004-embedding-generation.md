# F-004: Embedding Generation

## Overview

**Use Case**: [UC-001: Index Documents](../../../use-cases/briefs/UC-001-index-documents.md)
**Milestone**: v0.1
**Priority**: P0

## Problem Statement

Chunks must be converted to vector embeddings for semantic search. Embeddings must be generated locally (privacy-first) and stored efficiently for retrieval.

## Design Approach

### Architecture

```
Chunks
    ↓
Embedding Model (local)
    ├── sentence-transformers (default)
    └── Ollama embeddings (alternative)
    ↓
Vectors + Metadata
    ↓
ChromaDB Storage
```

### Technologies

- **sentence-transformers**: Primary embedding library (local, fast)
- **Ollama**: Alternative for users with Ollama installed
- **ChromaDB**: Vector storage with metadata

### Embedder Interface

```python
class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts."""
        ...

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        ...
```

## Implementation Tasks

- [ ] Define `Embedder` protocol
- [ ] Implement `SentenceTransformerEmbedder` with model selection
- [ ] Implement `OllamaEmbedder` for Ollama users
- [ ] Create `EmbedderFactory` with backend selection
- [ ] Add batch processing for efficiency
- [ ] Implement ChromaDB storage integration
- [ ] Add embedding caching to avoid re-embedding
- [ ] Write unit tests for embedders
- [ ] Write integration tests with ChromaDB

## Success Criteria

- [ ] Embeddings generated locally (no external API calls)
- [ ] Batch processing improves throughput
- [ ] ChromaDB stores embeddings with metadata
- [ ] Model can be configured via settings
- [ ] Embedding dimension matches storage expectations
- [ ] Processing time reasonable (< 100 chunks/second on CPU)

## Dependencies

- sentence-transformers
- chromadb
- torch (CPU or CUDA)

## Technical Notes

### Default Model

```yaml
embeddings:
  backend: sentence-transformers
  model: all-MiniLM-L6-v2  # Fast, 384 dimensions
  batch_size: 32
  device: auto  # cpu, cuda, mps
```

### Model Options

| Model | Dimensions | Speed | Quality |
|-------|------------|-------|---------|
| all-MiniLM-L6-v2 | 384 | Fast | Good |
| all-mpnet-base-v2 | 768 | Medium | Better |
| BAAI/bge-small-en | 384 | Fast | Good |

### ChromaDB Integration

```python
import chromadb

client = chromadb.PersistentClient(path="~/.ragd/chroma")
collection = client.get_or_create_collection(
    name="documents",
    metadata={"hnsw:space": "cosine"}
)
```

### Batch Processing

Process chunks in batches to leverage GPU parallelism:

```python
def embed_batch(chunks: list[str], batch_size: int = 32):
    embeddings = []
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        embeddings.extend(model.encode(batch))
    return embeddings
```

### Privacy

All embedding generation happens locally. No text is sent to external services.

## Related Documentation

- [State-of-the-Art Embeddings](../../research/state-of-the-art-embeddings.md) - Research basis for model selection
- [F-003: Chunking Engine](./F-003-chunking-engine.md) - Upstream provider
- [F-005: Semantic Search](./F-005-semantic-search.md) - Uses embeddings for retrieval
- [Acknowledgements](../../lineage/acknowledgements.md) - sentence-transformers citation

---
