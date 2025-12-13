# F-130: NER Pipeline Integration

## Overview

**Research**: [State-of-the-Art NER Indexing](../../research/state-of-the-art-ner-indexing.md)
**Milestone**: [v1.1.0](../../milestones/v1.1.0.md)
**Priority**: P1 (High)

## Problem Statement

ragd has entity extraction capabilities (spaCy, pattern-based) and a knowledge graph (SQLite-backed), but these are **not integrated into the indexing pipeline**. Users must manually call extraction after indexing.

**Current State:**
```
ragd add document.pdf
    ↓
[Extract → Chunk → Embed → Store]
    ↓
Document indexed (no entities extracted)
Knowledge graph remains empty
```

**Desired State:**
```
ragd add document.pdf
    ↓
[Extract → Chunk → Extract Entities → Embed → Store]
    ↓
Document indexed with entities
Knowledge graph populated
```

### Impact

Without pipeline integration:
- Knowledge graph (F-022) remains empty after normal usage
- Entity-based filtering unavailable
- Metadata extraction (F-030) not utilised
- Users unaware entities exist as a feature

## Design Approach

### Integration Point

Add entity extraction as step 11 in `index_document()`:

```python
def index_document(
    path: Path,
    store: VectorStore,
    config: RagdConfig,
) -> IndexResult:
    # Steps 1-10: existing pipeline...

    # Step 11: Entity extraction (NEW)
    if config.entity_extraction.enabled:
        entities_by_chunk = extract_entities_for_chunks(
            chunks,
            config.entity_extraction,
        )

        # Add entities to chunk metadata
        for chunk, entities in zip(chunks, entities_by_chunk):
            chunk.metadata["entities"] = [e.text for e in entities]
            chunk.metadata["entity_types"] = {
                e.text: e.type for e in entities
            }

        # Step 12: Knowledge graph population (NEW)
        if config.knowledge_graph.enabled:
            graph = KnowledgeGraph(config.knowledge_graph.db_path)
            for chunk, entities in zip(chunks, entities_by_chunk):
                graph.add_entities_batch(entities, doc_id, chunk.id)

    # Steps 13+: existing storage...
```

### Configuration

```yaml
# ~/.ragd/config.yaml
entity_extraction:
  enabled: true
  mode: sync  # sync | async | disabled

  # Tier 1: Pattern-based (always, fast)
  pattern:
    enabled: true

  # Tier 2: spaCy (standard entities)
  spacy:
    enabled: true
    model: "en_core_web_sm"

  # Tier 3: GLiNER (custom types, optional)
  gliner:
    enabled: false
    model: "urchade/gliner_medium-v2.1"
    custom_types: []

  # Performance
  batch_size: 50

knowledge_graph:
  enabled: true
  auto_build: true  # Build during indexing
  db_path: "~/.ragd/graph.db"
```

### CLI Integration

```bash
# Default: entities extracted (configurable)
ragd add document.pdf

# Explicitly disable entity extraction
ragd add document.pdf --no-entities

# Extract custom entity types (requires GLiNER)
ragd add document.pdf --entity-types "TECHNOLOGY,CONCEPT"

# Re-extract entities for existing documents
ragd entities rebuild

# Check entity extraction status
ragd status
# → Documents: 150
# → With entities: 150 ✓
# → Knowledge graph: 1,234 entities, 567 relationships
```

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   index_document()                          │
├─────────────────────────────────────────────────────────────┤
│  1. Extract text                                            │
│  2. OCR fallback                                            │
│  3. Normalise text                                          │
│  4. Check duplicates                                        │
│  5. Chunk text                                              │
│  6. Generate embeddings                                     │
│  7. Extract PDF metadata                                    │
├─────────────────────────────────────────────────────────────┤
│  8. Extract entities (NEW)                                  │
│     ├─ Tier 1: Pattern-based (regex)                       │
│     ├─ Tier 2: spaCy NER                                   │
│     └─ Tier 3: GLiNER (if custom types)                    │
│  9. Populate knowledge graph (NEW)                          │
├─────────────────────────────────────────────────────────────┤
│  10. Store in ChromaDB                                      │
│  11. Add to BM25 index                                      │
│  12. Extract images (if PDF)                                │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Tasks

### Phase 1: Basic Integration

- [ ] Add `entity_extraction` section to `RagdConfig`
- [ ] Add `knowledge_graph.auto_build` config option
- [ ] Import entity extractor in `pipeline.py`
- [ ] Call `get_entity_extractor()` after chunking
- [ ] Store entities in chunk metadata
- [ ] Call `graph.add_entities_batch()` if graph enabled
- [ ] Add `--no-entities` flag to `ragd add`

### Phase 2: Performance

- [ ] Implement batch extraction with `nlp.pipe()`
- [ ] Add progress bar for entity extraction
- [ ] Skip extraction for already-processed chunks (incremental)
- [ ] Lazy-load NER models (only when first document processed)

### Phase 3: CLI Enhancements

- [ ] Add `ragd entities rebuild` command
- [ ] Add entity stats to `ragd status`
- [ ] Add `--entity-types` flag for custom types
- [ ] Show entity count in `ragd list` output

## Success Criteria

- [ ] `ragd add` extracts entities by default
- [ ] Knowledge graph populated during normal usage
- [ ] Entity extraction adds <2s per document (small model)
- [ ] Users can disable with `--no-entities` or config
- [ ] Existing tests pass with entity extraction enabled
- [ ] Entity count visible in `ragd status`

## Dependencies

- Existing: `src/ragd/knowledge/entities.py`
- Existing: `src/ragd/knowledge/graph.py`
- Optional: spaCy (for Tier 2)
- Optional: GLiNER (for Tier 3, F-128)

## Performance Budget

| Document Size | Entity Extraction | Total Index Time |
|---------------|-------------------|------------------|
| 1 page | <500ms | <3s |
| 10 pages | <2s | <10s |
| 100 pages | <15s | <60s |

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Increased indexing time | Configurable, can disable |
| spaCy model not installed | Graceful fallback to pattern-only |
| Memory pressure | Lazy model loading |
| Existing documents lack entities | Provide `rebuild` command |

---

## Related Documentation

- [State-of-the-Art NER Indexing](../../research/state-of-the-art-ner-indexing.md) - Research context
- [F-022: Knowledge Graph Integration](../completed/F-022-knowledge-graph.md) - Graph storage
- [F-030: Metadata Extraction](../completed/F-030-metadata-extraction.md) - Metadata pipeline
- [F-128: GLiNER NER](./F-128-gliner-ner.md) - Zero-shot extraction
- [NLP Library Integration](../../research/nlp-library-integration.md) - spaCy patterns

---

**Status**: Planned
