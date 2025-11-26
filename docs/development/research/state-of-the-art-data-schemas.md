# State-of-the-Art RAG Data Schema Patterns

Comprehensive research on data schema design for RAG systems: Pydantic models, ChromaDB patterns, document-chunk relationships, and citation metadata.

## Executive Summary

Effective RAG systems require carefully designed data schemas that balance retrieval efficiency, citation accuracy, and maintainability. Based on 2024-2025 research and production implementations, the key recommendations are:

### Key Recommendations

1. **Use Pydantic for Validation** - Define strict schemas for documents and chunks with runtime validation
2. **Parent-Child Architecture** - Store parent documents separately from searchable child chunks
3. **Position Tracking is Critical** - Preserve page numbers, character offsets, and section headers for citations
4. **Chunk Overlap in Metadata** - Track overlap windows (10-20%) to maintain context across boundaries
5. **ChromaDB Metadata Patterns** - Use flat JSON metadata structures; avoid deep nesting
6. **Bidirectional References** - Both chunks→document and document→chunks mappings improve retrieval flexibility

**Target Architecture**: SQLite for document/chunk metadata + ChromaDB for embeddings + bidirectional ID references.

---

## ChromaDB Metadata Best Practices

### Core Principles

ChromaDB stores metadata as JSON payloads alongside embeddings. Recent best practices (2024-2025) emphasise:

1. **Flat metadata structures** - ChromaDB performs better with flat key-value pairs than nested objects
2. **Metadata filtering before similarity search** - Use `where={...}` conditions to narrow search space
3. **Self-querying patterns** - Let LLMs extract metadata filters from natural language queries
4. **Persistent storage** - Always use `PersistentClient` for production systems

### Common Metadata Fields

Based on production RAG implementations:

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| `source` | `str` | Document identifier | `"report.pdf"` |
| `doc_id` | `str` | UUID reference to parent doc | `"doc_123e4567"` |
| `page` | `int` | Page number for citations | `5` |
| `chunk_index` | `int` | Position in document | `12` |
| `section` | `str` | Section heading | `"Revenue Analysis"` |
| `char_start` | `int` | Character offset start | `2450` |
| `char_end` | `int` | Character offset end | `2890` |
| `timestamp` | `str` | ISO8601 ingestion time | `"2024-11-26T10:30:00Z"` |
| `tags` | `list[str]` | User-defined categories | `["quarterly", "finance"]` |
| `author` | `str` | Document author | `"Smith, J."` |

**Sources**:
- [Elevate your projects with the powerful Chroma vector database in RAG workflows](https://www.claila.com/blog/chroma-vector-database)
- [Ultimate Guide to Chroma Vector Database](https://mlexplained.blog/2024/04/09/ultimate-guide-to-chroma-vector-database-everything-you-need-to-know-part-1/)

### ChromaDB-Specific Patterns

#### 1. Distance Function Configuration

For cosine similarity (recommended for sentence-transformers):

```python
collection = client.create_collection(
    name="documents",
    metadata={"hnsw:space": "cosine"}
)

# Query returns cosine distance; convert to similarity:
# cosine_similarity = 1 - cosine_distance
```

**Why cosine?** Sentence-transformers models produce normalised embeddings optimised for cosine similarity.

**Source**: [Learn How to Use Chroma DB](https://www.datacamp.com/tutorial/chromadb-tutorial-step-by-step-guide)

#### 2. Metadata Filtering Syntax

ChromaDB supports rich filtering operators:

```python
# Single condition
results = collection.query(
    query_embeddings=[embedding],
    where={"source": "report.pdf"}
)

# Multiple conditions (AND)
results = collection.query(
    query_embeddings=[embedding],
    where={
        "$and": [
            {"page": {"$gte": 5}},
            {"page": {"$lte": 10}},
            {"tags": {"$in": ["finance", "quarterly"]}}
        ]
    }
)

# Complex nested filters
results = collection.query(
    query_embeddings=[embedding],
    where={
        "$or": [
            {"author": "Smith"},
            {"$and": [
                {"date": {"$gte": "2024-01-01"}},
                {"department": "engineering"}
            ]}
        ]
    }
)
```

**Supported operators**: `$eq`, `$ne`, `$gt`, `$gte`, `$lt`, `$lte`, `$in`, `$nin`, `$and`, `$or`

**Source**: [Advanced RAG techniques with LangChain — Part 7](https://medium.com/@roberto.g.infante/advanced-rag-techniques-with-langchain-part-7-843ecd3199f0)

#### 3. Dynamic Metadata Updates

ChromaDB allows updating metadata without re-embedding:

```python
collection.update(
    ids=["chunk_001"],
    metadatas=[{
        "tags": ["finance", "quarterly", "reviewed"],  # Updated tags
        "reviewed_by": "Alice",
        "review_date": "2024-11-26"
    }]
)
```

**Use case**: Adding user annotations, review status, or quality scores post-ingestion.

**Source**: [How to modify metadata for ChromaDB collections?](https://stackoverflow.com/questions/79088240/how-to-modify-metadata-for-chromadb-collections)

#### 4. Self-Querying Pattern

Rather than manual filter specification, use LLMs to extract metadata constraints:

```python
# User query: "Show me finance reports from Q3 2024"
# System extracts:
#   - Semantic query: "finance reports"
#   - Metadata filters: department="finance" AND date >= "2024-07-01" AND date <= "2024-09-30"

from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo

metadata_fields = [
    AttributeInfo(
        name="department",
        description="Department that created the document",
        type="string"
    ),
    AttributeInfo(
        name="date",
        description="Document creation date (YYYY-MM-DD)",
        type="date"
    ),
    AttributeInfo(
        name="doc_type",
        description="Type of document",
        type="string",
        enum=["report", "memo", "contract", "email"]
    )
]

retriever = SelfQueryRetriever.from_llm(
    llm=llm,
    vectorstore=chroma_vectorstore,
    document_content_description="Company documents and reports",
    metadata_field_info=metadata_fields
)
```

**Source**: [How to Build an Authorization System for Your RAG Applications](https://www.cerbos.dev/blog/authorization-for-rag-applications-langchain-chromadb-cerbos)

### ChromaDB Limitations and Workarounds

| Limitation | Impact | Workaround |
|------------|--------|------------|
| No native hybrid search (BM25 + vector) | Cannot combine keyword + semantic search | Use separate BM25 index or implement client-side |
| No nested metadata indexing | Deep object structures slow filtering | Flatten metadata to top-level keys |
| No full-text search on metadata | Cannot search within metadata strings | Use external search index (e.g., SQLite FTS5) |
| Limited aggregations | Cannot compute stats across chunks | Store summaries in separate metadata database |

**Recommendation for ragd**: Use ChromaDB for embeddings + metadata filtering, SQLite for complex metadata queries and full-text search.

**Source**: [Best practices for adding file dynamic in LlamaIndex with Chromadb](https://github.com/run-llama/llama_index/discussions/13648)

---

## Document-Chunk Relationship Patterns

### The Parent-Child Pattern

The dominant pattern in production RAG systems separates **parent documents** (original content) from **child chunks** (searchable segments).

#### Why Parent-Child?

**Problem**: Small chunks improve embedding accuracy but lose context.

**Solution**:
1. **Embed small chunks** for precise semantic search
2. **Store parent documents** separately
3. **Retrieve child, return parent** to provide full context to LLM

**Source**: [Parent-Child Retrieval Strategy](https://medium.com/@pinaki.brahma/improve-llm-based-response-through-parent-child-retrieval-strategy-part-1-cde3b1493961)

### Implementation Approaches

#### Approach 1: Sentence Window Retrieval

**Strategy**: Embed individual sentences, but return surrounding context during retrieval.

```
Original document divided into sentences:
[S1] [S2] [S3] [S4] [S5] [S6] [S7] [S8]

Stored embeddings: One per sentence
Retrieved for query: S3
Returned to LLM: [S1, S2, S3, S4, S5]  ← Window of context
```

**Metadata required**:

```python
{
    "doc_id": "doc_123",
    "sentence_index": 3,
    "window_size": 2  # ±2 sentences
}
```

**Retrieval logic**:

```python
# 1. Retrieve most similar sentence
results = collection.query(query_embedding, n_results=5)

# 2. For each result, fetch surrounding window
for result in results:
    sentence_idx = result.metadata["sentence_index"]
    doc_id = result.metadata["doc_id"]

    # Fetch window from database
    context_sentences = db.get_sentences(
        doc_id=doc_id,
        start=sentence_idx - 2,
        end=sentence_idx + 2
    )
```

**Source**: [Modified RAG: Parent Document & Bigger chunk Retriever](https://blog.lancedb.com/modified-rag-parent-document-bigger-chunk-retriever-62b3d1e79bc6/)

#### Approach 2: Hierarchical Document Structure

**Strategy**: Multi-level chunking with parent-child relationships at multiple granularities.

```
Document
├── Chapter 1 (Parent Level 1)
│   ├── Section 1.1 (Parent Level 2)
│   │   ├── Paragraph 1 (Chunk - searchable)
│   │   ├── Paragraph 2 (Chunk - searchable)
│   │   └── Paragraph 3 (Chunk - searchable)
│   └── Section 1.2 (Parent Level 2)
│       ├── Paragraph 4 (Chunk - searchable)
│       └── Paragraph 5 (Chunk - searchable)
└── Chapter 2 (Parent Level 1)
    └── ...
```

**Metadata structure**:

```python
{
    "doc_id": "doc_123",
    "chunk_id": "chunk_456",
    "parent_chunk_id": "section_1.1",  # Immediate parent
    "grandparent_chunk_id": "chapter_1",  # Higher level
    "hierarchy_path": "doc_123/chapter_1/section_1.1/para_1",
    "level": 3  # 0=document, 1=chapter, 2=section, 3=paragraph
}
```

**Retrieval strategies**:

- **Bottom-up**: Find relevant paragraph → retrieve parent section → optionally retrieve chapter
- **Top-down**: Search chapter summaries → drill down to relevant sections → retrieve paragraphs

**Source**: [Document Hierarchy in RAG: Boosting AI Retrieval Efficiency](https://medium.com/@nay1228/document-hierarchy-in-rag-boosting-ai-retrieval-efficiency-aa23f21b5fb9)

#### Approach 3: Chunk with Metadata Links

**Strategy**: Each chunk stores both parent document ID and sequence number for reconstruction.

**Schema**:

```python
@dataclass
class Chunk:
    chunk_id: str
    doc_id: str  # Foreign key to parent document
    sequence_num: int  # Position in document (0-indexed)
    content: str
    embedding: list[float]

    # Navigation metadata
    prev_chunk_id: Optional[str]
    next_chunk_id: Optional[str]

    # Position tracking
    page_numbers: list[int]  # May span pages
    char_start: int
    char_end: int
```

**Retrieval logic**:

```python
# 1. Retrieve relevant chunk
chunk = collection.query(query_embedding, n_results=1)[0]

# 2. Option A: Fetch surrounding chunks by sequence
surrounding_chunks = db.get_chunks(
    doc_id=chunk.doc_id,
    sequence_range=(chunk.sequence_num - 2, chunk.sequence_num + 2)
)

# 3. Option B: Fetch entire parent document
parent_doc = db.get_document(doc_id=chunk.doc_id)
```

**Source**: [Hierarchical Indices in Document Retrieval](https://github.com/NirDiamant/RAG_Techniques/blob/main/all_rag_techniques/hierarchical_indices.ipynb)

### ID Prefix Conventions

For hierarchical relationships, use ID prefixes to represent structure:

```python
# Document ID
doc_id = "doc_20241126_001"

# Chunk IDs with prefix
chunk_ids = [
    "doc_20241126_001#chunk_000",
    "doc_20241126_001#chunk_001",
    "doc_20241126_001#chunk_002",
]

# Extract parent document from chunk ID
def get_parent_id(chunk_id: str) -> str:
    return chunk_id.split("#")[0]

# Get all chunks for document
def get_document_chunks(doc_id: str):
    return collection.get(where={"chunk_id": {"$like": f"{doc_id}#%"}})
```

**Benefits**:
- No separate parent ID field needed
- Easy to identify related chunks
- Natural grouping in databases

**Source**: [Manage RAG documents - Pinecone Docs](https://docs.pinecone.io/guides/data/manage-rag-documents)

---

## Chunk Overlap Handling

### Why Overlap Matters

**Problem**: Relevant information at chunk boundaries gets split, losing context.

**Solution**: Overlap chunks by 10-20% to ensure boundary information appears in multiple chunks.

```
Chunk 1: [────────────────────]
Chunk 2:                [────────────────────]
                       ^^^^ 20% overlap
Chunk 3:                               [────────────────────]
```

**Source**: [How to Chunk Documents for RAG](https://www.multimodal.dev/post/how-to-chunk-documents-for-rag)

### Default Overlap Settings

| Source | Chunk Size | Overlap | Overlap % |
|--------|------------|---------|-----------|
| LlamaIndex default | 1024 tokens | 20 tokens | 2% |
| OpenAI documentation | 800 tokens | 400 tokens | 50% |
| Recommended practice | 512-1024 tokens | 10-20% | 10-20% |

**Source**: [Breaking up is hard to do: Chunking in RAG applications](https://stackoverflow.blog/2024/12/27/breaking-up-is-hard-to-do-chunking-in-rag-applications/)

### Overlap Metadata Pattern

Track overlap windows in chunk metadata:

```python
@dataclass
class ChunkMetadata:
    chunk_id: str
    doc_id: str
    sequence_num: int

    # Content boundaries
    char_start: int  # Start in original document
    char_end: int    # End in original document

    # Overlap tracking
    overlap_prev_chars: int  # How many chars overlap with previous chunk
    overlap_next_chars: int  # How many chars overlap with next chunk

    # For deduplication during retrieval
    unique_content_start: int  # Start of non-overlapping content
    unique_content_end: int    # End of non-overlapping content
```

**Example**:

```python
# Document: 1000 characters, 3 chunks with 20% overlap

chunk_1 = ChunkMetadata(
    chunk_id="c1",
    char_start=0,
    char_end=400,
    overlap_prev_chars=0,
    overlap_next_chars=80,  # 20% of 400
    unique_content_start=0,
    unique_content_end=320
)

chunk_2 = ChunkMetadata(
    chunk_id="c2",
    char_start=320,  # Overlaps with chunk_1
    char_end=720,
    overlap_prev_chars=80,
    overlap_next_chars=80,
    unique_content_start=400,
    unique_content_end=640
)

chunk_3 = ChunkMetadata(
    chunk_id="c3",
    char_start=640,  # Overlaps with chunk_2
    char_end=1000,
    overlap_prev_chars=80,
    overlap_next_chars=0,
    unique_content_start=720,
    unique_content_end=1000
)
```

**Source**: [Chunk size and overlap | Unstract Documentation](https://docs.unstract.com/unstract/unstract_platform/user_guides/chunking/)

### Trade-offs

| Aspect | More Overlap | Less Overlap |
|--------|--------------|--------------|
| Context preservation | ✅ Better | ❌ Worse |
| Retrieval redundancy | ❌ Higher (same content in multiple chunks) | ✅ Lower |
| Storage efficiency | ❌ More storage needed | ✅ Less storage |
| Computational cost | ❌ More embeddings | ✅ Fewer embeddings |
| IoU scores (metrics) | ❌ Penalised for redundancy | ✅ Better scores |

**Recommendation**: Start with 10-20% overlap, measure retrieval quality, adjust based on domain.

**Source**: [Evaluating Chunking Strategies for Retrieval](https://research.trychroma.com/evaluating-chunking)

---

## Pydantic Model Design for RAG

### Why Pydantic?

Modern RAG systems (2024-2025) use Pydantic for:

1. **Runtime validation** - Catch schema errors during ingestion, not retrieval
2. **Type safety** - IDE autocomplete and static type checking
3. **Serialisation** - JSON ↔ Python objects with automatic validation
4. **LLM integration** - PydanticAI, LangChain, LlamaIndex all use Pydantic for structured outputs

**Source**: [PydanticAI in Practice](https://bix-tech.com/pydanticai-in-practice-a-complete-guide-to-data-validation-and-quality-control-for-ai-systems/)

### Document Schema

```python
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
from enum import Enum

class DocumentType(str, Enum):
    """Document classification"""
    PDF = "pdf"
    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"

class DocumentSchema(BaseModel):
    """Parent document metadata"""

    # Identifiers
    doc_id: str = Field(..., description="Unique document identifier (UUID)")
    source_path: str = Field(..., description="Original file path")
    source_hash: str = Field(..., description="SHA-256 hash of original file")

    # Dublin Core metadata
    title: Optional[str] = Field(None, description="Document title")
    creator: Optional[list[str]] = Field(default_factory=list, description="Authors/creators")
    subject: Optional[list[str]] = Field(default_factory=list, description="Keywords/topics")
    description: Optional[str] = Field(None, description="Summary or abstract")
    date_created: Optional[datetime] = Field(None, description="Original creation date")
    doc_type: DocumentType = Field(..., description="Document format type")
    language: str = Field(default="en", description="ISO 639-1 language code")

    # RAG-specific fields
    chunk_count: int = Field(..., ge=0, description="Number of chunks generated")
    total_chars: int = Field(..., ge=0, description="Total character count")
    embedding_model: str = Field(..., description="Model used for embeddings")

    # Timestamps
    ingestion_date: datetime = Field(default_factory=datetime.utcnow)
    last_modified: datetime = Field(default_factory=datetime.utcnow)

    # User metadata
    tags: list[str] = Field(default_factory=list, description="User-defined tags")
    project: Optional[str] = Field(None, description="Project classification")

    class Config:
        json_schema_extra = {
            "example": {
                "doc_id": "doc_123e4567-e89b-12d3-a456-426614174000",
                "source_path": "/documents/report.pdf",
                "source_hash": "a3c5f...",
                "title": "Q3 2024 Financial Report",
                "creator": ["Smith, J.", "Doe, A."],
                "subject": ["finance", "quarterly", "revenue"],
                "doc_type": "pdf",
                "chunk_count": 42,
                "total_chars": 15000,
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "tags": ["finance", "2024"]
            }
        }

    @validator("source_hash")
    def validate_hash(cls, v):
        """Ensure hash is valid SHA-256"""
        if len(v) != 64:
            raise ValueError("source_hash must be 64-character SHA-256 hash")
        return v.lower()
```

**Source**: [GitHub - avsolatorio/metaschema: Repository of Pydantic models for metadata schema](https://github.com/avsolatorio/metaschema)

### Chunk Schema

```python
from pydantic import BaseModel, Field, validator
from typing import Optional

class ChunkSchema(BaseModel):
    """Individual chunk metadata with position tracking"""

    # Identifiers
    chunk_id: str = Field(..., description="Unique chunk identifier (UUID)")
    doc_id: str = Field(..., description="Parent document ID (foreign key)")

    # Position tracking
    sequence_num: int = Field(..., ge=0, description="Position in document (0-indexed)")
    char_start: int = Field(..., ge=0, description="Character offset start in original doc")
    char_end: int = Field(..., gt=0, description="Character offset end in original doc")

    # Content
    content: str = Field(..., min_length=1, description="Chunk text content")
    content_hash: str = Field(..., description="SHA-256 hash of content for dedup")

    # Citation metadata
    page_numbers: list[int] = Field(default_factory=list, description="Pages this chunk spans")
    section_heading: Optional[str] = Field(None, description="Section/heading this chunk belongs to")

    # Overlap tracking
    overlap_prev_chars: int = Field(default=0, ge=0, description="Characters overlapping with previous chunk")
    overlap_next_chars: int = Field(default=0, ge=0, description="Characters overlapping with next chunk")

    # Navigation
    prev_chunk_id: Optional[str] = Field(None, description="Previous chunk ID in sequence")
    next_chunk_id: Optional[str] = Field(None, description="Next chunk ID in sequence")

    # Embedding metadata (NOT the embedding itself - stored in ChromaDB)
    embedding_model: str = Field(..., description="Model used for this chunk's embedding")
    embedding_timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": "chunk_987fcdeb-51a2-43d7-8c9d-1234567890ab",
                "doc_id": "doc_123e4567-e89b-12d3-a456-426614174000",
                "sequence_num": 5,
                "char_start": 2450,
                "char_end": 2890,
                "content": "The quarterly revenue increased by 15%...",
                "content_hash": "b7f3a...",
                "page_numbers": [5, 6],
                "section_heading": "Revenue Analysis",
                "overlap_prev_chars": 50,
                "overlap_next_chars": 50,
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
            }
        }

    @validator("char_end")
    def validate_char_range(cls, v, values):
        """Ensure char_end > char_start"""
        if "char_start" in values and v <= values["char_start"]:
            raise ValueError("char_end must be greater than char_start")
        return v

    @validator("content_hash")
    def validate_content_hash(cls, v):
        """Ensure hash is valid SHA-256"""
        if len(v) != 64:
            raise ValueError("content_hash must be 64-character SHA-256 hash")
        return v.lower()
```

**Source**: [RAG - Pydantic AI](https://ai.pydantic.dev/examples/rag/)

### ChromaDB Integration Schema

```python
class ChromaDBMetadata(BaseModel):
    """Flattened metadata for ChromaDB storage (no nesting)"""

    # Document reference
    doc_id: str
    source: str  # source_path for filtering

    # Position (for citations)
    chunk_index: int  # sequence_num
    page: Optional[int] = None  # First page if multi-page chunk
    pages: Optional[str] = None  # "5,6" for multi-page chunks
    section: Optional[str] = None  # section_heading

    # Character positions (for reconstruction)
    char_start: int
    char_end: int

    # Document-level metadata (duplicated for filtering)
    title: Optional[str] = None
    author: Optional[str] = None  # First author if multiple
    date: Optional[str] = None  # ISO8601 string

    # User metadata
    tags: Optional[str] = None  # Comma-separated: "finance,quarterly,2024"
    project: Optional[str] = None

    # Timestamps
    timestamp: str  # ISO8601 ingestion time

    class Config:
        json_schema_extra = {
            "example": {
                "doc_id": "doc_123e4567",
                "source": "report.pdf",
                "chunk_index": 5,
                "page": 5,
                "pages": "5,6",
                "section": "Revenue Analysis",
                "char_start": 2450,
                "char_end": 2890,
                "title": "Q3 2024 Financial Report",
                "author": "Smith, J.",
                "date": "2024-01-15",
                "tags": "finance,quarterly,2024",
                "timestamp": "2024-11-26T10:30:00Z"
            }
        }

    def to_chromadb_dict(self) -> dict:
        """Convert to ChromaDB-compatible metadata dict"""
        return {k: v for k, v in self.model_dump().items() if v is not None}
```

**Why flatten?** ChromaDB performs better with flat structures. Instead of `{"tags": ["finance", "quarterly"]}`, use `{"tags": "finance,quarterly"}`.

**Source**: [Advanced RAG: Automated Structured Metadata Enrichment](https://haystack.deepset.ai/cookbook/metadata_enrichment)

### Validation Patterns

```python
from pydantic import BaseModel, validator, root_validator

class ValidatedChunk(BaseModel):
    """Chunk with comprehensive validation"""

    content: str
    char_start: int
    char_end: int
    page_numbers: list[int]

    @validator("content")
    def content_not_empty(cls, v):
        """Ensure content has substance"""
        if not v.strip():
            raise ValueError("Chunk content cannot be empty or whitespace")
        if len(v) < 10:
            raise ValueError("Chunk content too short (min 10 chars)")
        return v

    @validator("page_numbers")
    def pages_sequential(cls, v):
        """Ensure page numbers are sequential"""
        if not v:
            return v
        sorted_pages = sorted(v)
        if sorted_pages != v:
            raise ValueError("Page numbers must be in sequential order")
        # Check for gaps
        for i in range(len(sorted_pages) - 1):
            if sorted_pages[i+1] - sorted_pages[i] > 1:
                raise ValueError(f"Page number gap between {sorted_pages[i]} and {sorted_pages[i+1]}")
        return v

    @root_validator
    def validate_consistency(cls, values):
        """Cross-field validation"""
        char_start = values.get("char_start")
        char_end = values.get("char_end")
        content = values.get("content")

        if char_start and char_end and content:
            expected_length = char_end - char_start
            actual_length = len(content)

            # Allow some tolerance for whitespace normalisation
            if abs(expected_length - actual_length) > 5:
                raise ValueError(
                    f"Content length ({actual_length}) doesn't match "
                    f"char range ({expected_length})"
                )

        return values
```

**Source**: [Building Intelligent AI Agents with PydanticAI and RAG](https://medium.com/@eng.aa.azeem/building-intelligent-ai-agents-with-pydanticai-and-rag-a-step-by-step-guide-9248bf47ac0b)

---

## Citation Metadata Fields

### The Citation Challenge

Production RAG systems must answer: **"Where did this information come from?"**

Effective citations require precise source attribution at multiple levels:

1. **Document level** - Which document?
2. **Page level** - Which page(s)?
3. **Section level** - Which section/heading?
4. **Chunk level** - Which specific passage?

**Source**: [Retrieval Augmented Generation with Citations](https://zilliz.com/blog/retrieval-augmented-generation-with-citations)

### Citation Metadata Schema

```python
from pydantic import BaseModel, Field
from typing import Optional

class CitationMetadata(BaseModel):
    """Complete metadata for accurate source attribution"""

    # Document identification
    doc_id: str = Field(..., description="Unique document identifier")
    source_path: str = Field(..., description="Original file path")
    title: Optional[str] = Field(None, description="Document title")
    author: Optional[str] = Field(None, description="Primary author")
    date: Optional[str] = Field(None, description="Publication/creation date")

    # Location within document
    page_numbers: list[int] = Field(default_factory=list, description="Page(s) containing this content")
    section_heading: Optional[str] = Field(None, description="Section or chapter heading")

    # Precise position (for exact quotes)
    char_start: int = Field(..., description="Character offset in original document")
    char_end: int = Field(..., description="End character offset")

    # Retrieval metadata
    chunk_id: str = Field(..., description="Retrieved chunk identifier")
    retrieval_score: float = Field(..., ge=0.0, le=1.0, description="Similarity/relevance score")

    # Content excerpt
    excerpt: str = Field(..., description="Actual text content retrieved")

    class Config:
        json_schema_extra = {
            "example": {
                "doc_id": "doc_123e4567",
                "source_path": "reports/Q3_2024_Financial.pdf",
                "title": "Q3 2024 Financial Report",
                "author": "Smith, J.",
                "date": "2024-10-15",
                "page_numbers": [5, 6],
                "section_heading": "Revenue Analysis",
                "char_start": 2450,
                "char_end": 2890,
                "chunk_id": "chunk_987fcdeb",
                "retrieval_score": 0.89,
                "excerpt": "The quarterly revenue increased by 15%..."
            }
        }
```

**Source**: [Build RAG with in-line citations](https://docs.llamaindex.ai/en/stable/examples/workflow/citation_query_engine/)

### Citation Output Formats

#### 1. LangChain Pattern: CitedAnswer

```python
from pydantic import BaseModel

class Citation(BaseModel):
    """Individual source reference"""
    source_id: int  # Reference number [1], [2], etc.
    quote: str  # Exact text from source
    doc_title: str
    page: Optional[int] = None

class CitedAnswer(BaseModel):
    """Answer with inline citations"""
    answer: str  # Response with citation markers like [1], [2]
    citations: list[Citation]  # Ordered list of sources

# Example output:
# {
#   "answer": "Revenue increased by 15% in Q3 [1], driven by strong performance in Asia [2].",
#   "citations": [
#     {"source_id": 1, "quote": "quarterly revenue increased by 15%",
#      "doc_title": "Q3 Financial Report", "page": 5},
#     {"source_id": 2, "quote": "Asia-Pacific region grew 22%",
#      "doc_title": "Regional Analysis", "page": 12}
#   ]
# }
```

**Source**: [How to get a RAG application to add citations](https://python.langchain.com/v0.2/docs/how_to/qa_citations/)

#### 2. LlamaIndex Pattern: CitationQueryEngine

```python
from llama_index.core.response.schema import Response

class SourceNode(BaseModel):
    """Source node with citation info"""
    node_id: str
    text: str
    metadata: dict  # Includes page, section, etc.
    score: float

class CitedResponse(Response):
    """Response with source nodes"""
    response: str  # Generated answer
    source_nodes: list[SourceNode]  # Sources used

    def get_formatted_sources(self) -> str:
        """Format sources as citations"""
        citations = []
        for i, node in enumerate(self.source_nodes, 1):
            page = node.metadata.get("page", "unknown")
            title = node.metadata.get("title", "unknown")
            citations.append(f"[{i}] {title}, p. {page}")
        return "\n".join(citations)
```

**Source**: [In-Text Citing for RAG Question-Answering](https://medium.com/@yotamabraham/in-text-citing-with-langchain-question-answering-e19a24d81e39)

#### 3. Academic Citation Format

For research-oriented applications:

```python
class AcademicCitation(BaseModel):
    """APA-style citation components"""
    authors: list[str]  # ["Smith, J.", "Doe, A."]
    year: Optional[int] = None
    title: str
    source: str  # Journal, publisher, or file path
    pages: Optional[str] = None  # "45-47"
    doi: Optional[str] = None
    url: Optional[str] = None

    def format_apa(self) -> str:
        """Generate APA citation"""
        author_str = ", ".join(self.authors) if self.authors else "Unknown"
        year_str = f"({self.year})" if self.year else "(n.d.)"

        citation = f"{author_str} {year_str}. {self.title}. {self.source}"

        if self.pages:
            citation += f", pp. {self.pages}"
        if self.doi:
            citation += f". https://doi.org/{self.doi}"
        elif self.url:
            citation += f". {self.url}"

        return citation

# Example:
# "Smith, J., Doe, A. (2024). Q3 Financial Report. Corporate Finance Quarterly, pp. 45-47."
```

**Source**: [Building Trustworthy RAG Systems with In Text Citations](https://haruiz.github.io/blog/improve-rag-systems-reliability-with-citations)

### Multi-Hop Citation Tracking

For RAG systems that retrieve from multiple sources:

```python
class MultiHopCitation(BaseModel):
    """Citation for answers synthesised from multiple sources"""

    claim: str  # The specific claim in the answer
    supporting_sources: list[CitationMetadata]  # All sources supporting this claim
    confidence: float = Field(..., ge=0.0, le=1.0)

    class Config:
        json_schema_extra = {
            "example": {
                "claim": "Revenue increased by 15% in Q3",
                "supporting_sources": [
                    {
                        "doc_id": "doc_123",
                        "title": "Q3 Report",
                        "page_numbers": [5],
                        "excerpt": "quarterly revenue increased by 15%",
                        "retrieval_score": 0.92
                    },
                    {
                        "doc_id": "doc_456",
                        "title": "Financial Summary",
                        "page_numbers": [2],
                        "excerpt": "Q3 growth: 15%",
                        "retrieval_score": 0.87
                    }
                ],
                "confidence": 0.95
            }
        }
```

**Why track multiple sources?** Cross-verification and redundancy increase answer trustworthiness.

**Source**: [Citations | LangChain](https://python.langchain.com/v0.1/docs/use_cases/question_answering/citations/)

---

## Sentence-Transformers Embedding Dimensions

### Default Models and Dimensions

| Model | Dimensions | Speed | Quality | Use Case |
|-------|-----------|-------|---------|----------|
| `all-MiniLM-L6-v2` | **384** | Fast | Good | General purpose (ChromaDB default) |
| `all-MiniLM-L12-v2` | 384 | Medium | Better | Higher quality |
| `sentence-t5-base` | **768** | Slow | High | Research, precision-critical |
| `paraphrase-MiniLM-L3-v2` | 384 | Very fast | Moderate | Speed-critical applications |
| `all-mpnet-base-v2` | 768 | Medium | Best | Production RAG (recommended) |

**Default for ChromaDB**: `all-MiniLM-L6-v2` (384 dimensions)

**Source**:
- [Chroma Embedding Functions](https://docs.trychroma.com/docs/embeddings/embedding-functions)
- [Write a Custom Embedding Function for Chroma DB](https://mobiarch.wordpress.com/2024/03/13/write-a-custom-embedding-function-for-chroma-db/)

### Schema Implications

Store embedding model info in metadata for version tracking:

```python
class EmbeddingConfig(BaseModel):
    """Track embedding model configuration"""
    model_name: str = Field(..., description="Full model name")
    dimensions: int = Field(..., description="Embedding vector dimensions")
    max_seq_length: int = Field(..., description="Maximum sequence length")

    # For ragd default
    DEFAULT = {
        "model_name": "sentence-transformers/all-MiniLM-L6-v2",
        "dimensions": 384,
        "max_seq_length": 256
    }

    @classmethod
    def validate_dimensions(cls, embeddings: list[float], expected_dim: int):
        """Ensure embedding has correct dimensions"""
        if len(embeddings) != expected_dim:
            raise ValueError(
                f"Embedding dimension mismatch: got {len(embeddings)}, "
                f"expected {expected_dim}"
            )
```

**Why track this?** If you change embedding models, you must re-embed ALL chunks. Tracking prevents mixing incompatible embeddings.

**Source**: [Use Chromadb with Langchain and embedding from SentenceTransformer model](https://github.com/langchain-ai/langchain/discussions/7818)

### Custom Embedding Functions

```python
from chromadb.api.types import EmbeddingFunction
from sentence_transformers import SentenceTransformer

class CustomEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.dimensions = self.model.get_sentence_embedding_dimension()

    def __call__(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts"""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

# Use with ChromaDB
embedding_fn = CustomEmbeddingFunction("all-mpnet-base-v2")
collection = client.create_collection(
    name="documents",
    embedding_function=embedding_fn,
    metadata={"hnsw:space": "cosine"}  # Match sentence-transformers optimisation
)
```

**Source**: [Creating your own embedding function - Chroma Cookbook](https://cookbook.chromadb.dev/embeddings/bring-your-own-embeddings/)

---

## Recommended Schema Architecture for ragd

### Database Schema (SQLite)

```sql
-- Documents table
CREATE TABLE documents (
    doc_id TEXT PRIMARY KEY,
    source_path TEXT NOT NULL UNIQUE,
    source_hash TEXT NOT NULL UNIQUE,

    -- Dublin Core metadata
    title TEXT,
    creator TEXT,  -- JSON array: ["Author 1", "Author 2"]
    subject TEXT,  -- JSON array: ["keyword1", "keyword2"]
    description TEXT,
    date_created TEXT,  -- ISO8601
    doc_type TEXT NOT NULL,
    language TEXT DEFAULT 'en',

    -- RAG metadata
    chunk_count INTEGER NOT NULL,
    total_chars INTEGER NOT NULL,
    embedding_model TEXT NOT NULL,

    -- Timestamps
    ingestion_date TEXT NOT NULL,
    last_modified TEXT NOT NULL,

    -- User metadata
    tags TEXT,  -- JSON array
    project TEXT,

    -- Indexes for filtering
    CHECK (chunk_count >= 0),
    CHECK (total_chars >= 0)
);

CREATE INDEX idx_documents_source ON documents(source_path);
CREATE INDEX idx_documents_tags ON documents(tags);
CREATE INDEX idx_documents_date ON documents(date_created);

-- Chunks table
CREATE TABLE chunks (
    chunk_id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,

    -- Position
    sequence_num INTEGER NOT NULL,
    char_start INTEGER NOT NULL,
    char_end INTEGER NOT NULL,

    -- Content
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,

    -- Citation metadata
    page_numbers TEXT,  -- JSON array: [5, 6]
    section_heading TEXT,

    -- Overlap tracking
    overlap_prev_chars INTEGER DEFAULT 0,
    overlap_next_chars INTEGER DEFAULT 0,

    -- Navigation
    prev_chunk_id TEXT,
    next_chunk_id TEXT,

    -- Embedding metadata
    embedding_model TEXT NOT NULL,
    embedding_timestamp TEXT NOT NULL,

    FOREIGN KEY (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE,
    FOREIGN KEY (prev_chunk_id) REFERENCES chunks(chunk_id),
    FOREIGN KEY (next_chunk_id) REFERENCES chunks(chunk_id),

    CHECK (sequence_num >= 0),
    CHECK (char_end > char_start),
    CHECK (overlap_prev_chars >= 0),
    CHECK (overlap_next_chars >= 0)
);

CREATE INDEX idx_chunks_doc ON chunks(doc_id);
CREATE INDEX idx_chunks_sequence ON chunks(doc_id, sequence_num);
CREATE INDEX idx_chunks_content_hash ON chunks(content_hash);
CREATE INDEX idx_chunks_page ON chunks(page_numbers);

-- Full-text search on chunks (for hybrid retrieval)
CREATE VIRTUAL TABLE chunks_fts USING fts5(
    chunk_id UNINDEXED,
    content,
    section_heading
);
```

### ChromaDB Schema

Store only essential metadata in ChromaDB (flat structure):

```python
# Metadata stored in ChromaDB (alongside embeddings)
chromadb_metadata = {
    # IDs
    "doc_id": "doc_123e4567",
    "chunk_id": "chunk_987fcdeb",

    # Position (for citations)
    "chunk_index": 5,
    "page": 5,  # First page
    "pages": "5,6",  # All pages (comma-separated)
    "section": "Revenue Analysis",
    "char_start": 2450,
    "char_end": 2890,

    # Document metadata (denormalised for filtering)
    "source": "report.pdf",
    "title": "Q3 2024 Financial Report",
    "author": "Smith, J.",  # First author
    "date": "2024-01-15",

    # User metadata
    "tags": "finance,quarterly,2024",  # Comma-separated
    "project": "acme_corp",

    # Timestamp
    "timestamp": "2024-11-26T10:30:00Z"
}

# Store in ChromaDB
collection.add(
    ids=[chunk_id],
    documents=[chunk_content],
    metadatas=[chromadb_metadata]
)
```

### Retrieval Pattern

```python
# 1. Query ChromaDB (vector search + metadata filter)
results = collection.query(
    query_embeddings=[query_embedding],
    where={
        "$and": [
            {"date": {"$gte": "2024-01-01"}},
            {"tags": {"$like": "%finance%"}}
        ]
    },
    n_results=10
)

# 2. Extract chunk IDs
chunk_ids = [r["chunk_id"] for r in results["metadatas"]]

# 3. Fetch full chunk data from SQLite
chunks = db.execute(
    "SELECT * FROM chunks WHERE chunk_id IN ({})"
    .format(",".join(["?"] * len(chunk_ids))),
    chunk_ids
).fetchall()

# 4. Fetch parent documents if needed
doc_ids = [c["doc_id"] for c in chunks]
documents = db.execute(
    "SELECT * FROM documents WHERE doc_id IN ({})"
    .format(",".join(["?"] * len(doc_ids))),
    doc_ids
).fetchall()

# 5. Construct citations
citations = [
    CitationMetadata(
        doc_id=chunk["doc_id"],
        source_path=doc["source_path"],
        title=doc["title"],
        page_numbers=json.loads(chunk["page_numbers"]),
        section_heading=chunk["section_heading"],
        chunk_id=chunk["chunk_id"],
        retrieval_score=result["distance"],
        excerpt=chunk["content"]
    )
    for chunk, doc, result in zip(chunks, documents, results)
]
```

---

## Key Takeaways

### 1. ChromaDB Metadata Best Practices
- Use **flat metadata structures** (no deep nesting)
- Store **essential filtering fields** (date, author, tags, page)
- Configure **cosine distance** for sentence-transformers
- Use **`PersistentClient`** for production
- Implement **self-querying** for natural language filters

### 2. Document-Chunk Relationships
- **Parent-child pattern** is the industry standard
- Store **bidirectional references** (chunk→doc and doc→chunks)
- Track **sequence numbers** for reconstructing document order
- Use **ID prefixes** for hierarchical relationships (`doc_123#chunk_001`)

### 3. Pydantic Model Design
- Define **strict schemas** with validation for documents and chunks
- Use **`@validator`** decorators for field validation
- Implement **`@root_validator`** for cross-field checks
- Flatten schemas for ChromaDB, keep rich schemas for SQLite

### 4. Citation Metadata
- Store **page numbers, char offsets, section headings**
- Track **retrieval scores** for confidence metrics
- Support **multi-hop citations** (multiple sources per claim)
- Provide **formatted citation outputs** (APA, inline, etc.)

### 5. Chunk Overlap Handling
- Use **10-20% overlap** as default
- Store **`overlap_prev_chars` and `overlap_next_chars`** in metadata
- Track **unique content boundaries** to avoid duplication during retrieval
- Balance **context preservation** vs. **storage efficiency**

### 6. Embedding Configuration
- Default to **`all-MiniLM-L6-v2` (384 dimensions)** for speed
- Upgrade to **`all-mpnet-base-v2` (768 dimensions)** for quality
- **Track embedding model** in both document and chunk metadata
- **Validate dimensions** during ingestion to prevent mixing models

---

## Implementation Checklist for ragd v0.2

- [ ] Define `DocumentSchema` and `ChunkSchema` Pydantic models
- [ ] Create SQLite tables with proper indexes and foreign keys
- [ ] Implement `ChromaDBMetadata` flattening logic
- [ ] Configure ChromaDB with `cosine` distance metric
- [ ] Store page numbers, char offsets, and section headings in chunks
- [ ] Implement chunk overlap tracking (10-20%)
- [ ] Add embedding model version tracking
- [ ] Create citation output formatters (inline, APA)
- [ ] Implement parent-child retrieval logic
- [ ] Add bidirectional chunk navigation (prev/next)
- [ ] Create metadata update functionality (tags, annotations)
- [ ] Implement self-querying retriever (optional, v0.3+)

---

## References

### ChromaDB Documentation
- [Chroma Embedding Functions](https://docs.trychroma.com/docs/embeddings/embedding-functions)
- [Creating your own embedding function - Chroma Cookbook](https://cookbook.chromadb.dev/embeddings/bring-your-own-embeddings/)
- [Ultimate Guide to Chroma Vector Database](https://mlexplained.blog/2024/04/09/ultimate-guide-to-chroma-vector-database-everything-you-need-to-know-part-1/)
- [Learn How to Use Chroma DB](https://www.datacamp.com/tutorial/chromadb-tutorial-step-by-step-guide)

### RAG Chunking and Relationships
- [Breaking up is hard to do: Chunking in RAG applications](https://stackoverflow.blog/2024/12/27/breaking-up-is-hard-to-do-chunking-in-rag-applications/)
- [How to Chunk Documents for RAG](https://www.multimodal.dev/post/how-to-chunk-documents-for-rag)
- [Document Hierarchy in RAG: Boosting AI Retrieval Efficiency](https://medium.com/@nay1228/document-hierarchy-in-rag-boosting-ai-retrieval-efficiency-aa23f21b5fb9)
- [Parent-Child Retrieval Strategy](https://medium.com/@pinaki.brahma/improve-llm-based-response-through-parent-child-retrieval-strategy-part-1-cde3b1493961)
- [Modified RAG: Parent Document & Bigger chunk Retriever](https://blog.lancedb.com/modified-rag-parent-document-bigger-chunk-retriever-62b3d1e79bc6/)
- [Hierarchical Indices in Document Retrieval](https://github.com/NirDiamant/RAG_Techniques/blob/main/all_rag_techniques/hierarchical_indices.ipynb)

### Pydantic and Schema Design
- [RAG - Pydantic AI](https://ai.pydantic.dev/examples/rag/)
- [Advanced RAG: Automated Structured Metadata Enrichment](https://haystack.deepset.ai/cookbook/metadata_enrichment)
- [GitHub - avsolatorio/metaschema](https://github.com/avsolatorio/metaschema)
- [PydanticAI in Practice](https://bix-tech.com/pydanticai-in-practice-a-complete-guide-to-data-validation-and-quality-control-for-ai-systems/)
- [Building Intelligent AI Agents with PydanticAI and RAG](https://medium.com/@eng.aa.azeem/building-intelligent-ai-agents-with-pydanticai-and-rag-a-step-by-step-guide-9248bf47ac0b)

### Citation Systems
- [Retrieval Augmented Generation with Citations](https://zilliz.com/blog/retrieval-augmented-generation-with-citations)
- [Build RAG with in-line citations](https://docs.llamaindex.ai/en/stable/examples/workflow/citation_query_engine/)
- [How to get a RAG application to add citations](https://python.langchain.com/v0.2/docs/how_to/qa_citations/)
- [Building Trustworthy RAG Systems with In Text Citations](https://haruiz.github.io/blog/improve-rag-systems-reliability-with-citations)
- [In-Text Citing for RAG Question-Answering](https://medium.com/@yotamabraham/in-text-citing-with-langchain-question-answering-e19a24d81e39)
- [Citations | LangChain](https://python.langchain.com/v0.1/docs/use_cases/question_answering/citations/)

### Metadata Filtering
- [Advanced RAG techniques with LangChain — Part 7](https://medium.com/@roberto.g.infante/advanced-rag-techniques-with-langchain-part-7-843ecd3199f0)
- [How to Build an Authorization System for Your RAG Applications](https://www.cerbos.dev/blog/authorization-for-rag-applications-langchain-chromadb-cerbos)
- [Dynamic Metadata RAG — Using LLMs for Metadata Generation](https://medium.com/@anvesha6496/dynamic-metadata-rag-using-llms-for-metadata-generation-939c3e0fa05b)

### Chunk Overlap
- [Chunk size and overlap | Unstract Documentation](https://docs.unstract.com/unstract/unstract_platform/user_guides/chunking/)
- [Evaluating Chunking Strategies for Retrieval](https://research.trychroma.com/evaluating-chunking)

### Database Patterns
- [Manage RAG documents - Pinecone Docs](https://docs.pinecone.io/guides/data/manage-rag-documents)
- [Best practices for adding file dynamic in LlamaIndex with Chromadb](https://github.com/run-llama/llama_index/discussions/13648)

---

## Related Documentation

- [State-of-the-Art Metadata](./state-of-the-art-metadata.md) - Document metadata extraction and standards
- [State-of-the-Art Chunking](./state-of-the-art-chunking.md) - Text chunking strategies
- [Citation Systems Research](./citation-systems.md) - Citation formats and academic standards
- [State-of-the-Art Embeddings](./state-of-the-art-embeddings.md) - Embedding model selection

---

**Status**: Research complete, ready for v0.2 schema implementation
