# State-of-the-Art: NER Integration with Document Indexing

> **Research Date:** December 2024
>
> This document examines best practices for integrating Named Entity Recognition (NER) into document indexing pipelines. The key question: **when** should entities be extracted—during indexing, post-indexing, or at query time?

## Executive Summary

**Key Finding:** Industry best practice is **index-time entity extraction**—entities should be extracted during document ingestion and stored as metadata, not computed at query time.

**ragd Status:** The roadmap specifies index-time extraction (F-022, F-030, F-100), but the current implementation has a **design-implementation gap**: entity extraction exists as a separate system not called during the indexing pipeline.

**Recommendation:** Integrate NER into `index_document()` as an optional, configurable step with async support for performance.

---

## Part 1: The Timing Question

### When to Extract Entities?

| Timing | Pros | Cons | Best For |
|--------|------|------|----------|
| **Index-time** | Fast queries, pre-computed, enables filtering | Slower ingestion, storage overhead | Production RAG systems |
| **Query-time** | Fresh extraction, no storage | High latency, repeated computation | Exploratory/ad-hoc analysis |
| **Hybrid** | Flexible, fresh for new types | Complexity | Evolving entity schemas |
| **Async/Background** | Non-blocking ingestion | Eventual consistency | High-throughput systems |

### Industry Consensus: Index-Time Extraction

Research and production systems overwhelmingly favour **index-time extraction**:

> "In your preprocessing pipeline, you can include a component that uses a small language model to identify named entities and store them as metadata along with your text. These named entities can then be used as a filter at query time."
> — [Elasticsearch Labs: Advanced RAG Techniques (2024)](https://www.elastic.co/search-labs/blog/advanced-rag-techniques-part-1)

> "Tag during ingestion: Enrich metadata at index time, not query time."
> — State-of-the-Art Topic Extraction (ragd research)

> "During indexing, documents are processed to extract entities and their relations, which are then stored as nodes and edges in a knowledge graph."
> — [GraphRAG Architecture (2024)](https://medium.com/@zilliz_learn/graphrag-explained-enhancing-rag-with-knowledge-graphs-3312065f99e1)

### Why Index-Time Wins

1. **Query Latency**: Pre-extracted entities enable sub-100ms filtering vs seconds for runtime NER
2. **Consistency**: Same entity set for all queries on a document
3. **Filtering**: Enables `--entity-type PERSON` style CLI filters
4. **Knowledge Graphs**: Entities must exist before relationship detection
5. **Composite Embeddings**: Entity metadata can be weighted into embeddings (typically 5%)

---

## Part 2: Architecture Patterns

### Pattern 1: Synchronous Pipeline Integration

Entities extracted as a step in the main indexing pipeline.

```
Document → Extract Text → Chunk → Extract Entities → Embed → Store
                                       ↓
                              Entity Storage (SQLite)
```

**Pros:**
- Simple, predictable
- Entities available immediately after indexing
- Single pipeline to maintain

**Cons:**
- Increases indexing latency
- Blocking on NER model loading

**When to Use:** Small to medium corpora (<10,000 documents)

### Pattern 2: Async/Background Extraction

Entities extracted in a background job after initial indexing.

```
Document → Extract Text → Chunk → Embed → Store
                ↓ (async)
        Background Worker → Extract Entities → Update Metadata
```

**Pros:**
- Non-blocking ingestion
- User sees document immediately
- Can retry failed extractions

**Cons:**
- Eventual consistency (entities not immediately queryable)
- Additional infrastructure (job queue)

**When to Use:** High-throughput systems, large document batches

**Source:** [LlamaIndex Async Ingestion Pipeline](https://docs.llamaindex.ai/en/stable/examples/ingestion/async_ingestion_pipeline/)

### Pattern 3: Tiered Extraction

Fast extraction first, expensive extraction deferred.

```
Document → Extract Text → Chunk → Tier 1 (Pattern/Fast) → Embed → Store
                                          ↓ (async)
                           Tier 2 (spaCy) → Tier 3 (GLiNER) → Update
```

**Pros:**
- Fast initial indexing with basic entities
- Rich entities added incrementally
- Cost-effective (skip expensive NER if not needed)

**Cons:**
- Multiple passes over documents
- Entity set evolves over time

**When to Use:** When fast ingestion matters but rich entities eventually needed

### Pattern 4: GraphRAG-Style Entity-Centric Indexing

Entities are first-class citizens, not just metadata.

```
Document → Extract Text → Chunk → Extract Entities → Build Entity Graph
                                          ↓
                              Community Detection (Leiden)
                                          ↓
                              Community Summaries (LLM)
                                          ↓
                              Dual Index (Vector + Graph)
```

**Pros:**
- Enables multi-hop reasoning
- Corpus-wide entity understanding
- Powerful for relationship queries

**Cons:**
- High computational cost (LLM for summaries)
- Complex infrastructure
- Granularity dilemma (entity-level vs document-level)

**When to Use:** Complex QA, research, investigative analysis

**Source:** [Microsoft GraphRAG](https://microsoft.github.io/graphrag/), [deepset GraphRAG](https://www.deepset.ai/blog/graph-rag)

---

## Part 3: Entity Storage Strategies

### Strategy 1: Inline Metadata (Recommended for ragd)

Store entities as document/chunk metadata in the vector store.

```python
collection.add(
    documents=["chunk text"],
    embeddings=[embedding],
    metadatas=[{
        "source": "report.pdf",
        "entities": ["Apple Inc.", "Tim Cook", "Cupertino"],
        "entity_types": {"Apple Inc.": "ORG", "Tim Cook": "PERSON"},
    }],
    ids=["chunk_001"]
)
```

**Pros:** Single query for retrieval + filtering, simple architecture
**Cons:** Limited query flexibility, entity duplication across chunks

### Strategy 2: Separate Entity Store

Dedicated entity table with document references.

```sql
-- Entity table
CREATE TABLE entities (
    name TEXT PRIMARY KEY,
    type TEXT,
    doc_count INTEGER,
    chunk_count INTEGER
);

-- Mentions table (linking entities to locations)
CREATE TABLE entity_mentions (
    entity_name TEXT,
    doc_id TEXT,
    chunk_id TEXT,
    position_start INTEGER,
    position_end INTEGER
);
```

**Pros:** Rich entity queries, normalisation, relationship storage
**Cons:** Two-phase retrieval, more complex

### Strategy 3: Composite Embeddings

Weight entity metadata into the embedding itself.

```python
# Elasticsearch approach
composite = (
    0.70 * embed(chunk_text) +
    0.25 * embed(keyphrases) +
    0.05 * embed(entities)
)
```

**Pros:** Semantic boost from entities, single embedding per chunk
**Cons:** Requires re-embedding if entities change

**Source:** [Elastic Labs (2024)](https://www.elastic.co/search-labs/blog/advanced-rag-techniques-part-1)

---

## Part 4: Performance Considerations

### NER Latency Benchmarks

| Method | Latency (per chunk) | Memory | Notes |
|--------|---------------------|--------|-------|
| Pattern-based (regex) | <1ms | Minimal | Always fast |
| spaCy (en_core_web_sm) | ~5-10ms | ~50MB | Good baseline |
| spaCy (en_core_web_trf) | ~50-100ms | ~400MB | Transformer-based |
| GLiNER (medium) | ~20-50ms | ~400MB | Zero-shot capability |
| LLM (GPT-4) | ~1-3s | API | Highest quality |

### Throughput Targets

| Scale | Documents | Target Ingestion | Approach |
|-------|-----------|------------------|----------|
| Personal | <1,000 | Minutes | Sync pipeline |
| Team | 1,000-10,000 | Hour | Sync with batching |
| Enterprise | 10,000-100,000 | Hours | Async workers |
| Large-scale | >100,000 | Continuous | Stream processing |

### Optimisation Techniques

1. **Batch Processing**: Use `nlp.pipe()` for 10-100x speedup
2. **Lazy Model Loading**: Load NER models only when enabled
3. **Caching**: Skip re-extraction for unchanged documents
4. **Incremental Extraction**: Only process new/modified documents
5. **Tier Skipping**: Skip expensive tiers if cheaper tier sufficient

**Source:** [OpenMetadata Incremental Extraction](https://docs.open-metadata.org/latest/connectors/ingestion/workflows/metadata/incremental-extraction)

---

## Part 5: Entity Resolution & Normalisation

### The Deduplication Problem

Raw NER produces duplicates and variants:
- "Apple", "Apple Inc.", "Apple Inc"
- "2024", "Year 2024"
- "IT", "Information Technology"

> "In the original GraphRAG, extracted named entities were directly used without deduplication, which could lead to issues... This challenge, known academically as Entity Resolution, typically involves complex algorithms."
> — [RAGFlow GraphRAG](https://ragflow.io/blog/ragflow-support-graphrag)

### Resolution Strategies

| Strategy | Complexity | Quality | Notes |
|----------|------------|---------|-------|
| Exact match | Low | Poor | Only catches identical strings |
| Lowercase + strip | Low | Fair | Basic normalisation |
| Fuzzy matching | Medium | Good | Levenshtein distance |
| Embedding similarity | Medium | Good | Semantic matching |
| LLM canonicalisation | High | Excellent | "Apple Inc" → "Apple Inc." |
| Knowledge base linking | High | Excellent | Link to Wikidata/DBpedia |

### Recommended Approach for ragd

```python
def normalise_entity(name: str, entity_type: str) -> str:
    """Basic entity normalisation."""
    # Lowercase and strip
    normalised = name.strip()

    # Remove common suffixes for organisations
    if entity_type == "ORG":
        for suffix in [" Inc.", " Inc", " Ltd.", " Ltd", " LLC"]:
            if normalised.endswith(suffix):
                normalised = normalised[:-len(suffix)]

    return normalised
```

---

## Part 6: ragd Gap Analysis

### Current State vs Best Practice

| Aspect | Best Practice | ragd Design | ragd Implementation |
|--------|---------------|-------------|---------------------|
| **Timing** | Index-time | Index-time (F-030) | ❌ Separate system |
| **Integration** | In pipeline | In pipeline | ❌ Not integrated |
| **Storage** | Metadata + Graph | SQLite graph | ✅ Implemented |
| **Configuration** | Configurable | Planned | ❌ No config options |
| **Async Support** | Optional | Not designed | ❌ Not implemented |

### The Gap

From exploration of `src/ragd/ingestion/pipeline.py`:

```python
def index_document(...):
    # 1. Extract text ✅
    # 2. OCR fallback ✅
    # 3. Normalise text ✅
    # 4. Check duplicates ✅
    # 5. Chunk text ✅
    # 6. Generate embeddings ✅
    # 7. Extract PDF metadata ✅
    # 8. Store in ChromaDB ✅
    # 9. Add to BM25 index ✅
    # 10. Extract images ✅
    # 11. Extract entities ❌ MISSING
    # 12. Build knowledge graph ❌ MISSING
```

### Recommended Integration

Add entity extraction as step 11 in `index_document()`:

```python
def index_document(
    path: Path,
    store: VectorStore,
    config: RagdConfig,
    # New parameters
    extract_entities: bool = True,
    entity_types: list[str] | None = None,
) -> IndexResult:
    # ... existing steps 1-10 ...

    # Step 11: Entity extraction (if enabled)
    if extract_entities and config.entity_extraction.enabled:
        extractor = get_entity_extractor(
            prefer_spacy=config.entity_extraction.use_spacy,
            use_gliner=bool(entity_types),
            custom_types=entity_types,
        )

        for chunk in chunks:
            entities = extractor.extract(chunk.text)
            chunk.metadata["entities"] = [e.text for e in entities]
            chunk.metadata["entity_types"] = {e.text: e.type for e in entities}

            # Step 12: Add to knowledge graph
            if config.knowledge_graph.enabled:
                graph.add_entities_batch(entities, doc_id, chunk.id)

    # ... existing storage steps ...
```

---

## Part 7: Configuration Recommendation

Add entity extraction configuration to `RagdConfig`:

```yaml
# ~/.ragd/config.yaml
entity_extraction:
  enabled: true

  # Extraction timing
  mode: sync  # sync | async | disabled

  # Extractors to use
  extractors:
    pattern: true      # Always fast, no dependencies
    spacy: true        # Standard entity types
    gliner: false      # Custom types (requires gliner)

  # Default entity types (spaCy)
  default_types:
    - PERSON
    - ORG
    - GPE
    - DATE

  # Custom entity types (GLiNER)
  custom_types: []
    # - TECHNOLOGY
    # - CONCEPT

  # Performance tuning
  batch_size: 50
  timeout_seconds: 30

  # Entity normalisation
  normalise: true
  deduplicate: true

knowledge_graph:
  enabled: true
  auto_build: true  # Build graph during indexing
  cooccurrence_window: 3
```

---

## Part 8: Implementation Roadmap

### Phase 1: Basic Integration (Priority: High)

**Goal:** Call existing entity extractors during indexing

- [ ] Add `entity_extraction` config section to `RagdConfig`
- [ ] Call `get_entity_extractor()` in `index_document()`
- [ ] Store entities in chunk metadata
- [ ] Populate knowledge graph during indexing
- [ ] Add `--extract-entities` flag to `ragd add`

**Estimated Effort:** 1-2 days

### Phase 2: Performance Optimisation

**Goal:** Handle large document sets efficiently

- [ ] Implement batch processing with `nlp.pipe()`
- [ ] Add async extraction mode
- [ ] Skip unchanged documents (incremental)
- [ ] Cache entity models across documents

**Estimated Effort:** 2-3 days

### Phase 3: Entity Quality

**Goal:** Improve entity accuracy and usefulness

- [ ] Implement entity normalisation
- [ ] Add deduplication logic
- [ ] Integrate GLiNER for custom types (F-100)
- [ ] Add entity linking (optional)

**Estimated Effort:** 3-5 days

---

## References

### Industry Resources

- [Elasticsearch Labs: Advanced RAG Techniques (2024)](https://www.elastic.co/search-labs/blog/advanced-rag-techniques-part-1)
- [LlamaIndex Async Ingestion Pipeline](https://docs.llamaindex.ai/en/stable/examples/ingestion/async_ingestion_pipeline/)
- [deepset: GraphRAG](https://www.deepset.ai/blog/graph-rag)
- [Microsoft GraphRAG](https://microsoft.github.io/graphrag/)
- [RAGFlow GraphRAG Support](https://ragflow.io/blog/ragflow-support-graphrag)

### Research Papers

- [GraphRAG: Unlocking LLM Discovery (Edge et al., 2024)](https://arxiv.org/abs/2404.16130)
- [MES-RAG: Entity-Storage RAG](https://arxiv.org/abs/2503.13563)
- [Query-Centric Graph RAG](https://arxiv.org/abs/2509.21237)

### ragd Documentation

- [State-of-the-Art NER](./state-of-the-art-ner.md) - NER techniques
- [State-of-the-Art Knowledge Graphs](./state-of-the-art-knowledge-graphs.md) - Graph construction
- [F-022: Knowledge Graph Integration](../features/completed/F-022-knowledge-graph.md) - Feature spec
- [F-030: Metadata Extraction](../features/completed/F-030-metadata-extraction.md) - Metadata pipeline
- [F-100: GLiNER NER](../features/planned/F-100-gliner-ner.md) - Zero-shot extraction
- [ADR-0031: Knowledge Graph Storage](../decisions/adrs/0031-knowledge-graph-storage.md) - SQLite decision

---

## Related Documentation

- [State-of-the-Art NER](./state-of-the-art-ner.md) - Extraction techniques
- [NLP Library Integration](./nlp-library-integration.md) - spaCy/KeyBERT patterns
- [State-of-the-Art Knowledge Graphs](./state-of-the-art-knowledge-graphs.md) - Entity graphs

---

**Status**: Research complete
