# Data Schema Reference

Complete specification of ragd's data models, ChromaDB collection structure, and citation metadata.

## Overview

ragd uses a **dual-database architecture**:

| Database | Purpose | Contents |
|----------|---------|----------|
| **SQLite** | Metadata + full-text search | Documents, chunks, FTS5 index |
| **ChromaDB** | Embeddings + vector search | Chunk embeddings + flat metadata |

This separation optimises for both structured queries (SQLite) and semantic search (ChromaDB).

---

## Document Model

Documents represent source files indexed by ragd.

### DocumentMetadata

```python
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from enum import Enum
import hashlib

class DocumentType(str, Enum):
    """Supported document formats."""
    PDF = "pdf"
    TEXT = "txt"
    MARKDOWN = "md"

class DocumentMetadata(BaseModel):
    """Parent document metadata stored in SQLite."""

    # Identifiers
    doc_id: str = Field(..., description="UUID v4 document identifier")
    source_path: str = Field(..., description="Original file path")
    source_hash: str = Field(..., description="SHA-256 hash of file contents")

    # Basic metadata
    filename: str = Field(..., description="Base filename without path")
    format: DocumentType = Field(..., description="Document format type")
    title: Optional[str] = Field(None, description="Document title if detected")

    # Content statistics
    total_chars: int = Field(..., ge=0, description="Total character count")
    word_count: int = Field(..., ge=0, description="Approximate word count")
    chunk_count: int = Field(..., ge=0, description="Number of chunks generated")

    # Processing metadata
    indexed_at: datetime = Field(default_factory=datetime.utcnow)
    embedding_model: str = Field(..., description="Model used for embeddings")

    # User metadata
    tags: list[str] = Field(default_factory=list, description="User-defined tags")

    @field_validator("source_hash")
    @classmethod
    def validate_hash(cls, v: str) -> str:
        """Ensure hash is valid SHA-256 (64 hex characters)."""
        if len(v) != 64 or not all(c in "0123456789abcdef" for c in v.lower()):
            raise ValueError("source_hash must be 64-character hex SHA-256")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "doc_id": "doc_123e4567-e89b-12d3-a456-426614174000",
                "source_path": "~/Documents/report.pdf",
                "source_hash": "a3c5f9e2b1d4c6a8e0f2b4d6c8a0e2f4a6b8c0d2e4f6a8b0c2d4e6f8a0b2c4d6",
                "filename": "report.pdf",
                "format": "pdf",
                "title": "Q3 2024 Financial Report",
                "total_chars": 15000,
                "word_count": 2500,
                "chunk_count": 12,
                "embedding_model": "BAAI/bge-base-en-v1.5",
                "tags": ["finance", "2024"]
            }
        }
```

### SQLite Schema

```sql
CREATE TABLE documents (
    doc_id TEXT PRIMARY KEY,
    source_path TEXT NOT NULL UNIQUE,
    source_hash TEXT NOT NULL UNIQUE,
    filename TEXT NOT NULL,
    format TEXT NOT NULL CHECK (format IN ('pdf', 'txt', 'md')),
    title TEXT,
    total_chars INTEGER NOT NULL CHECK (total_chars >= 0),
    word_count INTEGER NOT NULL CHECK (word_count >= 0),
    chunk_count INTEGER NOT NULL CHECK (chunk_count >= 0),
    indexed_at TEXT NOT NULL,
    embedding_model TEXT NOT NULL,
    tags TEXT,  -- JSON array: ["tag1", "tag2"]

    -- Indexes
    UNIQUE (source_hash)
);

CREATE INDEX idx_documents_path ON documents(source_path);
CREATE INDEX idx_documents_format ON documents(format);
CREATE INDEX idx_documents_indexed ON documents(indexed_at);
```

---

## Chunk Model

Chunks are searchable segments of documents with position tracking for citations.

### ChunkMetadata

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime

class ChunkMetadata(BaseModel):
    """Individual chunk metadata stored in SQLite."""

    # Identifiers
    chunk_id: str = Field(..., description="UUID v4 chunk identifier")
    doc_id: str = Field(..., description="Parent document ID (foreign key)")

    # Position in document
    chunk_index: int = Field(..., ge=0, description="Position in document (0-indexed)")
    char_start: int = Field(..., ge=0, description="Character offset start")
    char_end: int = Field(..., gt=0, description="Character offset end")

    # Content
    content: str = Field(..., min_length=1, description="Chunk text content")
    content_hash: str = Field(..., description="SHA-256 hash for deduplication")
    token_count: int = Field(..., ge=0, description="Token count for embedding model")

    # Citation metadata
    page_numbers: list[int] = Field(default_factory=list, description="Pages this chunk spans")
    section_header: Optional[str] = Field(None, description="Section heading if detected")

    # Overlap tracking
    overlap_prev_chars: int = Field(default=0, ge=0, description="Overlap with previous chunk")
    overlap_next_chars: int = Field(default=0, ge=0, description="Overlap with next chunk")

    # Navigation
    prev_chunk_id: Optional[str] = Field(None, description="Previous chunk ID")
    next_chunk_id: Optional[str] = Field(None, description="Next chunk ID")

    # Embedding metadata
    embedding_model: str = Field(..., description="Model used for this chunk")
    embedded_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("char_end")
    @classmethod
    def validate_char_range(cls, v: int, info) -> int:
        """Ensure char_end > char_start."""
        if "char_start" in info.data and v <= info.data["char_start"]:
            raise ValueError("char_end must be greater than char_start")
        return v

    @model_validator(mode="after")
    def validate_content_length(self) -> "ChunkMetadata":
        """Ensure content length matches character range."""
        expected = self.char_end - self.char_start
        actual = len(self.content)
        # Allow tolerance for whitespace normalisation
        if abs(expected - actual) > 10:
            raise ValueError(
                f"Content length ({actual}) doesn't match "
                f"char range ({expected})"
            )
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": "chunk_987fcdeb-51a2-43d7-8c9d-1234567890ab",
                "doc_id": "doc_123e4567-e89b-12d3-a456-426614174000",
                "chunk_index": 5,
                "char_start": 2450,
                "char_end": 2890,
                "content": "The quarterly revenue increased by 15%...",
                "content_hash": "b7f3a9e2c1d4...",
                "token_count": 112,
                "page_numbers": [5, 6],
                "section_header": "Revenue Analysis",
                "overlap_prev_chars": 50,
                "overlap_next_chars": 50,
                "embedding_model": "BAAI/bge-base-en-v1.5"
            }
        }
```

### SQLite Schema

```sql
CREATE TABLE chunks (
    chunk_id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    char_start INTEGER NOT NULL CHECK (char_start >= 0),
    char_end INTEGER NOT NULL CHECK (char_end > char_start),
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    token_count INTEGER NOT NULL CHECK (token_count >= 0),
    page_numbers TEXT,  -- JSON array: [5, 6]
    section_header TEXT,
    overlap_prev_chars INTEGER DEFAULT 0 CHECK (overlap_prev_chars >= 0),
    overlap_next_chars INTEGER DEFAULT 0 CHECK (overlap_next_chars >= 0),
    prev_chunk_id TEXT,
    next_chunk_id TEXT,
    embedding_model TEXT NOT NULL,
    embedded_at TEXT NOT NULL,

    FOREIGN KEY (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE,
    FOREIGN KEY (prev_chunk_id) REFERENCES chunks(chunk_id),
    FOREIGN KEY (next_chunk_id) REFERENCES chunks(chunk_id),

    UNIQUE (doc_id, chunk_index)
);

CREATE INDEX idx_chunks_doc ON chunks(doc_id);
CREATE INDEX idx_chunks_sequence ON chunks(doc_id, chunk_index);
CREATE INDEX idx_chunks_hash ON chunks(content_hash);

-- Full-text search index for hybrid retrieval
CREATE VIRTUAL TABLE chunks_fts USING fts5(
    chunk_id UNINDEXED,
    content,
    section_header
);
```

---

## ChromaDB Collection

ChromaDB stores embeddings with flat metadata for vector search.

### Collection Configuration

```python
import chromadb
from chromadb.config import Settings

# Persistent client with cosine distance
client = chromadb.PersistentClient(
    path="~/.local/share/ragd/chroma_db",
    settings=Settings(anonymized_telemetry=False)
)

# Create collection with cosine similarity
collection = client.get_or_create_collection(
    name="ragd_chunks",
    metadata={
        "hnsw:space": "cosine",  # Required for sentence-transformers
        "hnsw:construction_ef": 128,
        "hnsw:search_ef": 64,
    }
)
```

### ChromaDB Metadata Schema

ChromaDB metadata must be **flat** (no nested objects):

```python
from pydantic import BaseModel
from typing import Optional

class ChromaDBMetadata(BaseModel):
    """Flattened metadata for ChromaDB storage."""

    # Identifiers (required)
    doc_id: str
    chunk_id: str

    # Position (for citations)
    chunk_index: int
    page: Optional[int] = None  # First page if multi-page
    pages: Optional[str] = None  # Comma-separated: "5,6"
    section: Optional[str] = None

    # Character positions
    char_start: int
    char_end: int

    # Document metadata (denormalised for filtering)
    source: str  # Filename for filtering
    title: Optional[str] = None
    format: str  # pdf, txt, md

    # User metadata
    tags: Optional[str] = None  # Comma-separated: "finance,2024"

    # Timestamp
    indexed_at: str  # ISO8601 format

    def to_dict(self) -> dict:
        """Convert to ChromaDB-compatible dict (exclude None values)."""
        return {k: v for k, v in self.model_dump().items() if v is not None}
```

### Adding Chunks to ChromaDB

```python
def add_chunk_to_chromadb(
    collection: chromadb.Collection,
    chunk: ChunkMetadata,
    document: DocumentMetadata,
    embedding: list[float]
) -> None:
    """Add a chunk with its embedding to ChromaDB."""

    metadata = ChromaDBMetadata(
        doc_id=chunk.doc_id,
        chunk_id=chunk.chunk_id,
        chunk_index=chunk.chunk_index,
        page=chunk.page_numbers[0] if chunk.page_numbers else None,
        pages=",".join(map(str, chunk.page_numbers)) if chunk.page_numbers else None,
        section=chunk.section_header,
        char_start=chunk.char_start,
        char_end=chunk.char_end,
        source=document.filename,
        title=document.title,
        format=document.format.value,
        tags=",".join(document.tags) if document.tags else None,
        indexed_at=chunk.embedded_at.isoformat(),
    )

    collection.add(
        ids=[chunk.chunk_id],
        documents=[chunk.content],
        embeddings=[embedding],
        metadatas=[metadata.to_dict()]
    )
```

---

## Citation Schema

Citations provide source attribution for search results.

### CitationMetadata

```python
from pydantic import BaseModel, Field
from typing import Optional

class CitationMetadata(BaseModel):
    """Complete metadata for accurate source attribution."""

    # Document identification
    doc_id: str
    source_path: str
    filename: str
    title: Optional[str] = None

    # Location within document
    page_numbers: list[int] = Field(default_factory=list)
    section_header: Optional[str] = None
    char_start: int
    char_end: int

    # Retrieval metadata
    chunk_id: str
    retrieval_score: float = Field(..., ge=0.0, le=1.0)

    # Content excerpt
    excerpt: str

    def format_citation(self) -> str:
        """Format as human-readable citation."""
        location = []
        if self.title:
            location.append(f'"{self.title}"')
        else:
            location.append(self.filename)

        if self.page_numbers:
            pages = self.page_numbers
            if len(pages) == 1:
                location.append(f"p. {pages[0]}")
            else:
                location.append(f"pp. {pages[0]}-{pages[-1]}")

        if self.section_header:
            location.append(f'section "{self.section_header}"')

        return ", ".join(location)

    class Config:
        json_schema_extra = {
            "example": {
                "doc_id": "doc_123e4567",
                "source_path": "~/Documents/report.pdf",
                "filename": "report.pdf",
                "title": "Q3 2024 Financial Report",
                "page_numbers": [5, 6],
                "section_header": "Revenue Analysis",
                "char_start": 2450,
                "char_end": 2890,
                "chunk_id": "chunk_987fcdeb",
                "retrieval_score": 0.89,
                "excerpt": "The quarterly revenue increased by 15%..."
            }
        }
```

### Citation Output Format

```python
class SearchResult(BaseModel):
    """Search result with citation."""

    query: str
    results: list[CitationMetadata]
    total_found: int

    def format_results(self) -> str:
        """Format results with citations."""
        lines = [f"Found {self.total_found} results for: {self.query}\n"]

        for i, result in enumerate(self.results, 1):
            lines.append(f"[{i}] {result.format_citation()}")
            lines.append(f"    Score: {result.retrieval_score:.2%}")
            lines.append(f"    {result.excerpt[:100]}...")
            lines.append("")

        return "\n".join(lines)
```

---

## Embedding Configuration

### Default Model

| Setting | Value | Rationale |
|---------|-------|-----------|
| **Model** | `BAAI/bge-base-en-v1.5` | Best accuracy/speed balance |
| **Dimensions** | 768 | Model output dimensions |
| **Distance** | Cosine | Optimised for sentence-transformers |
| **Query Prefix** | `"Represent this sentence for searching relevant passages: "` | Required for BGE models |

### EmbeddingConfig

```python
from pydantic import BaseModel, Field

class EmbeddingConfig(BaseModel):
    """Embedding model configuration."""

    model: str = "BAAI/bge-base-en-v1.5"
    dimensions: int = 768
    device: str = "auto"  # auto | cpu | cuda | mps
    normalize: bool = True
    batch_size: int = 32
    query_prefix: str = "Represent this sentence for searching relevant passages: "

    @property
    def is_bge_model(self) -> bool:
        """Check if model requires query prefix."""
        return "bge" in self.model.lower()
```

---

## Chunking Configuration

### Default Settings

| Setting | Value | Rationale |
|---------|-------|-----------|
| **Strategy** | `sentence` | Preserves semantic boundaries |
| **Target Size** | 512 tokens | Balanced context/precision |
| **Max Size** | 768 tokens | Hard limit for embedding model |
| **Overlap** | 50 tokens (~10%) | Maintains boundary context |

### ChunkingConfig

```python
from pydantic import BaseModel, Field
from enum import Enum

class ChunkingStrategy(str, Enum):
    SENTENCE = "sentence"
    RECURSIVE = "recursive"
    FIXED = "fixed"

class ChunkingConfig(BaseModel):
    """Text chunking configuration."""

    strategy: ChunkingStrategy = ChunkingStrategy.SENTENCE
    target_tokens: int = Field(512, ge=100, le=2000)
    max_tokens: int = Field(768, ge=200, le=4000)
    min_tokens: int = Field(50, ge=10, le=500)
    overlap_tokens: int = Field(50, ge=0, le=200)

    @property
    def overlap_percent(self) -> float:
        """Calculate overlap as percentage of target."""
        return self.overlap_tokens / self.target_tokens * 100
```

---

## Related Documentation

- [State-of-the-Art Data Schemas](../development/research/state-of-the-art-data-schemas.md) - Research findings
- [ADR-0002: ChromaDB Vector Store](../development/decisions/adrs/0002-chromadb-vector-store.md)
- [ADR-0006: Citation System](../development/decisions/adrs/0006-citation-system.md)
- [ADR-0018: Chunking Strategy](../development/decisions/adrs/0018-chunking-strategy.md)
- [F-003: Chunking Engine](../development/features/completed/F-003-chunking-engine.md)
- [F-009: Citation Output](../development/features/completed/F-009-citation-output.md)

---

**Status**: Reference specification for v0.1.0
