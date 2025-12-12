# F-029: Metadata Storage

## Overview

**Use Case**: [UC-005](../../../use-cases/briefs/UC-005-manage-metadata.md)
**Milestone**: v0.2
**Priority**: P0

## Problem Statement

Document metadata (title, author, tags, dates) is essential for filtering, citation, and organisation. Without structured metadata storage, users cannot filter searches, trace citations to sources, or organise their knowledge base by project or topic.

## Design Approach

Implement a Dublin Core-based metadata schema with RAG-specific extensions, stored alongside the vector database.

**Schema Design:**

```python
@dataclass
class DocumentMetadata:
    # Dublin Core fields (ISO 15836)
    dc_title: str                    # Document title
    dc_creator: list[str]            # Author(s)
    dc_subject: list[str]            # Keywords/topics
    dc_description: str              # Summary
    dc_date: datetime                # Creation/publication date
    dc_type: str                     # Document type (report, memo, etc.)
    dc_format: str                   # MIME type
    dc_identifier: str               # Unique ID
    dc_language: str                 # ISO language code

    # RAG-specific extensions
    ragd_source_path: str            # Original file path
    ragd_source_hash: str            # SHA-256 for deduplication
    ragd_chunk_count: int            # Number of chunks
    ragd_embedding_model: str        # Model used for embeddings
    ragd_ingestion_date: datetime    # When indexed
    ragd_quality_score: float        # PDF quality assessment

    # User-defined
    ragd_tags: list[str]             # User tags
    ragd_project: str                # Project assignment
    ragd_sensitivity: str            # public/internal/confidential
```

**Storage Architecture:**
```
┌─────────────────┐     ┌─────────────────┐
│  SQLite/JSON    │     │   ChromaDB      │
├─────────────────┤     ├─────────────────┤
│ documents       │     │ chunks          │
│  - id           │←────│  - doc_id (FK)  │
│  - metadata     │     │  - embedding    │
│  - created_at   │     │  - chunk_meta   │
└─────────────────┘     └─────────────────┘
```

## Implementation Tasks

- [ ] Define Pydantic models for document and chunk metadata
- [ ] Create SQLite schema for document metadata storage
- [ ] Implement CRUD operations for metadata
- [ ] Add metadata to ChromaDB chunk payloads
- [ ] Implement Dublin Core field validation
- [ ] Create metadata migration utilities
- [ ] Add indexing for common query patterns (date, tags, project)

## Success Criteria

- [ ] All indexed documents have structured metadata
- [ ] Metadata queryable via CLI (`ragd meta show <id>`)
- [ ] Dublin Core compliance for core fields
- [ ] Sub-100ms metadata queries
- [ ] Schema versioning for future migrations

## Dependencies

- [F-001: Document Ingestion](./F-001-document-ingestion.md) - Triggers metadata creation
- SQLite (bundled with Python)

## Technical Notes

**Why Dublin Core:**
- International standard (ISO 15836, IETF, NISO)
- Interoperable with other systems
- Well-defined semantics
- Extensible with custom namespaces

**ChromaDB Metadata Integration:**
```python
collection.add(
    documents=[chunk_text],
    embeddings=[embedding],
    metadatas=[{
        "doc_id": document.id,
        "page": 5,
        "section": "Introduction",
        "dc_title": document.dc_title,
        "dc_date": document.dc_date.isoformat(),
    }],
    ids=[chunk_id]
)
```

**Filtering Example:**
```python
results = collection.query(
    query_texts=["revenue growth"],
    where={
        "$and": [
            {"dc_date": {"$gte": "2024-01-01"}},
            {"ragd_project": "Q1-analysis"}
        ]
    }
)
```

## Related Documentation

- [State-of-the-Art Metadata](../../research/state-of-the-art-metadata.md)
- [Dublin Core Wikipedia](https://en.wikipedia.org/wiki/Dublin_Core)
- [F-030: Metadata Extraction](./F-030-metadata-extraction.md)

