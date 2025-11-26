# F-003: Chunking Engine

## Overview

**Use Case**: [UC-001: Index Documents](../../../use-cases/briefs/UC-001-index-documents.md)
**Milestone**: v0.1
**Priority**: P0

## Problem Statement

Extracted text must be split into chunks suitable for embedding and retrieval. Chunks should be semantically coherent, appropriately sized for the embedding model, and preserve enough context for useful retrieval.

## Design Approach

### Architecture

```
Extracted Text
    ↓
Chunking Strategy Router
    ├── Fixed Size (fallback)
    ├── Sentence-based (default)
    └── Recursive (structure-aware)
    ↓
Chunks with Metadata
```

### Strategies (v0.1)

| Strategy | Use Case | Description |
|----------|----------|-------------|
| **Fixed** | Fallback | Split by character count with overlap |
| **Sentence** | Default | Split on sentence boundaries, combine to target size |
| **Recursive** | Structured docs | Split on headers, then paragraphs, then sentences |

### Chunker Interface

```python
class Chunker(Protocol):
    def chunk(self, text: str, metadata: dict) -> list[Chunk]:
        """Split text into chunks."""
        ...

@dataclass
class Chunk:
    content: str
    index: int
    start_char: int
    end_char: int
    metadata: dict[str, Any]
```

## Implementation Tasks

- [ ] Define `Chunker` protocol and `Chunk` dataclass
- [ ] Implement `FixedChunker` with configurable size and overlap
- [ ] Implement `SentenceChunker` using sentence tokenisation
- [ ] Implement `RecursiveChunker` for structured documents
- [ ] Create `ChunkerFactory` with strategy selection
- [ ] Add token counting for embedding model compatibility
- [ ] Implement chunk overlap for context preservation
- [ ] Write unit tests for each chunking strategy
- [ ] Write integration tests for chunking pipeline

## Success Criteria

- [ ] Chunks are within embedding model token limits
- [ ] Sentence boundaries respected where possible
- [ ] Overlap provides context between chunks
- [ ] Metadata preserved and augmented (chunk index, position)
- [ ] Empty chunks filtered out
- [ ] Processing time < 100ms for typical documents

## Dependencies

- nltk or spacy (sentence tokenisation)
- tiktoken (token counting)

## Technical Notes

### Default Configuration

```yaml
chunking:
  strategy: sentence
  target_size: 512  # tokens
  max_size: 1024    # tokens
  overlap: 50       # tokens
  min_size: 50      # tokens (filter out tiny chunks)
```

### Token Counting

Use tiktoken with the embedding model's tokeniser for accurate counts:

```python
import tiktoken

def count_tokens(text: str, model: str = "cl100k_base") -> int:
    enc = tiktoken.get_encoding(model)
    return len(enc.encode(text))
```

### Sentence Tokenisation

Use NLTK's punkt tokeniser for reliable sentence splitting:

```python
import nltk
nltk.download('punkt_tab', quiet=True)
from nltk.tokenize import sent_tokenize
```

### Chunk Metadata

Each chunk carries:
- `doc_id`: Parent document identifier
- `chunk_index`: Position in document (0-indexed)
- `start_char`, `end_char`: Character offsets in original text
- `token_count`: Number of tokens in chunk

## Related Documentation

- [State-of-the-Art Chunking](../../research/state-of-the-art-chunking.md) - Research basis for design decisions
- [F-002: Text Extraction](./F-002-text-extraction.md) - Upstream provider
- [F-004: Embedding Generation](./F-004-embedding-generation.md) - Downstream consumer
- [ragged Analysis](../../lineage/ragged-analysis.md) - Chunking lessons learned

---
