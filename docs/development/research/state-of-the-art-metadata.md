# State-of-the-Art Document Metadata for RAG Systems

> **Note:** This document surveys state-of-the-art techniques including commercial
> cloud services. ragd implements **local-only** processing. Cloud service integration
> is not planned until v2.0+.

Techniques for extracting, storing, and leveraging document metadata to enable tagging, selection, citation, and traceability.

## Executive Summary

Metadata is the invisible backbone of effective RAG systems. Beyond simple retrieval, well-structured metadata enables:
- **Filtering and selection** - narrow retrieval to relevant document subsets
- **Citation and attribution** - trace answers back to source documents and pages
- **Tagging and organisation** - categorise documents for user navigation
- **Provenance and traceability** - audit trail for compliance and trust

Recent advances (2024-2025) show that **LLM-based metadata extraction** combined with **self-querying retrievers** dramatically improves retrieval precision. The key insight: treat metadata as a first-class citizen in your RAG pipeline, not an afterthought.

---

## Metadata Hierarchy: Document vs Chunk Level

Understanding the two levels of metadata is critical for ragd's architecture:

### Document-Level Metadata

| Field | Source | Purpose |
|-------|--------|---------|
| Title | PDF properties, LLM extraction | Display, search |
| Author(s) | PDF properties, LLM extraction | Attribution, filtering |
| Date created/modified | File system, PDF properties | Temporal filtering |
| Source path | File system | Citation, deduplication |
| Document type | LLM classification | Filtering by category |
| Language | Detection (langdetect, fastText) | Multi-language support |
| Summary | LLM extraction | Preview, context |
| Keywords/tags | KeyBERT, LLM extraction | Tagging, navigation |

### Chunk-Level Metadata

| Field | Source | Purpose |
|-------|--------|---------|
| Page number | PDF extraction | Citation |
| Section/heading | Structure detection | Context, navigation |
| Chunk index | Chunking pipeline | Ordering, adjacency |
| Parent document ID | Foreign key | Traceability |
| Entities | NER (spaCy, transformers) | Entity-based retrieval |
| Questions answered | LLM extraction | Query matching |

**Source:** [LlamaIndex Metadata Extraction](https://docs.llamaindex.ai/en/stable/module_guides/indexing/metadata_extraction/)

### Best Practice: Contextualised Chunk Embeddings

Traditional chunking loses document context. Modern approaches solve this:

1. **Prepend document context** to each chunk before embedding
2. **Voyage-context-3** model encodes both chunk content and document context in a single embedding
3. **Metadata injection** adds title/summary to chunk text

```
# Traditional chunk embedding
embed("The quarterly revenue increased by 15%.")

# Contextualised chunk embedding
embed("Document: Q3 2024 Financial Report. Section: Revenue Analysis. Content: The quarterly revenue increased by 15%.")
```

**Source:** [Voyage AI Context Model](https://www.mongodb.com/company/blog/product-release-announcements/voyage-context-3-focused-chunk-level-details-global-document-context)

---

## Metadata Extraction Techniques

### 1. Algorithmic Extraction (Fast, No LLM)

**PDF Properties Extraction:**
```python
# PyMuPDF example
doc = fitz.open("document.pdf")
metadata = doc.metadata  # title, author, subject, keywords, creator, producer, dates
```

**Keyword Extraction with KeyBERT:**

[KeyBERT](https://github.com/MaartenGr/KeyBERT) uses BERT embeddings to extract keywords most similar to the document:

```python
from keybert import KeyBERT
kw_model = KeyBERT()
keywords = kw_model.extract_keywords(doc_text, keyphrase_ngram_range=(1, 2), top_n=10)
```

**Why KeyBERT for RAG:**
- Improves sparse retrieval (BM25) in hybrid search
- Generates consistent tags for document categorisation
- 3 lines of code, no LLM costs

**Source:** [KeyBERT GitHub](https://github.com/MaartenGr/KeyBERT), [KeyBERT for Hybrid RAG](https://medium.com/@raghutapas12/harnessing-the-power-of-hybrid-search-enhancing-rag-systems-with-keybert-d4901733eeb2)

**Named Entity Recognition (NER):**

```python
import spacy
nlp = spacy.load("en_core_web_trf")  # Transformer-based
doc = nlp(text)
entities = [(ent.text, ent.label_) for ent in doc.ents]
# [("Apple Inc.", "ORG"), ("Tim Cook", "PERSON"), ("Cupertino", "GPE")]
```

### 2. LLM-Based Extraction (Rich, Flexible)

For complex metadata that requires understanding:

**LlamaIndex MetadataExtractor:**

```python
from llama_index.core.extractors import (
    TitleExtractor,
    SummaryExtractor,
    QuestionsAnsweredExtractor,
    EntityExtractor,
)
from llama_index.core.node_parser import SentenceSplitter

extractors = [
    TitleExtractor(nodes=5),
    SummaryExtractor(summaries=["prev", "self", "next"]),
    QuestionsAnsweredExtractor(questions=3),
    EntityExtractor(prediction_threshold=0.5),
]

node_parser = SentenceSplitter()
pipeline = IngestionPipeline(transformations=[node_parser, *extractors])
nodes = pipeline.run(documents=documents)
```

**Benefits:**
- **QuestionsAnsweredExtractor** - enables "chunk dreaming" (chunks know what questions they answer)
- **SummaryExtractor** - captures context from adjacent chunks
- **EntityExtractor** - structured entity extraction for filtering

**Source:** [LlamaIndex Metadata Extraction Guide](https://docs.llamaindex.ai/en/stable/module_guides/indexing/metadata_extraction/)

**Vectorize Automatic Metadata Extraction:**

Define a schema, and the system extracts structured fields automatically:

```python
schema = {
    "document_type": "enum[report, memo, contract, email]",
    "department": "string",
    "urgency": "enum[low, medium, high]",
    "key_dates": "list[date]"
}
```

**Source:** [Vectorize Blog](https://vectorize.io/blog/introducing-automatic-metadata-extraction-supercharge-your-rag-pipelines-with-structured-information)

### 3. Hybrid Approach (Recommended for ragd)

| Metadata Field | Extraction Method | Cost |
|---------------|-------------------|------|
| Title, author, dates | PDF properties | Free |
| Keywords | KeyBERT | Low (local) |
| Entities | spaCy NER | Low (local) |
| Summary | LLM (optional) | Medium |
| Document type | LLM classification | Medium |
| Questions answered | LLM | High |

**Recommendation:** Start with algorithmic extraction for all documents, add LLM extraction for high-value documents or on-demand.

---

## Metadata Storage Architectures

### Option 1: Embedded in Vector Store

Store metadata as payload alongside embeddings:

**ChromaDB:**
```python
collection.add(
    documents=["chunk text"],
    embeddings=[embedding],
    metadatas=[{
        "source": "report.pdf",
        "page": 5,
        "author": "Smith",
        "date": "2024-01-15",
        "tags": ["quarterly", "finance"]
    }],
    ids=["chunk_001"]
)
```

**Qdrant:**
```python
client.upsert(
    collection_name="documents",
    points=[
        PointStruct(
            id=1,
            vector=embedding,
            payload={
                "source": "report.pdf",
                "page": 5,
                "department": "finance",
                "date": datetime(2024, 1, 15)
            }
        )
    ]
)
```

**Pros:**
- Single query for retrieval + filtering
- No join overhead
- Simple architecture

**Cons:**
- Limited query capabilities
- Metadata duplication across chunks
- Schema changes require re-indexing

### Option 2: Separate Metadata Store

Use a relational database for metadata, vector store for embeddings:

```
┌─────────────────┐     ┌─────────────────┐
│  PostgreSQL     │     │   ChromaDB      │
├─────────────────┤     ├─────────────────┤
│ documents       │     │ chunks          │
│  - id           │←────│  - doc_id (FK)  │
│  - title        │     │  - embedding    │
│  - author       │     │  - chunk_text   │
│  - created_at   │     │  - page_num     │
│  - tags[]       │     └─────────────────┘
│  - metadata{}   │
└─────────────────┘
```

**Pros:**
- Rich querying (SQL)
- Single source of truth for document metadata
- Easy schema evolution

**Cons:**
- Two-phase retrieval (filter → retrieve, or retrieve → filter)
- More complex architecture

### Option 3: Hybrid with Self-Querying Retriever

Use LLM to automatically extract filters from natural language:

```python
# User query: "Show me finance reports from Q3 2024"
# Self-query extracts:
#   - semantic: "finance reports"
#   - filter: department == "finance" AND date >= 2024-07-01 AND date <= 2024-09-30

from langchain.retrievers.self_query.base import SelfQueryRetriever

metadata_field_info = [
    AttributeInfo(name="department", description="Department that created the document", type="string"),
    AttributeInfo(name="date", description="Document creation date", type="date"),
    AttributeInfo(name="type", description="Document type", type="string", enum=["report", "memo", "contract"])
]

retriever = SelfQueryRetriever.from_llm(
    llm=llm,
    vectorstore=vectorstore,
    document_content_description="Company documents",
    metadata_field_info=metadata_field_info
)
```

**Source:** [LangChain Self-Query](https://python.langchain.com/docs/modules/data_connection/retrievers/self_query/), [LlamaIndex Auto-Retrieval](https://docs.llamaindex.ai/en/stable/examples/query_engine/pdf_tables/recursive_retriever/)

---

## Metadata Standards

### Dublin Core (ISO 15836)

The most widely adopted standard for document metadata:

| Element | Description | Example |
|---------|-------------|---------|
| dc:title | Resource name | "Q3 2024 Financial Report" |
| dc:creator | Primary author | "Jane Smith" |
| dc:subject | Topic keywords | "finance, quarterly, revenue" |
| dc:description | Summary | "Analysis of Q3 performance..." |
| dc:date | Creation/publication date | "2024-10-15" |
| dc:type | Resource type | "Report" |
| dc:format | File format | "application/pdf" |
| dc:identifier | Unique identifier | "DOC-2024-001" |
| dc:source | Derived from | "Annual Report 2023" |
| dc:language | Language | "en" |

**Why Dublin Core for ragd:**
- International standard (ISO, IETF, NISO)
- Interoperable with other systems
- Well-defined semantics
- Extensible

**Source:** [Dublin Core Wikipedia](https://en.wikipedia.org/wiki/Dublin_Core), [UCSC Library Guide](https://guides.library.ucsc.edu/c.php?g=618773&p=4306386)

### XMP (Extensible Metadata Platform)

Adobe's standard for embedding metadata in PDF/images:

- **Dublin Core Schema** - general metadata
- **XMP Basic Schema** - file-level metadata (dates, tools)
- **Rights Management Schema** - copyright, usage rights
- **PDF Schema** - PDF-specific properties

**Source:** [PDF/A Metadata Guide](https://pdfa.org/wp-content/until2016_uploads/2011/08/pdfa_metadata-2b.pdf)

### Custom Schema for RAG

Extend Dublin Core with RAG-specific fields:

```python
RAGD_METADATA_SCHEMA = {
    # Dublin Core fields
    "dc:title": str,
    "dc:creator": list[str],
    "dc:subject": list[str],
    "dc:description": str,
    "dc:date": datetime,
    "dc:type": str,
    "dc:identifier": str,

    # RAG-specific fields
    "ragd:chunk_count": int,
    "ragd:embedding_model": str,
    "ragd:ingestion_date": datetime,
    "ragd:source_hash": str,  # For deduplication
    "ragd:quality_score": float,  # PDF quality assessment

    # User-defined tags
    "ragd:tags": list[str],
    "ragd:project": str,
    "ragd:sensitivity": str,  # public, internal, confidential
}
```

---

## Provenance and Traceability

### The Citation Challenge

From the [ACM RAG Citation Study](https://dl.acm.org/doi/10.1145/3703412.3703431):

> "The complexity lies in re-constructing the document and identifying a page after the document has been pre-processed and split into chunks. PDFs are converted to text files during chunking, causing a change in formatting and loss of metadata."

### Solutions for Citation Traceability

**1. Chunk ID → Document → Page Mapping:**

```python
@dataclass
class ChunkMetadata:
    chunk_id: str
    document_id: str
    source_path: str
    page_numbers: list[int]  # May span multiple pages
    section_heading: str
    char_start: int
    char_end: int

@dataclass
class Citation:
    document_title: str
    author: str
    page: int
    section: str
    retrieval_score: float
```

**2. TF-IDF Reverse Search:**

When page numbers are lost, use TF-IDF to match chunks back to source pages:

```python
# Index original pages with TF-IDF
page_tfidf = TfidfVectorizer().fit_transform(original_pages)

# For each chunk, find most similar page
chunk_tfidf = vectorizer.transform([chunk_text])
similarities = cosine_similarity(chunk_tfidf, page_tfidf)
most_likely_page = similarities.argmax()
```

**3. W3C PROV-O for Full Provenance:**

The [PROV Ontology](https://www.w3.org/TR/prov-o/) provides a standard for tracking data lineage:

```
┌─────────────────┐
│ Entity          │  Document, Chunk, Embedding
├─────────────────┤
│ Activity        │  Ingestion, Chunking, Embedding
├─────────────────┤
│ Agent           │  User, System, Model
└─────────────────┘

Relationships:
- wasGeneratedBy (chunk → chunking activity)
- wasDerivedFrom (chunk → document)
- wasAttributedTo (document → author)
- used (embedding activity → chunk)
```

**Source:** [W3C PROV-O](https://www.w3.org/TR/prov-o/)

### Provenance Schema for ragd

```python
@dataclass
class DocumentProvenance:
    # Source tracking
    original_path: str
    original_hash: str  # SHA-256 of original file
    ingestion_timestamp: datetime

    # Processing history
    processing_steps: list[ProcessingStep]
    # e.g., [("pdf_extract", "pymupdf"), ("chunk", "sentence_splitter"), ("embed", "voyage-3")]

    # Derivation chain
    derived_from: Optional[str]  # Parent document ID
    supersedes: Optional[str]  # Previous version ID

    # Agent attribution
    ingested_by: str  # User or system
    last_modified_by: str

@dataclass
class ChunkProvenance:
    chunk_id: str
    document_id: str

    # Position in source
    page_numbers: list[int]
    char_offset_start: int
    char_offset_end: int

    # Embedding provenance
    embedding_model: str
    embedding_timestamp: datetime
    embedding_hash: str  # For cache invalidation
```

---

## Vector Database Filtering Comparison

| Database | Filter Types | Self-Query Support | Notes |
|----------|-------------|-------------------|-------|
| **ChromaDB** | `$eq`, `$ne`, `$gt`, `$gte`, `$lt`, `$lte`, `$in`, `$nin` | Via LangChain | No hybrid search natively |
| **Qdrant** | All comparison + geo, text match, nested | Via LangChain | Payload-aware HNSW traversal |
| **Weaviate** | Full filter DSL + BM25 | Native + LangChain | Strong hybrid search |
| **Pinecone** | Metadata filters | Via LangChain | Managed service |
| **Milvus** | Boolean, range, in-set | Via LangChain | Scalable |

**Source:** [Vector DB Comparison](https://github.com/avnlp/vectordb), [Airbyte Comparison](https://airbyte.com/data-engineering-resources/chroma-db-vs-qdrant)

### Recommended Pattern: Multi-Stage Retrieval

```
Query: "Show me Q3 finance reports about revenue growth"
                ↓
┌─────────────────────────────────────────────────────┐
│ Stage 1: Metadata Filter                            │
│   department = "finance" AND                        │
│   date >= 2024-07-01 AND date <= 2024-09-30         │
└─────────────────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────────────────┐
│ Stage 2: Semantic Search                            │
│   Query: "revenue growth"                           │
│   On: filtered document subset                      │
└─────────────────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────────────────┐
│ Stage 3: Rerank (optional)                          │
│   Cross-encoder on top-k results                    │
└─────────────────────────────────────────────────────┘
```

---

## Recommended Architecture for ragd

### Metadata Pipeline

```
Document Input
    ↓
┌─────────────────────────────────────────────────────┐
│ Stage 1: Algorithmic Extraction (always)            │
│   - PDF properties (title, author, dates)           │
│   - File metadata (path, size, hash)                │
│   - Language detection                              │
│   - KeyBERT keywords                                │
│   - spaCy NER entities                              │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Stage 2: LLM Enhancement (optional, configurable)   │
│   - Document summary                                │
│   - Document type classification                    │
│   - Questions each chunk answers                    │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Stage 3: User Enrichment                            │
│   - Manual tags                                     │
│   - Project assignment                              │
│   - Sensitivity classification                      │
└─────────────────────────────────────────────────────┘
    ↓
Storage (SQLite/PostgreSQL + ChromaDB)
```

### Proposed v0.2 Features (UC-005: Manage Metadata)

| Feature ID | Name | Description |
|------------|------|-------------|
| F-024 | Metadata Schema | Dublin Core + RAG extensions |
| F-025 | Automatic Extraction | KeyBERT keywords, spaCy NER, PDF properties |
| F-026 | LLM Enrichment | Optional summary/classification via LLM |
| F-027 | Tag Management | User-defined tags, bulk operations |
| F-028 | Provenance Tracking | Source hash, processing history, derivation |

### Proposed v0.2 Features (UC-006: Export & Backup)

| Feature ID | Name | Description |
|------------|------|-------------|
| F-029 | Metadata Export | Export metadata to JSON/CSV |
| F-030 | Full Backup | Database + vectors + metadata archive |
| F-031 | Selective Restore | Restore by tag/project/date |

---

## Key Takeaways

1. **Metadata enables precision retrieval.** Self-querying retrievers that extract filters from natural language queries dramatically improve relevance.

2. **Use Dublin Core as your base.** It's an ISO standard, extensible, and interoperable with other systems.

3. **Preserve chunk-to-document-to-page mapping.** This is essential for citation and traceability. Store page numbers and character offsets at chunk creation time.

4. **Hybrid extraction is cost-effective.** Use algorithmic methods (KeyBERT, spaCy) for all documents, LLM extraction for high-value documents.

5. **Consider provenance from day one.** Store hashes, timestamps, and processing history. You can't add provenance retroactively.

6. **ChromaDB supports rich filtering.** Despite not having native hybrid search, its metadata filtering is sufficient for ragd v0.2.

---

## References

### Documentation & Guides
- [LlamaIndex Metadata Extraction](https://docs.llamaindex.ai/en/stable/module_guides/indexing/metadata_extraction/)
- [LangChain Self-Query Retriever](https://python.langchain.com/docs/modules/data_connection/retrievers/self_query/)
- [Unstructured: Metadata in RAG](https://unstructured.io/insights/how-to-use-metadata-in-rag-for-better-contextual-results)
- [Haystack Metadata Enrichment](https://haystack.deepset.ai/cookbook/metadata_enrichment)

### Tools & Libraries
- [KeyBERT](https://github.com/MaartenGr/KeyBERT) - Keyword extraction
- [spaCy](https://spacy.io/) - NER and NLP
- [LlamaIndex MetadataExtractors](https://docs.llamaindex.ai/en/stable/module_guides/indexing/metadata_extraction/)

### Standards
- [Dublin Core (ISO 15836)](https://en.wikipedia.org/wiki/Dublin_Core)
- [W3C PROV-O](https://www.w3.org/TR/prov-o/) - Provenance ontology
- [XMP (ISO 16684)](https://pdfa.org/wp-content/until2016_uploads/2011/08/pdfa_metadata-2b.pdf) - PDF metadata

### Research
- [RAG Citation & Provenance (ACM)](https://dl.acm.org/doi/10.1145/3703412.3703431)
- [CiteFix: Citation Correction](https://arxiv.org/html/2504.15629v2)
- [Voyage-context-3 Model](https://www.mongodb.com/company/blog/product-release-announcements/voyage-context-3-focused-chunk-level-details-global-document-context)

---

## Related Documentation

- [State-of-the-Art RAG](./state-of-the-art-rag.md) - Advanced retrieval techniques
- [State-of-the-Art PDF Processing](./state-of-the-art-pdf-processing.md) - Document extraction
- [Citation Systems Research](./citation-systems.md) - Citation formats and output
- [UC-005: Manage Metadata](../../use-cases/briefs/UC-005-manage-metadata.md) - Use case brief

---

**Status**: Research complete, ready for v0.2 feature specification

