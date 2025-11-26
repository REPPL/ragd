# ADR-0016: Document Deduplication Strategy

## Status

Accepted

## Context

The watch folder feature (F-037) automatically indexes documents as they're added to monitored directories. Users frequently:
- Save the same document multiple times with different filenames
- Download the same web page to multiple folders
- Create slightly modified versions of documents
- Archive content that already exists in the knowledge base

Without deduplication:
- Storage waste from duplicate embeddings
- Search results polluted with redundant content
- Stale versions compete with updated versions
- Poor user experience

ragd needs a strategy to detect duplicates at multiple levels:
1. **Exact duplicates**: Identical content with different filenames
2. **Near-duplicates**: Minor edits, formatting changes
3. **Semantic duplicates**: Same information, different wording

## Decision

Implement a **multi-tier deduplication pipeline** with **SHA256 hash** for exact matches, **MinHash + LSH** for near-duplicates, and **embedding similarity** for semantic duplicates.

### Architecture

```
                     New Document
                          │
                          ▼
                ┌─────────────────┐
                │   SHA256 Hash   │◄── Tier 1: O(1) lookup
                └────────┬────────┘
                         │
              exact match? ──yes──► Skip indexing
                         │
                         no
                         ▼
                ┌─────────────────┐
                │  MinHash + LSH  │◄── Tier 2: O(1) query
                └────────┬────────┘
                         │
        Jaccard > 0.85? ──yes──► Version chain
                         │
                         no
                         ▼
                ┌─────────────────┐
                │    Embedding    │◄── Tier 3: Already computed
                │   Similarity    │
                └────────┬────────┘
                         │
         Cosine > 0.92? ──yes──► Flag for review
                         │
                         no
                         ▼
                   Index normally
```

### Tier 1: Exact Duplicate (SHA256)

```python
import hashlib
from pathlib import Path

def content_hash(content: str) -> str:
    """SHA256 hash of extracted text content."""
    return hashlib.sha256(content.encode()).hexdigest()

# Storage: document metadata
{
    "id": "doc_abc123",
    "path": "/path/to/document.pdf",
    "content_hash": "e3b0c44298fc...",  # SHA256
    "indexed_at": "2025-01-15T10:30:00Z",
}
```

**Key insight**: Hash extracted text, not raw file bytes. This catches duplicates across formats (PDF, DOCX, HTML all extracted to same text).

### Tier 2: Near-Duplicate (MinHash + LSH)

Using `datasketch` library:

```python
from datasketch import MinHash, MinHashLSH

# Configuration
NUM_PERMUTATIONS = 128
JACCARD_THRESHOLD = 0.85

def document_minhash(text: str) -> MinHash:
    """Create MinHash signature using word trigrams."""
    minhash = MinHash(num_perm=NUM_PERMUTATIONS)
    words = text.lower().split()
    for i in range(len(words) - 2):
        shingle = " ".join(words[i:i+3])
        minhash.update(shingle.encode("utf-8"))
    return minhash

# LSH index for fast lookup
lsh = MinHashLSH(threshold=JACCARD_THRESHOLD, num_perm=NUM_PERMUTATIONS)

def check_near_duplicate(doc_id: str, minhash: MinHash) -> list[str]:
    """Find near-duplicates in O(1) average time."""
    candidates = lsh.query(minhash)
    return [c for c in candidates if c != doc_id]
```

### Tier 3: Semantic Duplicate (Embeddings)

Leverages embeddings already computed for indexing:

```python
def check_semantic_duplicate(
    embedding: list[float],
    collection,  # ChromaDB collection
    threshold: float = 0.92,
) -> list[dict]:
    """Find semantically similar documents."""
    results = collection.query(
        query_embeddings=[embedding],
        n_results=5,
        include=["distances", "metadatas"],
    )

    duplicates = []
    for i, distance in enumerate(results["distances"][0]):
        similarity = 1 - distance
        if similarity > threshold:
            duplicates.append({
                "id": results["ids"][0][i],
                "similarity": similarity,
            })
    return duplicates
```

### Duplicate Actions

| Duplicate Type | Default Action | Options |
|---------------|----------------|---------|
| Exact | Skip | skip, warn, replace |
| Near | Version chain | version, warn, skip |
| Semantic | Flag for review | flag, skip, version |

### Version Chain Management

Near-duplicates become version chains:

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class DocumentVersion:
    id: str
    path: str
    content_hash: str
    indexed_at: datetime
    version_chain_id: str | None = None
    is_latest: bool = True
    previous_version: str | None = None

def create_version_chain(
    new_doc: DocumentVersion,
    existing_doc: DocumentVersion,
) -> None:
    """Link new document as newer version."""
    chain_id = existing_doc.version_chain_id or existing_doc.id

    new_doc.version_chain_id = chain_id
    new_doc.previous_version = existing_doc.id
    new_doc.is_latest = True

    existing_doc.is_latest = False
```

Search respects version chains:

```python
def search(query: str, include_history: bool = False):
    """Search with version awareness."""
    where_filter = None if include_history else {"is_latest": True}
    return collection.query(query, where=where_filter)
```

### Storage Schema

```python
# Document metadata stored in ChromaDB
{
    "id": "doc_abc123",
    "path": "/path/to/document.pdf",
    "content_hash": "e3b0c44298fc...",
    "indexed_at": "2025-01-15T10:30:00Z",

    # Version chain
    "version_chain_id": "doc_xyz789",  # First doc in chain
    "is_latest": True,
    "previous_version": "doc_def456",

    # Deduplication metadata
    "duplicate_type": None,            # null, "exact", "near", "semantic"
    "duplicate_of": None,              # Original document ID if duplicate
}

# Separate MinHash index stored in ~/.ragd/minhash.db (SQLite)
CREATE TABLE minhash_index (
    doc_id TEXT PRIMARY KEY,
    signature BLOB,  -- Pickled MinHash object
    indexed_at TEXT
);
```

### Configuration

```yaml
# ~/.ragd/config.yaml
deduplication:
  enabled: true

  exact:
    enabled: true
    action: skip          # skip | warn | replace

  near:
    enabled: true
    threshold: 0.85       # Jaccard similarity
    action: version       # version | warn | skip

  semantic:
    enabled: true
    threshold: 0.92       # Cosine similarity
    action: flag          # flag | skip | version
```

### CLI Interface

```bash
# Check for duplicates before indexing
ragd add ~/Downloads/report.pdf --check-duplicates

# Show duplicate information
ragd info ~/Documents/report.pdf
# Output:
# Duplicate Status: Near-duplicate
# Similar to: ~/Archives/old-report.pdf (87% similar)
# Version chain: 3 versions

# List all duplicates in index
ragd duplicates list

# Merge version chains
ragd duplicates merge doc_abc123 doc_def456

# Search including old versions
ragd search "machine learning" --include-history
```

## Consequences

### Positive

- Prevents storage waste from duplicate embeddings
- Clean search results without redundant content
- Version history preserved for document evolution
- Catches duplicates across file formats
- Minimal overhead (hashing is fast, embeddings already computed)

### Negative

- Additional complexity in indexing pipeline
- MinHash index adds ~1KB per document
- Near-duplicate threshold may need tuning per use case
- Version chains add metadata overhead
- datasketch dependency (~50KB)

### Phased Implementation

| Version | Features |
|---------|----------|
| v0.2 | SHA256 exact duplicate detection only |
| v0.3 | Add MinHash + LSH for near-duplicates |
| v0.4 | Add semantic deduplication + version chains |

## Alternatives Considered

### SimHash Only

- **Pros:** Single algorithm, very fast
- **Cons:** Less accurate for longer documents, no semantic detection
- **Rejected:** MinHash better for document-length content

### Embedding Similarity Only

- **Pros:** Catches semantic duplicates, no additional libraries
- **Cons:** Expensive (requires embedding), no exact match guarantee
- **Rejected:** Hash-based tiers are faster for obvious duplicates

### Content-Addressed Storage (Like Git)

- **Pros:** Automatic deduplication, immutable history
- **Cons:** Complex implementation, doesn't help search
- **Rejected:** Overkill for personal knowledge base

### No Deduplication

- **Pros:** Simpler implementation
- **Cons:** Watch folder would rapidly fill with duplicates
- **Rejected:** Essential for good UX with automated indexing

## Related Documentation

- [State-of-the-Art Deduplication](../../research/state-of-the-art-deduplication.md)
- [F-037: Watch Folder](../../features/planned/F-037-watch-folder.md)
- [ADR-0014: Daemon Process Management](./0014-daemon-management.md)
- [ADR-0015: Web Archive Processing](./0015-web-archive-processing.md)

