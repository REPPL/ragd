# ADR-0018: Text Chunking Strategy

## Status

Accepted

## Context

RAG retrieval quality depends critically on how documents are chunked. Poor chunking causes:
- **Information fragmentation**: Key context split across chunks
- **Semantic dilution**: Irrelevant content mixed with relevant
- **Boundary artifacts**: Sentences cut mid-thought
- **Retrieval noise**: Wrong chunks returned for queries

Research (LlamaIndex 2023, Weaviate 2024) shows significant quality differences between chunking strategies:

| Method | NDCG@10 | Processing Time |
|--------|---------|-----------------|
| Fixed (512 tokens) | 0.42 | 1.0x |
| Sentence-based | 0.48 | 1.2x |
| Recursive | 0.51 | 1.5x |
| Semantic (LLM-assisted) | 0.56 | 8-10x |

ragd needs a chunking strategy that balances quality and performance for local-first operation.

## Decision

Use **sentence-based chunking as default** with **recursive chunking for structured documents** (Markdown, code). Target **512 tokens** with **10-20% overlap**.

### Strategy Selection

```python
def select_chunking_strategy(document: Document) -> ChunkingStrategy:
    """Select optimal chunking strategy based on document type."""

    if document.format == "markdown":
        return RecursiveChunker(separators=MARKDOWN_SEPARATORS)

    if document.format == "code":
        return RecursiveChunker(separators=CODE_SEPARATORS)

    if document.word_count < 200:
        return NoChunker()  # Keep short docs as-is

    # Default: sentence-based
    return SentenceChunker()
```

### Default Configuration

```yaml
chunking:
  # Default strategy
  strategy: sentence

  # Size parameters
  target_tokens: 512
  max_tokens: 768
  min_tokens: 50

  # Overlap
  overlap_tokens: 50
  overlap_sentences: 1  # Ensure at least 1 sentence overlap

  # Structure detection
  detect_markdown: true
  markdown_strategy: recursive
```

### Separator Hierarchy

For recursive chunking:

```python
MARKDOWN_SEPARATORS = [
    "\n## ",     # H2 headers
    "\n### ",    # H3 headers
    "\n\n",      # Paragraphs
    "\n",        # Lines
    ". ",        # Sentences
    " ",         # Words (last resort)
]

CODE_SEPARATORS = [
    "\n\nclass ",    # Class definitions
    "\ndef ",        # Function definitions
    "\n\n",          # Blank lines
    "\n",            # Lines
]
```

### Overlap Strategy

Use sentence-aware overlap:
- Include at least 1 complete sentence from previous chunk
- Target 10-20% token overlap (50-100 tokens for 512-token chunks)
- Prevents context loss at boundaries

```python
def create_overlap(prev_chunk: str, overlap_sentences: int = 1) -> str:
    """Extract overlap from previous chunk."""
    sentences = sent_tokenize(prev_chunk)
    return ' '.join(sentences[-overlap_sentences:])
```

### Chunk Metadata

Every chunk carries:

```python
@dataclass
class ChunkMetadata:
    chunk_id: str
    doc_id: str
    chunk_index: int
    start_char: int
    end_char: int
    token_count: int
    section_header: str | None
    overlap_prev: int
    overlap_next: int
```

## Consequences

### Positive

- Sentence boundaries preserved (no mid-thought cuts)
- Structure-aware for Markdown/code documents
- Consistent chunk sizes for embedding model
- Overlap prevents boundary context loss
- Efficient processing (1.2-1.5x baseline)

### Negative

- Sentence detection may fail on edge cases
- Variable chunk sizes within target range
- Recursive chunking slower for complex documents
- No semantic awareness (topic shifts not detected)

### Future Enhancement: Late Chunking

For v0.3+, consider late chunking (JinaAI approach):
- Embed full document first
- Extract chunk vectors from token ranges
- 5-10% retrieval quality improvement
- Higher memory/compute cost

## Alternatives Considered

### Fixed-Size Only

- **Pros:** Simple, fast, deterministic
- **Cons:** Ignores semantic boundaries, cuts sentences
- **Rejected:** Quality too low for RAG

### Semantic Chunking (Embedding-Based)

- **Pros:** Best quality (0.56 NDCG@10)
- **Cons:** 8-10x slower, requires embedding each sentence
- **Rejected:** Too slow for local-first operation

### Agentic Chunking (LLM-Based)

- **Pros:** Highest quality boundaries
- **Cons:** Expensive, slow (seconds per document)
- **Rejected:** Impractical for bulk ingestion

### No Overlap

- **Pros:** Simpler, less storage
- **Cons:** Context lost at boundaries
- **Rejected:** Research shows 10-15% overlap is optimal

## Related Documentation

- [State-of-the-Art Chunking](../../research/state-of-the-art-chunking.md)
- [F-003: Chunking Engine](../../features/completed/F-003-chunking-engine.md)
- [F-011: Late Chunking](../../features/planned/F-011-late-chunking.md)
- [State-of-the-Art Embeddings](../../research/state-of-the-art-embeddings.md)

