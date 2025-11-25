# ADR-0002: Use ChromaDB as Default Vector Store

## Status

Accepted

## Context

ragd needs a vector database to store embeddings for semantic search. Requirements:
- **Local-first:** No cloud dependencies
- **Embedded:** Run within the application
- **Simple:** Minimal configuration
- **Performant:** Fast for personal-scale data (thousands of documents)
- **Reliable:** Mature and maintained

Several vector databases exist with different trade-offs between performance, complexity, and hosting requirements.

## Decision

Use **ChromaDB** as the default vector store for ragd.

ChromaDB provides:
- Embedded mode (runs in-process)
- Persistent storage to disk
- Simple Python API
- Metadata filtering
- No external services required

### Example Usage

```python
import chromadb

client = chromadb.PersistentClient(path="~/.ragd/chroma")
collection = client.get_or_create_collection(
    name="documents",
    metadata={"hnsw:space": "cosine"}
)

# Add embeddings
collection.add(
    ids=["doc1_chunk1"],
    embeddings=[[0.1, 0.2, ...]],
    documents=["chunk text"],
    metadatas=[{"source": "document.pdf", "chunk": 0}]
)

# Query
results = collection.query(
    query_embeddings=[[0.1, 0.2, ...]],
    n_results=10
)
```

## Consequences

### Positive

- Zero configuration for users
- All data stays local
- Simple API reduces implementation complexity
- Good performance for personal-scale use
- Active development and community
- MIT licence

### Negative

- Not suitable for very large datasets (millions of documents)
- Limited query language compared to dedicated databases
- Single-node only (no distributed deployment)

### Future Path

In v0.6, we plan to add a `VectorStore` abstraction allowing:
- LEANN integration for 97% storage savings
- Alternative backends for power users
- Easy testing with mock stores

ChromaDB remains the default for simplicity.

## Alternatives Considered

### Pinecone

- **Pros:** Highly scalable, managed service
- **Cons:** Cloud-only, costs money, privacy concerns
- **Rejected:** Violates privacy-first principle

### Weaviate

- **Pros:** Feature-rich, GraphQL API
- **Cons:** Heavy (Go-based), complex setup, overkill for personal use
- **Rejected:** Too complex for embedded use

### Qdrant

- **Pros:** Fast, Rust-based, embedded mode
- **Cons:** Less mature Python ecosystem, more complex API
- **Considered for future:** Potential alternative backend in v0.6

### FAISS

- **Pros:** Very fast, Facebook-backed
- **Cons:** Low-level, no persistence, requires wrapper
- **Rejected:** Too low-level, would need significant wrapper code

### LanceDB

- **Pros:** DuckDB-based, good for tabular + vector
- **Cons:** Newer, less mature
- **Considered for future:** Interesting option for v0.6

## Related Documentation

- [F-004: Embedding Generation](../../features/planned/F-004-embedding-generation.md)
- [F-005: Semantic Search](../../features/planned/F-005-semantic-search.md)
- [Acknowledgements](../../lineage/acknowledgements.md) - ChromaDB citation

