# State-of-the-Art Document Deduplication for RAG Systems

Strategies for detecting and handling duplicate documents in personal knowledge bases.

## Executive Summary

Watch folder automation introduces a critical challenge: users may save the same document multiple times, with different filenames, or save slightly modified versions. Without deduplication:

- **Storage waste**: Duplicate embeddings consume vector database space
- **Search pollution**: Same content appears multiple times in results
- **Stale content**: Old versions compete with updated versions
- **Poor UX**: Users see redundant information

This research covers multi-tier deduplication strategies, from exact hash matching to semantic similarity detection.

---

## The Deduplication Spectrum

### Types of Duplicates

| Type | Detection | Example |
|------|-----------|---------|
| **Exact** | SHA256 hash | Same file saved twice |
| **Near-duplicate** | MinHash/SimHash | Minor edits, formatting changes |
| **Semantic** | Embedding similarity | Rewritten content, translations |
| **Version** | Content + metadata | Updated versions of same document |

### Detection Accuracy vs Cost

```
                  Accuracy
                     ▲
                     │
                ●    │    ● Semantic (embeddings)
           Expensive │
                     │       ● MinHash + LSH
                     │
                     │          ● SimHash
                     │
             Cheap   │             ● SHA256
                     └──────────────────────────► Cost
```

---

## Tier 1: Exact Duplicate Detection (SHA256)

### Strategy

Hash the document content and detect identical files instantly.

```python
import hashlib
from pathlib import Path

def content_hash(file_path: Path) -> str:
    """Generate SHA256 hash of file content."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def is_exact_duplicate(file_path: Path, hash_index: dict[str, str]) -> str | None:
    """Check if file is exact duplicate. Returns original path if duplicate."""
    file_hash = content_hash(file_path)
    if file_hash in hash_index:
        return hash_index[file_hash]
    hash_index[file_hash] = str(file_path)
    return None
```

### Characteristics

| Aspect | Value |
|--------|-------|
| Speed | O(n) file read, O(1) lookup |
| Storage | 64 bytes per document |
| False positives | Zero (cryptographic hash) |
| False negatives | High (any change = different hash) |

### When to Use

- **First-pass filter**: Catch obvious duplicates before expensive processing
- **Content-addressed storage**: Like Git, use hash as document ID
- **Import deduplication**: Prevent re-indexing identical files

---

## Tier 2: Near-Duplicate Detection (MinHash + LSH)

### The Problem

Users save documents with minor changes:
- Different whitespace or formatting
- Added/removed headers/footers
- Typo corrections
- Extracted sections

SHA256 fails completely here—a single character change produces entirely different hash.

### MinHash Algorithm

MinHash estimates Jaccard similarity between documents by comparing signature sketches.

```python
from datasketch import MinHash, MinHashLSH

def document_minhash(text: str, num_perm: int = 128) -> MinHash:
    """Create MinHash signature for document."""
    minhash = MinHash(num_perm=num_perm)
    # Shingle the document (n-grams of words)
    words = text.lower().split()
    for i in range(len(words) - 2):
        shingle = " ".join(words[i:i+3])
        minhash.update(shingle.encode("utf-8"))
    return minhash

def create_lsh_index(threshold: float = 0.5) -> MinHashLSH:
    """Create LSH index for fast similarity search."""
    return MinHashLSH(threshold=threshold, num_perm=128)

def find_near_duplicates(
    doc_id: str,
    minhash: MinHash,
    lsh: MinHashLSH
) -> list[str]:
    """Find documents similar to this one."""
    # Query returns candidate duplicates
    candidates = lsh.query(minhash)
    return [c for c in candidates if c != doc_id]
```

### Jaccard Similarity Thresholds

| Threshold | Meaning | Use Case |
|-----------|---------|----------|
| 0.95+ | Near-identical | Typo fixes, whitespace changes |
| 0.80-0.95 | Very similar | Minor edits, formatting |
| 0.50-0.80 | Related | Shared sections, derivatives |
| <0.50 | Different | Unrelated documents |

### LSH (Locality-Sensitive Hashing)

LSH enables sub-linear lookup by hashing similar items to same buckets:

```python
# Without LSH: O(n) comparisons
for doc in all_documents:
    if minhash.jaccard(doc.minhash) > 0.85:
        # Near-duplicate found

# With LSH: O(1) average case
candidates = lsh.query(minhash)  # Returns ~10-100 candidates
for candidate in candidates:
    if minhash.jaccard(candidate.minhash) > 0.85:
        # Verified near-duplicate
```

### Characteristics

| Aspect | Value |
|--------|-------|
| Speed | O(1) query with LSH, O(k) verification |
| Storage | ~1KB per document (128 permutations × 8 bytes) |
| False positives | Configurable via threshold |
| False negatives | Low for near-duplicates |

---

## Tier 3: Semantic Deduplication (Embeddings)

### The Problem

Documents may express the same information differently:
- Rewritten articles
- Translations
- Summaries vs full documents
- Different sources covering same topic

### Embedding Similarity

```python
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("nomic-ai/nomic-embed-text-v1.5")

def semantic_similarity(doc1: str, doc2: str) -> float:
    """Compute semantic similarity between documents."""
    embeddings = model.encode([doc1, doc2])
    # Cosine similarity
    similarity = np.dot(embeddings[0], embeddings[1]) / (
        np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
    )
    return float(similarity)

def find_semantic_duplicates(
    doc_embedding: np.ndarray,
    collection,  # ChromaDB collection
    threshold: float = 0.92
) -> list[dict]:
    """Find semantically similar documents."""
    results = collection.query(
        query_embeddings=[doc_embedding.tolist()],
        n_results=10,
    )

    duplicates = []
    for i, distance in enumerate(results["distances"][0]):
        similarity = 1 - distance  # Convert distance to similarity
        if similarity > threshold:
            duplicates.append({
                "id": results["ids"][0][i],
                "similarity": similarity,
            })
    return duplicates
```

### Similarity Thresholds

| Threshold | Meaning | Action |
|-----------|---------|--------|
| 0.98+ | Semantic duplicate | Block or replace |
| 0.92-0.98 | Very similar | Flag for review |
| 0.85-0.92 | Related | Show as related documents |
| <0.85 | Different | Index normally |

### Cross-Chunk Deduplication

For chunked documents, compare at multiple levels:

```python
def document_level_similarity(chunks1: list[str], chunks2: list[str]) -> float:
    """Compare documents via their chunks."""
    # Average embedding of all chunks
    avg1 = np.mean([model.encode(c) for c in chunks1], axis=0)
    avg2 = np.mean([model.encode(c) for c in chunks2], axis=0)

    return float(np.dot(avg1, avg2) / (
        np.linalg.norm(avg1) * np.linalg.norm(avg2)
    ))
```

### Characteristics

| Aspect | Value |
|--------|-------|
| Speed | O(log n) with vector index (HNSW) |
| Storage | 768-1536 bytes per document (embedding dimension) |
| False positives | Higher (semantic overlap ≠ duplicate) |
| False negatives | Low for true semantic duplicates |

---

## Multi-Tier Pipeline

### Recommended Architecture

```
                     New Document
                          │
                          ▼
                ┌─────────────────┐
                │   SHA256 Hash   │◄── O(n) read, O(1) lookup
                └────────┬────────┘
                         │
              exact match? ──yes──► Skip indexing
                         │
                         no
                         ▼
                ┌─────────────────┐
                │  MinHash + LSH  │◄── O(1) query, O(k) verify
                └────────┬────────┘
                         │
        Jaccard > 0.85? ──yes──► Mark as version
                         │
                         no
                         ▼
                ┌─────────────────┐
                │    Embedding    │◄── Computed anyway for indexing
                │   Similarity    │
                └────────┬────────┘
                         │
         Cosine > 0.92? ──yes──► Flag for review
                         │
                         no
                         ▼
                   Index normally
```

### Implementation Strategy

```python
from dataclasses import dataclass
from enum import Enum

class DuplicateType(Enum):
    EXACT = "exact"           # SHA256 match
    NEAR = "near"             # MinHash Jaccard > 0.85
    SEMANTIC = "semantic"     # Embedding cosine > 0.92
    UNIQUE = "unique"         # No duplicate detected

@dataclass
class DuplicateResult:
    type: DuplicateType
    original_id: str | None = None
    similarity: float | None = None

def check_duplicate(
    content: str,
    content_hash: str,
    embedding: np.ndarray,
    hash_index: dict,
    lsh_index: MinHashLSH,
    vector_store,
) -> DuplicateResult:
    """Multi-tier duplicate detection."""

    # Tier 1: Exact hash
    if content_hash in hash_index:
        return DuplicateResult(
            type=DuplicateType.EXACT,
            original_id=hash_index[content_hash],
            similarity=1.0,
        )

    # Tier 2: Near-duplicate (MinHash)
    minhash = document_minhash(content)
    candidates = lsh_index.query(minhash)
    for candidate_id in candidates:
        candidate_minhash = get_minhash(candidate_id)
        jaccard = minhash.jaccard(candidate_minhash)
        if jaccard > 0.85:
            return DuplicateResult(
                type=DuplicateType.NEAR,
                original_id=candidate_id,
                similarity=jaccard,
            )

    # Tier 3: Semantic duplicate
    similar = vector_store.query(embedding, n_results=5)
    for doc_id, distance in similar:
        similarity = 1 - distance
        if similarity > 0.92:
            return DuplicateResult(
                type=DuplicateType.SEMANTIC,
                original_id=doc_id,
                similarity=similarity,
            )

    return DuplicateResult(type=DuplicateType.UNIQUE)
```

---

## Version Detection and Management

### The Versioning Problem

Documents evolve:
- Draft → Final
- v1.0 → v1.1 → v2.0
- Notes → Report → Publication

Users want to search the latest version, but may want to access history.

### Version Chain Detection

```python
from datetime import datetime

@dataclass
class DocumentVersion:
    id: str
    path: str
    content_hash: str
    indexed_at: datetime
    version_chain_id: str | None = None
    is_latest: bool = True

def detect_version_chain(
    new_doc: DocumentVersion,
    existing_docs: list[DocumentVersion],
    similarity_threshold: float = 0.75,
) -> str | None:
    """Detect if new document is version of existing one."""
    for existing in existing_docs:
        # Use MinHash for version detection (more lenient threshold)
        jaccard = compute_jaccard(new_doc.content, existing.content)
        if jaccard > similarity_threshold:
            # Same version chain - mark existing as not latest
            existing.is_latest = False
            new_doc.version_chain_id = existing.version_chain_id or existing.id
            return existing.id
    return None
```

### Search Behaviour for Versions

```python
def search_with_versions(query: str, include_history: bool = False):
    """Search respecting version chains."""
    if include_history:
        # Return all versions
        return vector_store.search(query)
    else:
        # Only return latest versions
        return vector_store.search(
            query,
            where={"is_latest": True}
        )
```

---

## Library Comparison

### Python Libraries

| Library | Algorithm | Speed | Memory | Notes |
|---------|-----------|-------|--------|-------|
| **datasketch** | MinHash, LSH | Fast | Low | Production-ready, well-maintained |
| **text-dedup** | Multiple | Fast | Low | NLP-focused, good defaults |
| **semhash** | Semantic hashing | Medium | Medium | Embedding-based |
| **simhash-py** | SimHash | Very fast | Very low | Best for short texts |

### Recommended Stack for ragd

| Tier | Library | Rationale |
|------|---------|-----------|
| Exact | `hashlib` (stdlib) | No dependencies, fast |
| Near | `datasketch` | Mature, configurable |
| Semantic | `chromadb` (existing) | Already computing embeddings |

### Installation

```bash
pip install datasketch  # ~50KB, pure Python
```

---

## Performance Considerations

### Indexing Cost

| Operation | Time per Document | Memory |
|-----------|-------------------|--------|
| SHA256 hash | ~1ms | 64 bytes |
| MinHash (128 perm) | ~10ms | 1KB |
| Embedding | ~50-100ms | 768-1536 bytes |
| LSH query | ~0.1ms | - |
| Vector query | ~1-5ms | - |

### Scaling

| Documents | Hash Index | MinHash LSH | Vector Index |
|-----------|------------|-------------|--------------|
| 10K | 0.6MB | 10MB | 15MB |
| 100K | 6MB | 100MB | 150MB |
| 1M | 60MB | 1GB | 1.5GB |

---

## Edge Cases

### Same Content, Different Formats

```
Document A: report.pdf (PDF)
Document B: report.docx (Word)
Document C: report.md (Markdown)
```

**Solution**: Hash extracted text, not raw file.

### Partial Duplicates

```
Document A: Full research paper
Document B: Executive summary (extracted)
```

**Solution**: Chunk-level deduplication with parent tracking.

### Multi-Language Duplicates

```
Document A: English version
Document B: French translation
```

**Solution**: Language-agnostic embeddings (e.g., multilingual models) or explicit translation detection.

---

## Recommendations for ragd

### v0.2 Implementation

1. **Tier 1 only**: SHA256 hash index
   - Block exact duplicates at import
   - Store hash in document metadata
   - O(1) lookup, zero false positives

### v0.3+ Enhancement

2. **Add Tier 2**: MinHash + LSH
   - Detect near-duplicates
   - Version chain management
   - datasketch library

3. **Add Tier 3**: Semantic deduplication
   - Already have embeddings
   - Query vector store before indexing
   - Configurable threshold

### Configuration

```yaml
deduplication:
  exact:
    enabled: true                  # SHA256 hash
  near:
    enabled: true                  # MinHash + LSH
    threshold: 0.85                # Jaccard threshold
    num_permutations: 128
  semantic:
    enabled: true                  # Embedding similarity
    threshold: 0.92                # Cosine threshold
  on_duplicate:
    exact: skip                    # skip | warn | replace
    near: version                  # version | warn | skip
    semantic: flag                 # flag | skip | version
```

---

## Related Documentation

- [ADR-0016: Document Deduplication Strategy](../decisions/adrs/0016-document-deduplication.md)
- [F-037: Watch Folder](../features/completed/F-037-watch-folder.md)
- [ADR-0015: Web Archive Processing](../decisions/adrs/0015-web-archive-processing.md)
- [State-of-the-Art Embeddings](./state-of-the-art-embeddings.md)

