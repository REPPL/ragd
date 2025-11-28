# ADR-0023: Metadata Schema Evolution

## Status

Accepted

## Context

v0.2.0 introduces comprehensive document metadata based on Dublin Core (F-029: Metadata Storage). This creates a schema evolution challenge:

1. **v0.1.0 documents** have minimal metadata (source path, hash, page count)
2. **v0.2.0 documents** will have full Dublin Core metadata plus RAG extensions
3. Users upgrading from v0.1.0 need their existing documents to work

The challenge is handling documents indexed before the schema change without requiring full re-indexing (which could be slow for large knowledge bases).

### Requirements

1. Existing v0.1.0 knowledge bases must continue to work
2. New metadata fields should have sensible defaults
3. Users should be able to enrich metadata for old documents
4. Schema changes should be forward-compatible for future versions

## Decision

Implement **lazy migration with schema versioning**:

### 1. Schema Version Field

Add `ragd_schema_version` to all document metadata:

```python
@dataclass
class DocumentMetadata:
    """Dublin Core-based metadata with RAG extensions."""

    # Schema version for migration handling
    ragd_schema_version: str = "2.0"  # v0.2.0 schema

    # Dublin Core fields
    dc_title: str = ""
    dc_creator: list[str] = field(default_factory=list)
    dc_subject: list[str] = field(default_factory=list)
    dc_description: str = ""
    dc_date: datetime | None = None
    dc_type: str = ""
    dc_format: str = ""
    dc_identifier: str = ""
    dc_language: str = "en"

    # RAG extensions
    ragd_source_path: str = ""
    ragd_source_hash: str = ""
    ragd_chunk_count: int = 0
    ragd_ingestion_date: datetime | None = None
    ragd_quality_score: float = 0.0
    ragd_tags: list[str] = field(default_factory=list)
    ragd_project: str = ""
```

### 2. Migration Strategy

**Lazy migration**: Documents are migrated on first access, not at startup.

```python
def get_document_metadata(doc_id: str) -> DocumentMetadata:
    """Get metadata, migrating from old schema if needed."""
    raw = storage.get_raw_metadata(doc_id)

    if raw is None:
        return None

    schema_version = raw.get("ragd_schema_version", "1.0")

    if schema_version == "1.0":
        # Migrate v0.1.0 → v0.2.0
        metadata = migrate_v1_to_v2(raw)
        storage.update_metadata(doc_id, metadata)
        return metadata

    return DocumentMetadata(**raw)

def migrate_v1_to_v2(v1_data: dict) -> DocumentMetadata:
    """Migrate v0.1.0 metadata to v0.2.0 schema."""
    return DocumentMetadata(
        ragd_schema_version="2.0",

        # Carry over existing fields
        ragd_source_path=v1_data.get("source_path", ""),
        ragd_source_hash=v1_data.get("content_hash", ""),
        ragd_chunk_count=v1_data.get("chunk_count", 0),
        ragd_ingestion_date=v1_data.get("indexed_at"),

        # Set defaults for new fields
        dc_title=Path(v1_data.get("source_path", "")).stem,
        dc_format=v1_data.get("file_type", ""),
        dc_language="en",  # Default, can be detected later

        # Leave optional fields empty
        dc_creator=[],
        dc_subject=[],
        dc_description="",
        dc_date=None,
        dc_type="",
        dc_identifier="",
        ragd_quality_score=0.0,
        ragd_tags=[],
        ragd_project="",
    )
```

### 3. Batch Migration Command

For users who want to migrate all documents upfront:

```bash
ragd meta migrate
```

This runs migration on all documents and optionally triggers metadata extraction:

```bash
ragd meta migrate --extract  # Also run KeyBERT/spaCy on migrated docs
```

### 4. Forward Compatibility

All new fields have defaults, so future schema changes can add fields without breaking existing documents.

```python
# Future v0.3.0 field
ragd_sensitivity: str = "internal"  # Default for existing docs
```

### 5. Storage Implementation

Metadata stored in separate SQLite database alongside ChromaDB:

```
~/.ragd/
├── chromadb/           # Vector storage
├── metadata.sqlite     # Dublin Core metadata (NEW)
└── config.yaml
```

**Why SQLite?**
- ChromaDB metadata has size limits
- SQLite supports complex queries (date ranges, full-text search)
- Easy to export/backup
- No additional dependencies (Python stdlib)

## Consequences

### Positive

- **No forced migration**: Existing knowledge bases work immediately
- **Gradual enrichment**: Users can enhance metadata over time
- **Performance**: Only migrate documents when accessed
- **Future-proof**: Schema versioning handles future changes

### Negative

- **Mixed state**: Some documents may have v1 schema until accessed
- **Storage overhead**: Separate SQLite database adds complexity
- **Migration during access**: First access to old documents slightly slower

### Mitigation

- Provide `ragd meta migrate` for users who want upfront migration
- Background migration option: `ragd meta migrate --background`
- Clear documentation of schema evolution behaviour

## Alternatives Considered

### 1. Force Migration on Upgrade

**Rejected**: Would require re-processing all documents, potentially taking hours for large knowledge bases. Users might avoid upgrading.

### 2. Store in ChromaDB Metadata

**Rejected**: ChromaDB metadata has size limits and doesn't support complex queries. Dublin Core can have multiple authors, long descriptions, etc.

### 3. Re-index All Documents

**Rejected**: Loses document modifications (tags, manual metadata edits) and is extremely slow.

## Implementation

### Phase 1: Schema Definition

```python
# src/ragd/metadata/models.py
@dataclass
class DocumentMetadata:
    # ... as defined above
```

### Phase 2: Storage Layer

```python
# src/ragd/metadata/store.py
class MetadataStore:
    def __init__(self, db_path: Path):
        self._conn = sqlite3.connect(db_path)
        self._init_schema()

    def get(self, doc_id: str) -> DocumentMetadata | None:
        # Lazy migration logic
        ...

    def set(self, doc_id: str, metadata: DocumentMetadata) -> None:
        ...

    def query(self, **filters) -> list[DocumentMetadata]:
        ...
```

### Phase 3: Migration Commands

```bash
ragd meta migrate           # Migrate all documents
ragd meta migrate --extract # Migrate + extract keywords/entities
ragd meta migrate --status  # Show migration progress
```

## Related Documentation

- [F-029: Metadata Storage](../../features/completed/F-029-metadata-storage.md)
- [F-030: Metadata Extraction](../../features/completed/F-030-metadata-extraction.md)
- [State-of-the-Art Metadata](../../research/state-of-the-art-metadata.md)
- [Dublin Core Standard](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/)

---

**Status**: Accepted
